import json
import logging
from datetime import datetime
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import re

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, namespace="helm-aware"):
        self.namespace = namespace
        self.configmap_name = "helm-chart-versions-cache"
        
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config")
        except config.ConfigException:
            try:
                config.load_kube_config()
                logger.info("Loaded local Kubernetes config")
            except config.ConfigException:
                logger.warning("Could not load Kubernetes config, cache will be disabled")
                self.v1_api = None
                return
        
        self.v1_api = client.CoreV1Api()
        logger.info("CacheService initialized successfully")
    
    def _sanitize_key(self, key):
        safe_key = re.sub(r'[^a-zA-Z0-9._-]', '_', key)
        logger.debug(f"Sanitized ConfigMap key: {key} -> {safe_key}")
        return safe_key

    def get_cached_versions(self, chart_key):
        """Get cached versions for a specific chart"""
        if not self.v1_api:
            logger.warning("Kubernetes API not available, returning None")
            return None
        
        try:
            configmap = self.v1_api.read_namespaced_config_map(
                name=self.configmap_name,
                namespace=self.namespace
            )
            
            safe_key = self._sanitize_key(chart_key)
            if hasattr(configmap, 'data') and configmap.data:  # type: ignore
                data = configmap.data.get(safe_key)  # type: ignore
                if data:
                    cached_data = json.loads(data)
                    logger.debug(f"Retrieved cached data for {safe_key}: {cached_data}")
                    return cached_data
                else:
                    logger.debug(f"No cached data found for {safe_key}")
                    return None
            else:
                logger.debug(f"No data in ConfigMap for {safe_key}")
                return None
                
        except ApiException as e:
            if e.status == 404:
                logger.debug(f"ConfigMap {self.configmap_name} not found")
                return None
            else:
                logger.error(f"Error reading ConfigMap: {e}")
                return None
        except Exception as e:
            logger.error(f"Error getting cached versions: {e}")
            return None
    
    def set_cached_versions(self, chart_key, versions, last_update=None, max_retries=3):
        """Cache versions for a specific chart"""
        if not self.v1_api:
            logger.warning("Kubernetes API not available, skipping cache update")
            return False
        
        if last_update is None:
            last_update = datetime.utcnow().isoformat()
        
        cached_data = {
            'versions': versions,
            'last_update': last_update
        }
        
        safe_key = self._sanitize_key(chart_key)
        for attempt in range(max_retries):
            try:
                try:
                    configmap = self.v1_api.read_namespaced_config_map(
                        name=self.configmap_name,
                        namespace=self.namespace
                    )
                    data = configmap.data or {}  # type: ignore
                except ApiException as e:
                    if e.status == 404:
                        logger.info(f"Creating new ConfigMap {self.configmap_name}")
                        configmap = client.V1ConfigMap(
                            metadata=client.V1ObjectMeta(
                                name=self.configmap_name,
                                namespace=self.namespace
                            ),
                            data={}
                        )
                        data = {}
                    else:
                        raise
                data[safe_key] = json.dumps(cached_data)
                configmap.data = data  # type: ignore
                try:
                    if hasattr(configmap.metadata, 'resource_version') and configmap.metadata.resource_version:  # type: ignore
                        self.v1_api.replace_namespaced_config_map(
                            name=self.configmap_name,
                            namespace=self.namespace,
                            body=configmap
                        )
                        logger.debug(f"Updated ConfigMap with data for {safe_key}")
                    else:
                        self.v1_api.create_namespaced_config_map(
                            namespace=self.namespace,
                            body=configmap
                        )
                        logger.debug(f"Created ConfigMap with data for {safe_key}")
                    return True
                except ApiException as e:
                    if e.status == 409 and attempt < max_retries - 1:
                        logger.warning(f"ConfigMap update conflict, retrying ({attempt+1}/{max_retries})")
                        continue  # retry
                    else:
                        raise
            except Exception as e:
                logger.error(f"Error setting cached versions: {e}")
                return False
        logger.error("Failed to update ConfigMap after retries")
        return False
    
    def get_cache_metadata(self):
        """Get metadata about the cache (last update time, etc.)"""
        if not self.v1_api:
            return None
        
        try:
            configmap = self.v1_api.read_namespaced_config_map(
                name=self.configmap_name,
                namespace=self.namespace
            )
            
            metadata = {
                'last_update': configmap.metadata.creation_timestamp.isoformat() if configmap.metadata.creation_timestamp else None,  # type: ignore
                'chart_count': len(configmap.data) if configmap.data else 0  # type: ignore
            }
            
            return metadata
            
        except ApiException as e:
            if e.status == 404:
                return None
            else:
                logger.error(f"Error reading cache metadata: {e}")
                return None
        except Exception as e:
            logger.error(f"Error getting cache metadata: {e}")
            return None
    
    def clear_cache(self):
        """Clear all cached data"""
        if not self.v1_api:
            logger.warning("Kubernetes API not available, cannot clear cache")
            return False
        
        try:
            self.v1_api.delete_namespaced_config_map(
                name=self.configmap_name,
                namespace=self.namespace
            )
            logger.info("Cache cleared successfully")
            return True
        except ApiException as e:
            if e.status == 404:
                logger.info("Cache was already empty")
                return True
            else:
                logger.error(f"Error clearing cache: {e}")
                return False
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False 
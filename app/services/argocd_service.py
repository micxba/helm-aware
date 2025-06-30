import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging
import time

logger = logging.getLogger(__name__)

class ArgoCDService:
    def __init__(self):
        logger.info("=== ArgoCDService: Initializing ===")
        start_time = time.time()
        
        try:
            # Try to load in-cluster config first
            logger.info("Step 1: Attempting to load in-cluster config...")
            config.load_incluster_config()
            logger.info("✅ Successfully loaded in-cluster config")
        except config.ConfigException as e:
            logger.warning(f"In-cluster config failed: {e}")
            try:
                # Fall back to kubeconfig file
                logger.info("Step 2: Trying kubeconfig file...")
                config.load_kube_config()
                logger.info("✅ Successfully loaded kubeconfig")
            except config.ConfigException as e:
                logger.error(f"❌ Kubeconfig failed: {e}")
                logger.error("❌ No valid Kubernetes configuration found")
                logger.error("❌ Please ensure you have:")
                logger.error("   - A valid kubeconfig file, or")
                logger.error("   - Are running inside a Kubernetes cluster")
                raise Exception("No valid Kubernetes configuration found")
        
        logger.info("Step 3: Initializing Kubernetes API clients...")
        try:
            self.v1 = client.CoreV1Api()
            logger.info("✅ CoreV1Api initialized")
            
            self.custom_objects_api = client.CustomObjectsApi()
            logger.info("✅ CustomObjectsApi initialized")
            
            init_time = time.time() - start_time
            logger.info(f"✅ ArgoCDService initialized successfully in {init_time:.2f}s")
        except Exception as e:
            logger.error(f"❌ Failed to initialize API clients: {e}")
            raise
    
    def get_all_applications(self):
        """Get all ArgoCD Applications from the cluster"""
        logger.info("=== ArgoCDService: Fetching Applications ===")
        start_time = time.time()
        
        try:
            logger.info("Step 1: Calling Kubernetes API for applications...")
            logger.info("  - Group: argoproj.io")
            logger.info("  - Version: v1alpha1")
            logger.info("  - Plural: applications")
            
            api_start = time.time()
            applications = self.custom_objects_api.list_cluster_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                plural="applications"
            )
            api_time = time.time() - api_start
            
            app_count = len(applications.get('items', []))
            total_time = time.time() - start_time
            
            logger.info(f"✅ API call completed in {api_time:.2f}s")
            logger.info(f"✅ Successfully fetched {app_count} ArgoCD Applications")
            logger.info(f"✅ Total time: {total_time:.2f}s")
            
            # Log details about each application
            for i, app in enumerate(applications.get('items', [])):
                app_name = app.get('metadata', {}).get('name', 'unknown')
                app_namespace = app.get('metadata', {}).get('namespace', 'unknown')
                logger.debug(f"  Application {i+1}: {app_name} (namespace: {app_namespace})")
            
            return applications.get('items', [])
            
        except ApiException as e:
            logger.error(f"❌ API Exception fetching ArgoCD Applications:")
            logger.error(f"  - Status: {e.status}")
            logger.error(f"  - Reason: {e.reason}")
            logger.error(f"  - Body: {e.body}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching applications: {e}", exc_info=True)
            return []
    
    def get_all_application_sets(self):
        """Get all ArgoCD ApplicationSets from the cluster"""
        logger.info("=== ArgoCDService: Fetching ApplicationSets ===")
        start_time = time.time()
        
        try:
            logger.info("Step 1: Calling Kubernetes API for application sets...")
            logger.info("  - Group: argoproj.io")
            logger.info("  - Version: v1alpha1")
            logger.info("  - Plural: applicationsets")
            
            api_start = time.time()
            application_sets = self.custom_objects_api.list_cluster_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                plural="applicationsets"
            )
            api_time = time.time() - api_start
            
            app_set_count = len(application_sets.get('items', []))
            total_time = time.time() - start_time
            
            logger.info(f"✅ API call completed in {api_time:.2f}s")
            logger.info(f"✅ Successfully fetched {app_set_count} ArgoCD ApplicationSets")
            logger.info(f"✅ Total time: {total_time:.2f}s")
            
            # Log details about each application set
            for i, app_set in enumerate(application_sets.get('items', [])):
                app_set_name = app_set.get('metadata', {}).get('name', 'unknown')
                app_set_namespace = app_set.get('metadata', {}).get('namespace', 'unknown')
                logger.debug(f"  ApplicationSet {i+1}: {app_set_name} (namespace: {app_set_namespace})")
            
            return application_sets.get('items', [])
            
        except ApiException as e:
            logger.error(f"❌ API Exception fetching ArgoCD ApplicationSets:")
            logger.error(f"  - Status: {e.status}")
            logger.error(f"  - Reason: {e.reason}")
            logger.error(f"  - Body: {e.body}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching application sets: {e}", exc_info=True)
            return []
    
    def get_application_by_name(self, name, namespace=None):
        """Get a specific ArgoCD Application by name"""
        logger.debug(f"Fetching ArgoCD Application: {name} in namespace: {namespace}")
        try:
            if namespace:
                application = self.custom_objects_api.get_namespaced_custom_object(
                    group="argoproj.io",
                    version="v1alpha1",
                    namespace=namespace,
                    plural="applications",
                    name=name
                )
            else:
                application = self.custom_objects_api.get_cluster_custom_object(
                    group="argoproj.io",
                    version="v1alpha1",
                    plural="applications",
                    name=name
                )
            logger.debug(f"✅ Successfully fetched application: {name}")
            return application
        except ApiException as e:
            logger.error(f"❌ Error fetching ArgoCD Application {name}: {e}")
            return None
    
    def get_application_set_by_name(self, name, namespace):
        """Get a specific ArgoCD ApplicationSet by name"""
        logger.debug(f"Fetching ArgoCD ApplicationSet: {name} in namespace: {namespace}")
        try:
            application_set = self.custom_objects_api.get_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=namespace,
                plural="applicationsets",
                name=name
            )
            logger.debug(f"✅ Successfully fetched application set: {name}")
            return application_set
        except ApiException as e:
            logger.error(f"❌ Error fetching ArgoCD ApplicationSet {name}: {e}")
            return None 
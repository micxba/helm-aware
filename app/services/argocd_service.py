import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging

logger = logging.getLogger(__name__)

class ArgoCDService:
    def __init__(self):
        logger.info("Initializing ArgoCDService...")
        try:
            # Try to load in-cluster config first
            logger.debug("Attempting to load in-cluster config...")
            config.load_incluster_config()
            logger.info("Successfully loaded in-cluster config")
        except config.ConfigException:
            try:
                # Fall back to kubeconfig file
                logger.debug("In-cluster config failed, trying kubeconfig...")
                config.load_kube_config()
                logger.info("Successfully loaded kubeconfig")
            except config.ConfigException:
                # Use default config
                logger.debug("Kubeconfig failed, using default config...")
                config.load_default_config()
                logger.info("Successfully loaded default config")
        
        logger.debug("Initializing Kubernetes API clients...")
        self.v1 = client.CoreV1Api()
        self.custom_objects_api = client.CustomObjectsApi()
        logger.info("ArgoCDService initialized successfully")
    
    def get_all_applications(self):
        """Get all ArgoCD Applications from the cluster"""
        logger.info("Fetching all ArgoCD Applications...")
        try:
            logger.debug("Calling Kubernetes API for applications...")
            applications = self.custom_objects_api.list_cluster_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                plural="applications"
            )
            app_count = len(applications.get('items', []))
            logger.info(f"Successfully fetched {app_count} ArgoCD Applications")
            return applications.get('items', [])
        except ApiException as e:
            logger.error(f"Error fetching ArgoCD Applications: {e}")
            logger.error(f"Status code: {e.status}")
            logger.error(f"Reason: {e.reason}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching applications: {e}")
            return []
    
    def get_all_application_sets(self):
        """Get all ArgoCD ApplicationSets from the cluster"""
        logger.info("Fetching all ArgoCD ApplicationSets...")
        try:
            logger.debug("Calling Kubernetes API for application sets...")
            application_sets = self.custom_objects_api.list_cluster_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                plural="applicationsets"
            )
            app_set_count = len(application_sets.get('items', []))
            logger.info(f"Successfully fetched {app_set_count} ArgoCD ApplicationSets")
            return application_sets.get('items', [])
        except ApiException as e:
            logger.error(f"Error fetching ArgoCD ApplicationSets: {e}")
            logger.error(f"Status code: {e.status}")
            logger.error(f"Reason: {e.reason}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching application sets: {e}")
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
            logger.debug(f"Successfully fetched application: {name}")
            return application
        except ApiException as e:
            logger.error(f"Error fetching ArgoCD Application {name}: {e}")
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
            logger.debug(f"Successfully fetched application set: {name}")
            return application_set
        except ApiException as e:
            logger.error(f"Error fetching ArgoCD ApplicationSet {name}: {e}")
            return None 
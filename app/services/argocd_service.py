import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging

logger = logging.getLogger(__name__)

class ArgoCDService:
    def __init__(self):
        try:
            # Try to load in-cluster config first
            config.load_incluster_config()
        except config.ConfigException:
            try:
                # Fall back to kubeconfig file
                config.load_kube_config()
            except config.ConfigException:
                # Use default config
                config.load_default_config()
        
        self.v1 = client.CoreV1Api()
        self.custom_objects_api = client.CustomObjectsApi()
    
    def get_all_applications(self):
        """Get all ArgoCD Applications from the cluster"""
        try:
            applications = self.custom_objects_api.list_cluster_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                plural="applications"
            )
            return applications.get('items', [])
        except ApiException as e:
            logger.error(f"Error fetching ArgoCD Applications: {e}")
            return []
    
    def get_all_application_sets(self):
        """Get all ArgoCD ApplicationSets from the cluster"""
        try:
            application_sets = self.custom_objects_api.list_cluster_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                plural="applicationsets"
            )
            return application_sets.get('items', [])
        except ApiException as e:
            logger.error(f"Error fetching ArgoCD ApplicationSets: {e}")
            return []
    
    def get_application_by_name(self, name, namespace=None):
        """Get a specific ArgoCD Application by name"""
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
            return application
        except ApiException as e:
            logger.error(f"Error fetching ArgoCD Application {name}: {e}")
            return None
    
    def get_application_set_by_name(self, name, namespace):
        """Get a specific ArgoCD ApplicationSet by name"""
        try:
            application_set = self.custom_objects_api.get_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=namespace,
                plural="applicationsets",
                name=name
            )
            return application_set
        except ApiException as e:
            logger.error(f"Error fetching ArgoCD ApplicationSet {name}: {e}")
            return None 
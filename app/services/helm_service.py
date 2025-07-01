import re
import requests
import yaml
import json
import logging
from urllib.parse import urlparse
import subprocess
import tempfile
import os
from .cache_service import CacheService

logger = logging.getLogger(__name__)

class HelmService:
    def __init__(self):
        logger.info("Initializing HelmService...")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Helm-Aware/1.0'
        })
        self.cache_service = CacheService()
        logger.info("HelmService initialized successfully")
    
    def analyze_helm_charts(self, resource):
        """Analyze a resource (Application or ApplicationSet) for Helm charts"""
        logger.debug(f"Analyzing Helm charts for resource: {resource.get('metadata', {}).get('name', 'unknown')}")
        helm_charts = []
        
        # Check if it's an Application
        if resource.get('kind') == 'Application':
            logger.debug("Resource is an Application, analyzing sources...")
            helm_charts.extend(self._analyze_application_sources(resource))
        # Check if it's an ApplicationSet
        elif resource.get('kind') == 'ApplicationSet':
            logger.debug("Resource is an ApplicationSet, analyzing sources...")
            helm_charts.extend(self._analyze_application_set_sources(resource))
        else:
            logger.debug(f"Unknown resource kind: {resource.get('kind')}")
        
        logger.info(f"Found {len(helm_charts)} Helm charts in resource")
        return helm_charts
    
    def _analyze_application_sources(self, application):
        """Analyze sources in an ArgoCD Application"""
        logger.debug("Analyzing application sources...")
        helm_charts = []
        spec = application.get('spec', {})
        
        # Check if the application itself has Helm configuration
        has_helm_config = self._has_helm_config_in_application(application)
        
        # Check single source
        if 'source' in spec:
            logger.debug("Found single source, analyzing...")
            chart_info = self._extract_helm_info(spec['source'], has_helm_config)
            if chart_info:
                helm_charts.append(chart_info)
                logger.debug(f"Added Helm chart: {chart_info['chart_name']}")
        
        # Check multiple sources
        if 'sources' in spec:
            logger.debug(f"Found {len(spec['sources'])} sources, analyzing each...")
            for i, source in enumerate(spec['sources']):
                logger.debug(f"Analyzing source {i+1}/{len(spec['sources'])}...")
                chart_info = self._extract_helm_info(source, has_helm_config)
                if chart_info:
                    helm_charts.append(chart_info)
                    logger.debug(f"Added Helm chart: {chart_info['chart_name']}")
        
        return helm_charts
    
    def _analyze_application_set_sources(self, application_set):
        """Analyze sources in an ArgoCD ApplicationSet"""
        logger.debug("Analyzing application set sources...")
        helm_charts = []
        spec = application_set.get('spec', {})
        
        # Check template sources
        template = spec.get('template', {})
        template_spec = template.get('spec', {})
        
        # Check if the application set template has Helm configuration
        has_helm_config = self._has_helm_config_in_application_set(application_set)
        
        # Check single source in template
        if 'source' in template_spec:
            logger.debug("Found single source in template, analyzing...")
            chart_info = self._extract_helm_info(template_spec['source'], has_helm_config)
            if chart_info:
                helm_charts.append(chart_info)
                logger.debug(f"Added Helm chart: {chart_info['chart_name']}")
        
        # Check multiple sources in template
        if 'sources' in template_spec:
            logger.debug(f"Found {len(template_spec['sources'])} sources in template, analyzing each...")
            for i, source in enumerate(template_spec['sources']):
                logger.debug(f"Analyzing template source {i+1}/{len(template_spec['sources'])}...")
                chart_info = self._extract_helm_info(source, has_helm_config)
                if chart_info:
                    helm_charts.append(chart_info)
                    logger.debug(f"Added Helm chart: {chart_info['chart_name']}")
        
        return helm_charts
    
    def _extract_helm_info(self, source, has_helm_config=False):
        """Extract Helm chart information from a source"""
        logger.debug(f"Extracting Helm info from source: {source}")
        repo_url = source.get('repoURL', '')
        target_revision = source.get('targetRevision', '')
        chart = source.get('chart', '')
        
        logger.debug(f"Source details - repoURL: {repo_url}, chart: {chart}, targetRevision: {target_revision}")
        
        # Check if this is a Helm chart
        if not self._is_helm_chart(source, has_helm_config):
            logger.debug("Source is not a Helm chart, skipping")
            return None
        
        # Extract chart name and version
        chart_name = chart
        chart_version = target_revision
        
        # If no protocol specified, assume OCI
        if not repo_url.startswith(('http://', 'https://', 'oci://')):
            repo_url = f"oci://{repo_url}"
            logger.debug(f"Added OCI protocol to repo URL: {repo_url}")
        
        chart_info = {
            'repo_url': repo_url,
            'chart_name': chart_name,
            'chart_version': chart_version,
            'source_type': 'helm'
        }
        
        logger.debug(f"Extracted chart info: {chart_info}")
        return chart_info
    
    def _is_helm_chart(self, source, has_helm_config=False):
        # Only allow if 'chart' or 'helm' is present in the source
        if 'chart' in source or 'helm' in source:
            return True
        return False
    
    def _has_helm_fields_in_source(self, source):
        """Check if the source has Helm-specific fields"""
        # Check for Helm-specific fields in the source
        helm_fields = [
            'helm',  # Helm configuration block
        ]
        
        for field in helm_fields:
            if field in source:
                logger.debug(f"Found Helm field '{field}' in source")
                return True
        
        return False
    
    def _has_valid_helm_fields_in_source(self, source):
        """Check if the source has VALID Helm-specific fields (restrictive)"""
        if 'helm' not in source:
            return False
        
        helm_config = source['helm']
        logger.debug(f"Checking Helm config in source: {helm_config}")
        
        # Pattern 1: valueFiles
        if 'valueFiles' in helm_config:
            logger.debug("Found valueFiles in Helm config - valid Helm chart")
            return True
        
        # Pattern 2: valueObject
        if 'valueObject' in helm_config:
            logger.debug("Found valueObject in Helm config - valid Helm chart")
            return True
        
        # Pattern 3: parameters
        if 'parameters' in helm_config:
            logger.debug("Found parameters in Helm config - valid Helm chart")
            return True
        
        logger.debug("Helm config does not contain valid fields")
        return False
    
    def _has_helm_config_in_application(self, application):
        """Check if the Application has VALID Helm configuration (restrictive)"""
        spec = application.get('spec', {})
        
        # Check for Helm configuration in the spec
        if 'helm' in spec:
            helm_config = spec['helm']
            logger.debug(f"Checking Helm config in application spec: {helm_config}")
            
            # Pattern 1: releaseName
            if 'releaseName' in helm_config:
                logger.debug("Found releaseName in application Helm config - valid Helm chart")
                return True
            
            # Pattern 2: values
            if 'values' in helm_config:
                logger.debug("Found values in application Helm config - valid Helm chart")
                return True
        
        # Check for Helm configuration in sources
        if 'source' in spec and 'helm' in spec['source']:
            helm_config = spec['source']['helm']
            logger.debug(f"Checking Helm config in application source: {helm_config}")
            
            # Pattern 1: valueFiles
            if 'valueFiles' in helm_config:
                logger.debug("Found valueFiles in application source Helm config - valid Helm chart")
                return True
            
            # Pattern 2: valueObject
            if 'valueObject' in helm_config:
                logger.debug("Found valueObject in application source Helm config - valid Helm chart")
                return True
            
            # Pattern 3: parameters
            if 'parameters' in helm_config:
                logger.debug("Found parameters in application source Helm config - valid Helm chart")
                return True
        
        if 'sources' in spec:
            for source in spec['sources']:
                if 'helm' in source:
                    helm_config = source['helm']
                    logger.debug(f"Checking Helm config in application sources: {helm_config}")
                    
                    # Pattern 1: valueFiles
                    if 'valueFiles' in helm_config:
                        logger.debug("Found valueFiles in application sources Helm config - valid Helm chart")
                        return True
                    
                    # Pattern 2: valueObject
                    if 'valueObject' in helm_config:
                        logger.debug("Found valueObject in application sources Helm config - valid Helm chart")
                        return True
                    
                    # Pattern 3: parameters
                    if 'parameters' in helm_config:
                        logger.debug("Found parameters in application sources Helm config - valid Helm chart")
                        return True
        
        return False
    
    def _has_helm_config_in_application_set(self, application_set):
        """Check if the ApplicationSet has VALID Helm configuration (restrictive)"""
        spec = application_set.get('spec', {})
        template = spec.get('template', {})
        template_spec = template.get('spec', {})
        
        # Check for Helm configuration in the template spec
        if 'helm' in template_spec:
            helm_config = template_spec['helm']
            logger.debug(f"Checking Helm config in application set template spec: {helm_config}")
            
            # Pattern 1: releaseName
            if 'releaseName' in helm_config:
                logger.debug("Found releaseName in application set template Helm config - valid Helm chart")
                return True
            
            # Pattern 2: values
            if 'values' in helm_config:
                logger.debug("Found values in application set template Helm config - valid Helm chart")
                return True
        
        # Check for Helm configuration in template sources
        if 'source' in template_spec and 'helm' in template_spec['source']:
            helm_config = template_spec['source']['helm']
            logger.debug(f"Checking Helm config in application set template source: {helm_config}")
            
            # Pattern 1: valueFiles
            if 'valueFiles' in helm_config:
                logger.debug("Found valueFiles in application set template source Helm config - valid Helm chart")
                return True
            
            # Pattern 2: valueObject
            if 'valueObject' in helm_config:
                logger.debug("Found valueObject in application set template source Helm config - valid Helm chart")
                return True
            
            # Pattern 3: parameters
            if 'parameters' in helm_config:
                logger.debug("Found parameters in application set template source Helm config - valid Helm chart")
                return True
        
        if 'sources' in template_spec:
            for source in template_spec['sources']:
                if 'helm' in source:
                    helm_config = source['helm']
                    logger.debug(f"Checking Helm config in application set template sources: {helm_config}")
                    
                    # Pattern 1: valueFiles
                    if 'valueFiles' in helm_config:
                        logger.debug("Found valueFiles in application set template sources Helm config - valid Helm chart")
                        return True
                    
                    # Pattern 2: valueObject
                    if 'valueObject' in helm_config:
                        logger.debug("Found valueObject in application set template sources Helm config - valid Helm chart")
                        return True
                    
                    # Pattern 3: parameters
                    if 'parameters' in helm_config:
                        logger.debug("Found parameters in application set template sources Helm config - valid Helm chart")
                        return True
        
        return False
    
    def _looks_like_helm_repo(self, repo_url):
        """Check if an HTTP/HTTPS URL looks like a Helm repository"""
        if not repo_url:
            return False
        
        # Common Helm repository patterns
        helm_patterns = [
            r'charts\.',  # charts.domain.com
            r'helm\.',    # helm.domain.com
            r'bitnami\.com',  # Bitnami charts
            r'stable\.',  # Stable charts
            r'incubator\.',  # Incubator charts
            r'chartmuseum\.',  # ChartMuseum
            r'charts\.bitnami\.com',  # Bitnami charts
            r'charts\.helm\.sh',  # Helm charts
        ]
        
        for pattern in helm_patterns:
            if re.search(pattern, repo_url, re.IGNORECASE):
                return True
        
        return False
    
    def _is_git_repository(self, repo_url):
        if not repo_url:
            logger.debug("GIT DETECTION: repo_url is empty")
            return False
        repo_url = repo_url.lower()
        is_git = (
            repo_url.startswith('git@') or
            repo_url.startswith('git://') or
            repo_url.endswith('.git') or
            ((repo_url.startswith('http://') or repo_url.startswith('https://')) and repo_url.endswith('.git'))
        )
        logger.debug(f"GIT DETECTION: repo_url={repo_url}, is_git={is_git}")
        return is_git
    
    def get_available_versions(self, chart_info):
        """Get available versions for a Helm chart (with caching)"""
        logger.info(f"Getting available versions for chart: {chart_info['chart_name']} from {chart_info['repo_url']}")
        
        # Create a unique key for caching
        chart_key = f"{chart_info['repo_url']}:{chart_info['chart_name']}"
        
        # Try to get cached versions first
        cached_data = self.cache_service.get_cached_versions(chart_key)
        if cached_data:
            logger.info(f"Using cached versions for {chart_info['chart_name']}")
            return cached_data.get('versions', [])
        
        # If not cached, fetch from remote
        try:
            repo_url = chart_info['repo_url']
            chart_name = chart_info['chart_name']
            
            if repo_url.startswith('oci://'):
                logger.debug("Using OCI version fetching method")
                versions = self._get_oci_versions(repo_url, chart_name)
            else:
                logger.debug("Using HTTP version fetching method")
                versions = self._get_http_versions(repo_url, chart_name)
            
            # Cache the results
            if versions:
                self.cache_service.set_cached_versions(chart_key, versions)
                logger.info(f"Cached {len(versions)} versions for {chart_info['chart_name']}")
            
            return versions
        except Exception as e:
            logger.error(f"Error getting versions for {chart_info}: {e}")
            return []
    
    def refresh_versions(self, chart_info):
        """Force refresh versions for a specific chart"""
        logger.info(f"Refreshing versions for chart: {chart_info['chart_name']} from {chart_info['repo_url']}")
        
        # Create a unique key for caching
        chart_key = f"{chart_info['repo_url']}:{chart_info['chart_name']}"
        
        try:
            repo_url = chart_info['repo_url']
            chart_name = chart_info['chart_name']
            
            if repo_url.startswith('oci://'):
                logger.debug("Using OCI version fetching method")
                versions = self._get_oci_versions(repo_url, chart_name)
            else:
                logger.debug("Using HTTP version fetching method")
                versions = self._get_http_versions(repo_url, chart_name)
            
            # Update cache with new results
            if versions:
                self.cache_service.set_cached_versions(chart_key, versions)
                logger.info(f"Updated cache with {len(versions)} versions for {chart_info['chart_name']}")
            
            return versions
        except Exception as e:
            logger.error(f"Error refreshing versions for {chart_info}: {e}")
            return []
    
    def get_cache_metadata(self):
        """Get cache metadata"""
        return self.cache_service.get_cache_metadata()
    
    def clear_cache(self):
        """Clear all cached data"""
        return self.cache_service.clear_cache()
    
    def _get_oci_versions(self, repo_url, chart_name):
        """Get versions from OCI registry"""
        logger.debug(f"Fetching OCI versions for {chart_name} from {repo_url}")
        try:
            # Remove oci:// prefix
            registry_url = repo_url.replace('oci://', '')
            
            # Use helm command to get versions
            cmd = [
                'helm', 'search', 'repo', 
                f'{registry_url}/{chart_name}', 
                '--versions', '--output', 'json'
            ]
            
            logger.debug(f"Executing Helm command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.debug("Helm command executed successfully")
                data = json.loads(result.stdout)
                versions = []
                for item in data:
                    if 'version' in item:
                        versions.append(item['version'])
                logger.info(f"Found {len(versions)} versions for {chart_name}")
                return sorted(versions, reverse=True)
            else:
                logger.warning(f"Helm command failed: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            logger.error(f"Helm command timed out for {chart_name}")
            return []
        except Exception as e:
            logger.error(f"Error getting OCI versions: {e}")
            return []
    
    def _get_http_versions(self, repo_url, chart_name):
        """Get versions from HTTP repository"""
        logger.debug(f"Fetching HTTP versions for {chart_name} from {repo_url}")
        try:
            # Try to fetch index.yaml
            index_url = f"{repo_url}/index.yaml"
            logger.debug(f"Fetching index from: {index_url}")
            
            response = self.session.get(index_url, timeout=10)
            response.raise_for_status()
            
            logger.debug("Successfully fetched index.yaml")
            index_data = yaml.safe_load(response.text)
            entries = index_data.get('entries', {})
            
            if chart_name in entries:
                versions = []
                for entry in entries[chart_name]:
                    if 'version' in entry:
                        versions.append(entry['version'])
                logger.info(f"Found {len(versions)} versions for {chart_name}")
                return sorted(versions, reverse=True)
            else:
                logger.warning(f"Chart {chart_name} not found in repository")
                return []
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching versions for {chart_name}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting HTTP versions: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting HTTP versions: {e}")
            return []
    
    def get_latest_version(self, versions):
        """Get the latest version from a list of versions"""
        if not versions:
            return None
        
        # Sort versions and return the first (latest)
        sorted_versions = sorted(versions, reverse=True)
        return sorted_versions[0] 
import re
import requests
import yaml
import json
import logging
from urllib.parse import urlparse
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)

class HelmService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Helm-Aware/1.0'
        })
    
    def analyze_helm_charts(self, resource):
        """Analyze a resource (Application or ApplicationSet) for Helm charts"""
        helm_charts = []
        
        # Check if it's an Application
        if resource.get('kind') == 'Application':
            helm_charts.extend(self._analyze_application_sources(resource))
        # Check if it's an ApplicationSet
        elif resource.get('kind') == 'ApplicationSet':
            helm_charts.extend(self._analyze_application_set_sources(resource))
        
        return helm_charts
    
    def _analyze_application_sources(self, application):
        """Analyze sources in an ArgoCD Application"""
        helm_charts = []
        spec = application.get('spec', {})
        
        # Check single source
        if 'source' in spec:
            chart_info = self._extract_helm_info(spec['source'])
            if chart_info:
                helm_charts.append(chart_info)
        
        # Check multiple sources
        if 'sources' in spec:
            for source in spec['sources']:
                chart_info = self._extract_helm_info(source)
                if chart_info:
                    helm_charts.append(chart_info)
        
        return helm_charts
    
    def _analyze_application_set_sources(self, application_set):
        """Analyze sources in an ArgoCD ApplicationSet"""
        helm_charts = []
        spec = application_set.get('spec', {})
        
        # Check template sources
        template = spec.get('template', {})
        template_spec = template.get('spec', {})
        
        # Check single source in template
        if 'source' in template_spec:
            chart_info = self._extract_helm_info(template_spec['source'])
            if chart_info:
                helm_charts.append(chart_info)
        
        # Check multiple sources in template
        if 'sources' in template_spec:
            for source in template_spec['sources']:
                chart_info = self._extract_helm_info(source)
                if chart_info:
                    helm_charts.append(chart_info)
        
        return helm_charts
    
    def _extract_helm_info(self, source):
        """Extract Helm chart information from a source"""
        repo_url = source.get('repoURL', '')
        target_revision = source.get('targetRevision', '')
        chart = source.get('chart', '')
        
        # Check if this is a Helm chart
        if not self._is_helm_chart(source):
            return None
        
        # Extract chart name and version
        chart_name = chart
        chart_version = target_revision
        
        # If no protocol specified, assume OCI
        if not repo_url.startswith(('http://', 'https://', 'oci://')):
            repo_url = f"oci://{repo_url}"
        
        return {
            'repo_url': repo_url,
            'chart_name': chart_name,
            'chart_version': chart_version,
            'source_type': 'helm'
        }
    
    def _is_helm_chart(self, source):
        """Determine if a source is a Helm chart"""
        # Check if chart field is present
        if 'chart' in source:
            return True
        
        # Check if it's an OCI repository (common for Helm charts)
        repo_url = source.get('repoURL', '')
        if repo_url.startswith('oci://'):
            return True
        
        # Check if targetRevision looks like a Helm version
        target_revision = source.get('targetRevision', '')
        if target_revision and re.match(r'^\d+\.\d+\.\d+', target_revision):
            return True
        
        return False
    
    def get_available_versions(self, chart_info):
        """Get available versions for a Helm chart"""
        try:
            repo_url = chart_info['repo_url']
            chart_name = chart_info['chart_name']
            
            if repo_url.startswith('oci://'):
                return self._get_oci_versions(repo_url, chart_name)
            else:
                return self._get_http_versions(repo_url, chart_name)
        except Exception as e:
            logger.error(f"Error getting versions for {chart_info}: {e}")
            return []
    
    def _get_oci_versions(self, repo_url, chart_name):
        """Get versions from OCI registry"""
        try:
            # Remove oci:// prefix
            registry_url = repo_url.replace('oci://', '')
            
            # Use helm command to get versions
            cmd = [
                'helm', 'search', 'repo', 
                f'{registry_url}/{chart_name}', 
                '--versions', '--output', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                versions = []
                for item in data:
                    if 'version' in item:
                        versions.append(item['version'])
                return sorted(versions, reverse=True)
            else:
                logger.warning(f"Helm command failed: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting OCI versions: {e}")
            return []
    
    def _get_http_versions(self, repo_url, chart_name):
        """Get versions from HTTP repository"""
        try:
            # Try to fetch index.yaml
            index_url = f"{repo_url}/index.yaml"
            response = self.session.get(index_url, timeout=10)
            response.raise_for_status()
            
            index_data = yaml.safe_load(response.text)
            entries = index_data.get('entries', {})
            
            if chart_name in entries:
                versions = []
                for entry in entries[chart_name]:
                    if 'version' in entry:
                        versions.append(entry['version'])
                return sorted(versions, reverse=True)
            
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
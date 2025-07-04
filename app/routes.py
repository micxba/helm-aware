from flask import Blueprint, render_template, jsonify, request
from app.services.argocd_service import ArgoCDService
from app.services.helm_service import HelmService
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from datetime import datetime

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main page showing Helm chart analysis"""
    try:
        logger.info("Loading main page...")
        
        # Get cache metadata
        cache_metadata = HelmService().get_cache_metadata()
        
        return render_template('index.html', cache_metadata=cache_metadata)
    except Exception as e:
        logger.error(f"Error loading main page: {e}")
        return render_template('index.html', error=str(e))

@main_bp.route('/api/applications')
def get_applications():
    """Get all ArgoCD Applications and ApplicationSets with Helm chart analysis"""
    logger.info("=== API: Starting applications analysis request ===")
    
    try:
        # Step 1: Initialize services
        logger.info("Step 1: Initializing services...")
        argocd_service = ArgoCDService()
        helm_service = HelmService()
        logger.info("✅ Services initialized successfully")
        
        # Step 2: Fetch ArgoCD resources (local data only)
        logger.info("Step 2: Fetching ArgoCD resources from cluster...")
        start_time = time.time()
        
        applications = argocd_service.get_all_applications()
        application_sets = argocd_service.get_all_application_sets()
        
        fetch_time = time.time() - start_time
        logger.info(f"✅ Fetched {len(applications)} applications and {len(application_sets)} application sets in {fetch_time:.2f}s")
        
        # Step 3: Analyze Helm charts in local data
        logger.info("Step 3: Analyzing Helm charts in local data...")
        start_time = time.time()
        
        total_charts = 0
        filtered_applications = []
        filtered_application_sets = []
        
        # Process applications
        logger.info(f"Processing {len(applications)} applications...")
        for i, app in enumerate(applications):
            app_name = app.get('metadata', {}).get('name', f'app-{i}')
            logger.info(f"  Processing application {i+1}/{len(applications)}: {app_name}")
            
            app['helm_charts'] = helm_service.analyze_helm_charts(app)
            chart_count = len(app['helm_charts'])
            total_charts += chart_count
            logger.info(f"    Found {chart_count} Helm charts")
            
            # Initialize empty versions for now
            for chart in app['helm_charts']:
                chart['available_versions'] = []
                chart['version_fetch_status'] = 'pending'
            
            if chart_count > 0:
                filtered_applications.append(app)
        
        # Process application sets
        logger.info(f"Processing {len(application_sets)} application sets...")
        for i, app_set in enumerate(application_sets):
            app_set_name = app_set.get('metadata', {}).get('name', f'appset-{i}')
            logger.info(f"  Processing application set {i+1}/{len(application_sets)}: {app_set_name}")
            
            app_set['helm_charts'] = helm_service.analyze_helm_charts(app_set)
            chart_count = len(app_set['helm_charts'])
            total_charts += chart_count
            logger.info(f"    Found {chart_count} Helm charts")
            
            # Initialize empty versions for now
            for chart in app_set['helm_charts']:
                chart['available_versions'] = []
                chart['version_fetch_status'] = 'pending'
            
            if chart_count > 0:
                filtered_application_sets.append(app_set)
        
        analysis_time = time.time() - start_time
        logger.info(f"✅ Local analysis complete: {total_charts} total charts found in {analysis_time:.2f}s")
        
        # Step 4: Return local data immediately
        logger.info("Step 4: Returning local data to frontend...")
        response_data = {
            'applications': filtered_applications,
            'application_sets': filtered_application_sets,
            'local_analysis_complete': True,
            'total_charts_found': total_charts
        }
        
        logger.info("✅ Returning response with local data")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Critical error in get_applications: {e}", exc_info=True)
        return jsonify({
            'error': f'Failed to load applications: {str(e)}',
            'local_analysis_complete': False
        }), 500

@main_bp.route('/api/helm-charts')
def get_helm_charts():
    """API endpoint to get all Helm charts from ArgoCD Applications and ApplicationSets"""
    try:
        logger.info("Fetching Helm charts from ArgoCD...")
        
        # Get all Applications and ApplicationSets
        applications = ArgoCDService().get_all_applications()
        application_sets = ArgoCDService().get_all_application_sets()
        
        logger.info(f"Found {len(applications)} Applications and {len(application_sets)} ApplicationSets")
        
        all_helm_charts = []
        
        # Analyze Applications
        for app in applications:
            logger.debug(f"Analyzing Application: {app.get('metadata', {}).get('name', 'unknown')}")
            helm_charts = HelmService().analyze_helm_charts(app)
            for chart in helm_charts:
                chart['resource_name'] = app.get('metadata', {}).get('name', 'unknown')
                chart['resource_kind'] = 'Application'
                chart['resource_namespace'] = app.get('metadata', {}).get('namespace', 'unknown')
            all_helm_charts.extend(helm_charts)
        
        # Analyze ApplicationSets
        for app_set in application_sets:
            logger.debug(f"Analyzing ApplicationSet: {app_set.get('metadata', {}).get('name', 'unknown')}")
            helm_charts = HelmService().analyze_helm_charts(app_set)
            for chart in helm_charts:
                chart['resource_name'] = app_set.get('metadata', {}).get('name', 'unknown')
                chart['resource_kind'] = 'ApplicationSet'
                chart['resource_namespace'] = app_set.get('metadata', {}).get('namespace', 'unknown')
            all_helm_charts.extend(helm_charts)
        
        logger.info(f"Total Helm charts found: {len(all_helm_charts)}")
        
        return jsonify({
            'success': True,
            'helm_charts': all_helm_charts,
            'total_count': len(all_helm_charts)
        })
        
    except Exception as e:
        logger.error(f"Error fetching Helm charts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/versions/<path:chart_key>')
def get_chart_versions(chart_key):
    """API endpoint to get available versions for a specific chart"""
    try:
        logger.info(f"Fetching versions for chart: {chart_key}")
        
        # Parse chart key (repo_url:chart_name)
        if ':' not in chart_key:
            return jsonify({'success': False, 'error': 'Invalid chart key format'}), 400
        
        repo_url, chart_name = chart_key.split(':', 1)
        chart_info = {
            'repo_url': repo_url,
            'chart_name': chart_name
        }
        
        versions = HelmService().get_available_versions(chart_info)
        
        return jsonify({
            'success': True,
            'versions': versions,
            'latest_version': HelmService().get_latest_version(versions)
        })
        
    except Exception as e:
        logger.error(f"Error fetching versions for {chart_key}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/refresh-versions/<path:chart_key>', methods=['POST'])
def refresh_chart_versions(chart_key):
    """API endpoint to refresh versions for a specific chart"""
    try:
        logger.info(f"Refreshing versions for chart: {chart_key}")
        
        # Parse chart key (repo_url:chart_name)
        if ':' not in chart_key:
            return jsonify({'success': False, 'error': 'Invalid chart key format'}), 400
        
        repo_url, chart_name = chart_key.split(':', 1)
        chart_info = {
            'repo_url': repo_url,
            'chart_name': chart_name
        }
        
        versions = HelmService().refresh_versions(chart_info)
        
        return jsonify({
            'success': True,
            'versions': versions,
            'latest_version': HelmService().get_latest_version(versions),
            'refreshed_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error refreshing versions for {chart_key}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/cache/metadata')
def get_cache_metadata():
    """API endpoint to get cache metadata"""
    try:
        metadata = HelmService().get_cache_metadata()
        return jsonify({
            'success': True,
            'metadata': metadata
        })
    except Exception as e:
        logger.error(f"Error getting cache metadata: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """API endpoint to clear all cached data"""
    try:
        success = HelmService().clear_cache()
        return jsonify({
            'success': success,
            'message': 'Cache cleared successfully' if success else 'Failed to clear cache'
        })
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/fetch-all-versions', methods=['POST'])
def fetch_all_versions():
    """Fetch versions for all charts asynchronously"""
    logger.info("=== API: Starting async version fetch for all charts ===")
    
    try:
        data = request.get_json()
        charts = data.get('charts', [])
        
        logger.info(f"Received {len(charts)} charts to fetch versions for")
        
        results = []
        helm_service = HelmService()
        
        # Process charts with timeout
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_chart = {}
            
            for chart in charts:
                future = executor.submit(helm_service.get_available_versions, chart)
                future_to_chart[future] = chart
            
            # Wait for completion with timeout
            for future in as_completed(future_to_chart, timeout=60):
                chart = future_to_chart[future]
                try:
                    versions = future.result(timeout=10)
                    results.append({
                        'chart_id': chart.get('chart_id'),
                        'versions': versions,
                        'status': 'success'
                    })
                    logger.info(f"✅ Fetched {len(versions)} versions for {chart['chart_name']}")
                except TimeoutError:
                    logger.warning(f"⏰ Timeout fetching versions for {chart['chart_name']}")
                    results.append({
                        'chart_id': chart.get('chart_id'),
                        'versions': [],
                        'status': 'timeout'
                    })
                except Exception as e:
                    logger.error(f"❌ Error fetching versions for {chart['chart_name']}: {e}")
                    results.append({
                        'chart_id': chart.get('chart_id'),
                        'versions': [],
                        'status': 'error',
                        'error': str(e)
                    })
        
        logger.info(f"✅ Async version fetch complete: {len(results)} results")
        return jsonify({'results': results})
        
    except Exception as e:
        logger.error(f"❌ Error in fetch_all_versions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/health')
def health_check():
    """Health check endpoint"""
    logger.debug("Health check request")
    return jsonify({'status': 'healthy', 'timestamp': time.time()}) 
from flask import Blueprint, render_template, jsonify, request
from app.services.argocd_service import ArgoCDService
from app.services.helm_service import HelmService
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    logger.info("Serving main page")
    return render_template('index.html')

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
        
        analysis_time = time.time() - start_time
        logger.info(f"✅ Local analysis complete: {total_charts} total charts found in {analysis_time:.2f}s")
        
        # Step 4: Return local data immediately
        logger.info("Step 4: Returning local data to frontend...")
        response_data = {
            'applications': applications,
            'application_sets': application_sets,
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

@main_bp.route('/api/chart-versions', methods=['POST'])
def get_chart_versions():
    """Get available versions for a specific chart"""
    logger.info("=== API: Chart versions request received ===")
    try:
        data = request.get_json()
        repo_url = data.get('repo_url')
        chart_name = data.get('chart_name')
        
        logger.info(f"Fetching versions for chart: {chart_name} from {repo_url}")
        
        helm_service = HelmService()
        versions = helm_service.get_available_versions({
            'repo_url': repo_url,
            'chart_name': chart_name
        })
        
        logger.info(f"✅ Found {len(versions)} versions for {chart_name}")
        return jsonify({'versions': versions})
    except Exception as e:
        logger.error(f"❌ Error in get_chart_versions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

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
from flask import Blueprint, render_template, jsonify, request
from app.services.argocd_service import ArgoCDService
from app.services.helm_service import HelmService
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    logger.info("Serving main page")
    return render_template('index.html')

@main_bp.route('/api/applications')
def get_applications():
    """Get all ArgoCD Applications and ApplicationSets with Helm chart analysis"""
    logger.info("API: Starting applications analysis request")
    try:
        logger.debug("Initializing services...")
        argocd_service = ArgoCDService()
        helm_service = HelmService()
        
        # Get all applications and application sets
        logger.info("Fetching ArgoCD resources...")
        applications = argocd_service.get_all_applications()
        application_sets = argocd_service.get_all_application_sets()
        
        logger.info(f"Processing {len(applications)} applications and {len(application_sets)} application sets")
        
        # Analyze Helm charts in applications
        logger.debug("Analyzing Helm charts in applications...")
        for i, app in enumerate(applications):
            logger.debug(f"Processing application {i+1}/{len(applications)}: {app.get('metadata', {}).get('name', 'unknown')}")
            app['helm_charts'] = helm_service.analyze_helm_charts(app)
            logger.debug(f"Found {len(app['helm_charts'])} Helm charts in application")
            
            # Get available versions for each chart
            for j, chart in enumerate(app['helm_charts']):
                logger.debug(f"Getting versions for chart {j+1}/{len(app['helm_charts'])}: {chart['chart_name']}")
                chart['available_versions'] = helm_service.get_available_versions(chart)
                logger.debug(f"Found {len(chart['available_versions'])} available versions")
        
        # Analyze Helm charts in application sets
        logger.debug("Analyzing Helm charts in application sets...")
        for i, app_set in enumerate(application_sets):
            logger.debug(f"Processing application set {i+1}/{len(application_sets)}: {app_set.get('metadata', {}).get('name', 'unknown')}")
            app_set['helm_charts'] = helm_service.analyze_helm_charts(app_set)
            logger.debug(f"Found {len(app_set['helm_charts'])} Helm charts in application set")
            
            # Get available versions for each chart
            for j, chart in enumerate(app_set['helm_charts']):
                logger.debug(f"Getting versions for chart {j+1}/{len(app_set['helm_charts'])}: {chart['chart_name']}")
                chart['available_versions'] = helm_service.get_available_versions(chart)
                logger.debug(f"Found {len(chart['available_versions'])} available versions")
        
        logger.info("Analysis complete, returning response")
        return jsonify({
            'applications': applications,
            'application_sets': application_sets
        })
    except Exception as e:
        logger.error(f"Error in get_applications: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/chart-versions', methods=['POST'])
def get_chart_versions():
    """Get available versions for a specific chart"""
    logger.info("API: Chart versions request received")
    try:
        data = request.get_json()
        repo_url = data.get('repo_url')
        chart_name = data.get('chart_name')
        
        logger.debug(f"Getting versions for chart: {chart_name} from {repo_url}")
        
        helm_service = HelmService()
        versions = helm_service.get_available_versions({
            'repo_url': repo_url,
            'chart_name': chart_name
        })
        
        logger.info(f"Found {len(versions)} versions for {chart_name}")
        return jsonify({'versions': versions})
    except Exception as e:
        logger.error(f"Error in get_chart_versions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500 
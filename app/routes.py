from flask import Blueprint, render_template, jsonify, request
from app.services.argocd_service import ArgoCDService
from app.services.helm_service import HelmService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/api/applications')
def get_applications():
    """Get all ArgoCD Applications and ApplicationSets with Helm chart analysis"""
    try:
        argocd_service = ArgoCDService()
        helm_service = HelmService()
        
        # Get all applications and application sets
        applications = argocd_service.get_all_applications()
        application_sets = argocd_service.get_all_application_sets()
        
        # Analyze Helm charts in applications
        for app in applications:
            app['helm_charts'] = helm_service.analyze_helm_charts(app)
            for chart in app['helm_charts']:
                chart['available_versions'] = helm_service.get_available_versions(chart)
        
        # Analyze Helm charts in application sets
        for app_set in application_sets:
            app_set['helm_charts'] = helm_service.analyze_helm_charts(app_set)
            for chart in app_set['helm_charts']:
                chart['available_versions'] = helm_service.get_available_versions(chart)
        
        return jsonify({
            'applications': applications,
            'application_sets': application_sets
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/chart-versions', methods=['POST'])
def get_chart_versions():
    """Get available versions for a specific chart"""
    try:
        data = request.get_json()
        repo_url = data.get('repo_url')
        chart_name = data.get('chart_name')
        
        helm_service = HelmService()
        versions = helm_service.get_available_versions({
            'repo_url': repo_url,
            'chart_name': chart_name
        })
        
        return jsonify({'versions': versions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 
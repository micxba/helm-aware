#!/usr/bin/env python3
"""
Simple test script to verify the Helm Aware application
"""

import sys
import os
import importlib.util

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        # Test Flask app creation
        from app import create_app
        app = create_app()
        print("✅ Flask app created successfully")
        
        # Test services
        from app.services.argocd_service import ArgoCDService
        print("✅ ArgoCD service imported successfully")
        
        from app.services.helm_service import HelmService
        print("✅ Helm service imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_helm_service():
    """Test Helm service functionality"""
    print("\nTesting Helm service...")
    
    try:
        from app.services.helm_service import HelmService
        
        helm_service = HelmService()
        
        # Test chart detection
        test_source = {
            'repoURL': 'https://charts.bitnami.com/bitnami',
            'chart': 'nginx',
            'targetRevision': '13.2.0'
        }
        
        is_helm = helm_service._is_helm_chart(test_source)
        print(f"✅ Helm chart detection: {is_helm}")
        
        # Test info extraction
        chart_info = helm_service._extract_helm_info(test_source)
        if chart_info:
            print(f"✅ Chart info extraction: {chart_info['chart_name']} {chart_info['chart_version']}")
        else:
            print("❌ Chart info extraction failed")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Helm service test failed: {e}")
        return False

def test_routes():
    """Test that routes are properly configured"""
    print("\nTesting routes...")
    
    try:
        from app import create_app
        
        app = create_app()
        
        # Check if routes are registered
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        expected_routes = ['/', '/api/applications', '/api/chart-versions']
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route {route} found")
            else:
                print(f"❌ Route {route} not found")
                return False
                
        return True
    except Exception as e:
        print(f"❌ Routes test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Helm Aware Application")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_helm_service,
        test_routes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Application is ready to run.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 
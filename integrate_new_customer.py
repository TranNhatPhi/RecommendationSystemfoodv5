"""
🔗 INTEGRATION SCRIPT FOR NEW CUSTOMER SYSTEM
============================================

This script integrates the new customer registration system with the main Flask app.

Author: AI Assistant
Date: June 19, 2025
"""

from new_customer_registration import add_new_customer_routes
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def integrate_new_customer_system(app):
    """
    Integrate new customer registration system with Flask app

    Args:
        app: Flask application instance
    """
    print("🔗 Integrating new customer registration system...")

    try:
        # Add new customer routes
        add_new_customer_routes(app)

        print("✅ New customer system integrated successfully!")
        print("📋 Available routes:")
        print("   • GET  /new-customer - Registration form")
        print("   • POST /api/register-customer - Register new customer")
        print("   • POST /api/check-email - Check email availability")
        print("   • GET  /api/get-customer/<customer_id> - Get customer info")
        print("   • GET  /customer-welcome/<customer_id> - Welcome page")

        return True

    except Exception as e:
        print(f"❌ Error integrating new customer system: {e}")
        return False


def test_integration():
    """Test the integration"""
    from flask import Flask

    app = Flask(__name__)
    success = integrate_new_customer_system(app)

    if success:
        print("\n🧪 Testing routes...")
        with app.test_client() as client:
            # Test form route
            response = client.get('/new-customer')
            print(f"   • /new-customer: {response.status_code}")

            # Test API route (without data - should return 400)
            response = client.post('/api/register-customer',
                                   json={},
                                   content_type='application/json')
            print(f"   • /api/register-customer: {response.status_code}")

        print("✅ Integration test completed")
    else:
        print("❌ Integration test failed")


if __name__ == "__main__":
    test_integration()

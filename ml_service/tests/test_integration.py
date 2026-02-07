"""
Integration tests for ML Service (AI features only).

These tests run against the live service (requires Docker to be running).

Run with: pytest ml_service/tests/test_integration.py -v
"""

import pytest
import requests
import time
import os

# ============ Configuration ============

ML_SERVICE_URL = "http://localhost:8001"
# Check if running in CI/CD or local
IS_CI = os.getenv("CI", "false").lower() == "true"


# ============ Helpers ============


def wait_for_service(url: str, timeout: int = 30) -> bool:
    """Wait for a service to become available."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    return False


def api_request(
    url: str, method: str = "GET", data: dict = None, timeout: int = 30
) -> tuple[bool, dict]:
    """Make an API request and return (success, data)."""
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            return False, {"error": f"Unknown method: {method}"}

        # 503 is valid for AI endpoints if key is missing (handled in tests)
        success = response.status_code == 200 or response.status_code == 503
        try:
            response_data = response.json()
            # Add status code to data for test logic
            response_data["_status_code"] = response.status_code
        except:
            response_data = {
                "text": response.text[:200],
                "_status_code": response.status_code,
            }

        return success, response_data
    except Exception as e:
        return False, {"error": str(e)}


# ============ Fixtures ============


@pytest.fixture(scope="module")
def ml_service_available():
    """Check if ML service is available."""
    available = wait_for_service(ML_SERVICE_URL, timeout=5)
    if not available:
        pytest.skip(f"ML service not available at {ML_SERVICE_URL}")
    return True


# ============ Integration Tests ============


class TestMLServiceIntegration:
    """Integration tests for the ML service."""

    def test_service_health(self, ml_service_available):
        """Test ML service health endpoint."""
        success, data = api_request(f"{ML_SERVICE_URL}/health")

        assert success
        assert data["status"] == "healthy"
        # Check for AI enabled flag (key name might vary but concept is same)
        assert "ai_enabled" in data or "gemini_enabled" in data

    def test_root_endpoint(self, ml_service_available):
        """Test ML service root endpoint."""
        success, data = api_request(f"{ML_SERVICE_URL}/")

        assert success
        assert "version" in data
        assert "endpoints" in data


class TestAIIntegration:
    """Integration tests for AI-powered endpoints."""

    def test_enhance_description(self, ml_service_available):
        """Test description enhancement endpoint."""
        success, data = api_request(
            f"{ML_SERVICE_URL}/enhance-description",
            "POST",
            {
                "item_name": "Test Burger",
                "current_description": "A burger",
                "category": "Star",
                "price": 15.00,
                "cuisine_type": "American",
            },
            timeout=60,
        )

        assert success

        # If AI is not configured (503), that's a pass for integration (service is reachable)
        # If AI is configured (200), check response structure
        if data["_status_code"] == 200:
            assert "enhanced_description" in data
        elif data["_status_code"] == 503:
            assert "not available" in data.get("detail", "")
        else:
            pytest.fail(f"Unexpected status code: {data['_status_code']}")

    def test_sales_suggestions(self, ml_service_available):
        """Test sales suggestions endpoint."""
        success, data = api_request(
            f"{ML_SERVICE_URL}/sales-suggestions",
            "POST",
            {
                "item_name": "Test Item",
                "category": "Star",
                "price": 20.0,
                "cost": 10.0,
                "purchases": 100,
            },
            timeout=60,
        )

        assert success

        if data["_status_code"] == 200:
            assert "priority" in data
        elif data["_status_code"] == 503:
            assert "not available" in data.get("detail", "")
        else:
            pytest.fail(f"Unexpected status code: {data['_status_code']}")

    def test_menu_structure_analysis(self, ml_service_available):
        """Test menu structure analysis endpoint."""
        success, data = api_request(
            f"{ML_SERVICE_URL}/menu-structure",
            "POST",
            {
                "sections": [
                    {
                        "name": "Appetizers",
                        "items": [{"name": "Wings", "price": 10.0, "category": "Star"}],
                    }
                ]
            },
            timeout=60,
        )

        assert success

        if data["_status_code"] == 200:
            assert "overall_score" in data or "raw_response" in data
        elif data["_status_code"] == 503:
            assert "not available" in data.get("detail", "")

    def test_customer_recommendations(self, ml_service_available):
        """Test customer recommendations endpoint."""
        success, data = api_request(
            f"{ML_SERVICE_URL}/customer-recommendations",
            "POST",
            {
                "current_items": ["Burger"],
                "menu_items": [{"name": "Fries", "price": 5.0}],
                "budget_remaining": 10.0,
            },
            timeout=60,
        )

        assert success

        if data["_status_code"] == 200:
            assert "top_recommendation" in data or "raw_response" in data
        elif data["_status_code"] == 503:
            assert "not available" in data.get("detail", "")

    def test_generate_report(self, ml_service_available):
        """Test owner report generation endpoint."""
        success, data = api_request(
            f"{ML_SERVICE_URL}/generate-report",
            "POST",
            {"summary_data": {"total_sales": 1000}, "period": "weekly"},
            timeout=60,
        )

        assert success

        if data["_status_code"] == 200:
            assert "executive_summary" in data or "raw_response" in data
        elif data["_status_code"] == 503:
            assert "not available" in data.get("detail", "")

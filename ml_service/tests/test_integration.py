"""
Integration tests for ML Service (AI features only).

These tests run against the live service (requires Docker to be running).

Run with: pytest ml_service/tests/test_integration.py -v
Or: python ml_service/tests/test_integration.py
"""

import pytest
import requests
import time

# ============ Configuration ============

ML_SERVICE_URL = "http://localhost:8001"
BACKEND_URL = "http://localhost:8000"


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

        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"error": str(e)}


# ============ Fixtures ============


@pytest.fixture(scope="module")
def ml_service_available():
    """Check if ML service is available."""
    available = wait_for_service(ML_SERVICE_URL, timeout=10)
    if not available:
        pytest.skip("ML service not available. Start with: docker compose up -d")
    return True


@pytest.fixture(scope="module")
def backend_available():
    """Check if backend is available."""
    available = wait_for_service(BACKEND_URL, timeout=10)
    if not available:
        pytest.skip("Backend not available. Start with: docker compose up -d")
    return True


# ============ ML Service Integration Tests ============


class TestMLServiceIntegration:
    """Integration tests for the ML service."""

    def test_service_health(self, ml_service_available):
        """Test ML service health endpoint."""
        success, data = api_request(f"{ML_SERVICE_URL}/health")

        assert success
        assert data["status"] == "healthy"
        assert "ai_enabled" in data

    def test_root_endpoint(self, ml_service_available):
        """Test ML service root endpoint."""
        success, data = api_request(f"{ML_SERVICE_URL}/")

        assert success
        assert data["service"] == "Menu Engineering AI API"
        assert data["version"] == "3.0.0"


class TestAIIntegration:
    """Integration tests for AI-powered endpoints (requires OpenRouter API)."""

    def test_ai_status(self, ml_service_available):
        """Check if AI/OpenRouter is enabled."""
        success, data = api_request(f"{ML_SERVICE_URL}/health")

        assert success
        print(f"AI enabled: {data.get('ai_enabled')}")

    @pytest.mark.slow
    def test_enhance_description(self, ml_service_available):
        """Test description enhancement (makes real API call)."""
        success, data = api_request(
            f"{ML_SERVICE_URL}/enhance-description",
            "POST",
            {
                "item_name": "Grilled Salmon",
                "current_description": "Salmon with rice",
                "category": "Puzzle",
                "price": 24.99,
                "cuisine_type": "Seafood",
            },
            timeout=60,
        )

        if not success and "not available" in str(data):
            pytest.skip("OpenRouter API not configured")

        assert success
        assert "enhanced_description" in data or "raw_response" in data

    @pytest.mark.slow
    def test_enhance_description_with_custom_instructions(self, ml_service_available):
        """Test description enhancement with custom instructions."""
        success, data = api_request(
            f"{ML_SERVICE_URL}/enhance-description",
            "POST",
            {
                "item_name": "Grilled Salmon",
                "custom_instructions": "Mention sustainable sourcing from Alaska",
                "tone": "elegant",
                "include_allergens": True,
            },
            timeout=60,
        )

        if not success and "not available" in str(data):
            pytest.skip("OpenRouter API not configured")

        assert success

    @pytest.mark.slow
    def test_sales_suggestions(self, ml_service_available):
        """Test sales suggestions (makes real API call)."""
        success, data = api_request(
            f"{ML_SERVICE_URL}/sales-suggestions",
            "POST",
            {
                "item_name": "Premium Steak",
                "category": "Star",
                "price": 39.99,
                "cost": 15.00,
                "purchases": 150,
            },
            timeout=60,
        )

        if not success and "not available" in str(data):
            pytest.skip("OpenRouter API not configured")

        assert success
        assert "priority" in data or "raw_response" in data

    @pytest.mark.slow
    def test_menu_structure_analysis(self, ml_service_available):
        """Test menu structure analysis (makes real API call)."""
        success, data = api_request(
            f"{ML_SERVICE_URL}/menu-structure",
            "POST",
            {
                "sections": [
                    {
                        "name": "Appetizers",
                        "items": [
                            {"name": "Wings", "price": 12.99, "category": "Star"},
                            {"name": "Soup", "price": 6.99, "category": "Dog"},
                        ],
                    },
                    {
                        "name": "Mains",
                        "items": [
                            {"name": "Steak", "price": 34.99, "category": "Puzzle"},
                            {"name": "Burger", "price": 16.99, "category": "Plowhorse"},
                        ],
                    },
                ]
            },
            timeout=60,
        )

        if not success and "not available" in str(data):
            pytest.skip("OpenRouter API not configured")

        assert success

    @pytest.mark.slow
    def test_customer_recommendations(self, ml_service_available):
        """Test customer recommendations (makes real API call)."""
        success, data = api_request(
            f"{ML_SERVICE_URL}/customer-recommendations",
            "POST",
            {
                "current_items": ["Burger", "Fries"],
                "menu_items": [
                    {"name": "Milkshake", "price": 5.99, "section": "Beverages"},
                    {"name": "Onion Rings", "price": 4.99, "section": "Sides"},
                    {"name": "Cheesecake", "price": 7.99, "section": "Desserts"},
                ],
                "budget_remaining": 15.00,
            },
            timeout=60,
        )

        if not success and "not available" in str(data):
            pytest.skip("OpenRouter API not configured")

        assert success

    @pytest.mark.slow
    def test_generate_report(self, ml_service_available):
        """Test report generation (makes real API call)."""
        success, data = api_request(
            f"{ML_SERVICE_URL}/generate-report",
            "POST",
            {
                "summary_data": {
                    "total_sales": 25000,
                    "total_orders": 450,
                    "average_order_value": 55.56,
                    "top_items": ["Burger", "Pizza", "Wings"],
                    "category_breakdown": {
                        "Star": 8,
                        "Plowhorse": 12,
                        "Puzzle": 5,
                        "Dog": 3,
                    },
                },
                "period": "weekly",
            },
            timeout=60,
        )

        if not success and "not available" in str(data):
            pytest.skip("OpenRouter API not configured")

        assert success


# ============ Backend Integration Tests ============


class TestBackendMLIntegration:
    """Tests for backend-to-ML service integration."""

    def test_backend_health(self, backend_available):
        """Test backend health."""
        success, data = api_request(f"{BACKEND_URL}/api/menu/")
        assert success

    def test_ml_health_via_backend(self, backend_available, ml_service_available):
        """Test ML health check through the backend."""
        success, data = api_request(f"{BACKEND_URL}/api/menu/ml/health/")

        assert success
        assert data["status"] == "healthy"
        assert "ai_enabled" in data


# ============ Run as Script ============


def run_tests():
    """Run integration tests as a script."""
    print("=" * 60)
    print("  ML SERVICE INTEGRATION TESTS")
    print("=" * 60)

    # Check services
    print("\nChecking services...")
    ml_available = wait_for_service(ML_SERVICE_URL, timeout=5)
    backend_available = wait_for_service(BACKEND_URL, timeout=5)

    print(f"  ML Service: {'✅ Available' if ml_available else '❌ Not available'}")
    print(
        f"  Backend:    {'✅ Available' if backend_available else '❌ Not available'}"
    )

    if not ml_available:
        print("\n❌ ML service not running. Start with: docker compose up -d")
        return

    # Run tests
    tests_passed = 0
    tests_failed = 0

    test_cases = [
        ("Health Check", lambda: api_request(f"{ML_SERVICE_URL}/health")),
        ("Root Endpoint", lambda: api_request(f"{ML_SERVICE_URL}/")),
    ]

    # AI tests (may be slow or rate-limited)
    ai_tests = [
        (
            "Enhance Description",
            lambda: api_request(
                f"{ML_SERVICE_URL}/enhance-description",
                "POST",
                {"item_name": "Test Burger", "category": "Star", "price": 15.99},
                timeout=60,
            ),
        ),
        (
            "Sales Suggestions",
            lambda: api_request(
                f"{ML_SERVICE_URL}/sales-suggestions",
                "POST",
                {
                    "item_name": "Test",
                    "category": "Star",
                    "price": 20.0,
                    "cost": 8.0,
                    "purchases": 100,
                },
                timeout=60,
            ),
        ),
    ]

    print("\n" + "-" * 60)
    print("  Core Tests")
    print("-" * 60)

    for name, test_fn in test_cases:
        try:
            success, data = test_fn()
            if success:
                print(f"  ✅ {name}")
                tests_passed += 1
            else:
                print(f"  ❌ {name}: {data.get('error', 'Failed')}")
                tests_failed += 1
        except Exception as e:
            print(f"  ❌ {name}: {str(e)}")
            tests_failed += 1

    print("\n" + "-" * 60)
    print("  AI Tests (may be slow)")
    print("-" * 60)

    for name, test_fn in ai_tests:
        try:
            success, data = test_fn()
            if success:
                print(f"  ✅ {name}")
                tests_passed += 1
            elif "not available" in str(data):
                print(f"  ⏭️  {name}: Skipped (API not configured)")
            else:
                print(f"  ❌ {name}: {data.get('error', data.get('detail', 'Failed'))}")
                tests_failed += 1
        except Exception as e:
            print(f"  ❌ {name}: {str(e)}")
            tests_failed += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"  Results: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()

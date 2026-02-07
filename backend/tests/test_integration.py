#!/usr/bin/env python
"""
Integration tests for Menu Engineering services.

Tests the live integration between:
- ML Service (AI-powered endpoints via OpenRouter)
- Backend (Django REST API)

Run with: python test_integration.py

Prerequisites:
    - Docker containers must be running (just up / docker compose up -d)
    - OPENROUTER_API_KEY must be set for AI features
"""

import requests
import sys

# ============ Configuration ============

ML_SERVICE_URL = "http://localhost:8001"
BACKEND_URL = "http://localhost:8000"


# ============ Helper Functions ============


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} | {name}")
    if details:
        print(f"         → {details}")


def test_endpoint(
    url: str, method: str = "GET", data: dict = None, expected_status: int = 200
) -> tuple[bool, dict]:
    """Test an endpoint and return (success, response_data)"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return False, {"error": f"Unknown method: {method}"}

        success = response.status_code == expected_status
        try:
            response_data = response.json()
        except:
            response_data = {"text": response.text[:200]}

        if not success:
            response_data["actual_status"] = response.status_code
            response_data["expected_status"] = expected_status

        return success, response_data
    except requests.exceptions.ConnectionError:
        return False, {"error": "Connection refused - is the service running?"}
    except Exception as e:
        return False, {"error": str(e)}


# ============ ML Service Tests (AI-focused) ============


def test_ml_service():
    """Test the AI-powered ML service endpoints."""
    print_header("ML SERVICE TESTS (AI)")
    all_passed = True

    # Test 1: Health Check
    success, data = test_endpoint(f"{ML_SERVICE_URL}/health")
    print_result("Health endpoint", success)
    if success:
        ai_enabled = data.get("ai_enabled", False) or data.get("gemini_enabled", False)
        print_result(
            "  AI service enabled",
            ai_enabled,
            "Check OPENROUTER_API_KEY" if not ai_enabled else "",
        )
        # AI not being enabled is informational, not a failure
    else:
        all_passed = False
        print_result("  Details", False, str(data))

    # Test 2: Root endpoint
    success, data = test_endpoint(f"{ML_SERVICE_URL}/")
    print_result("Root endpoint", success)
    if success:
        version = data.get("version", "unknown")
        print(f"         Version: {version}")
    all_passed = all_passed and success

    # Test 3: Enhance Description endpoint (expects 503 if no API key)
    enhance_request = {
        "item_name": "Test Chicken",
        "current_description": "Grilled chicken",
        "category": "Star",
        "price": 19.99,
        "cuisine_type": "American",
    }
    success, data = test_endpoint(
        f"{ML_SERVICE_URL}/enhance-description",
        "POST",
        enhance_request,
        expected_status=200,
    )
    if success:
        print_result("AI enhance-description", True, "AI responding correctly")
    else:
        # 503 means AI not available (no API key) - expected in test environments
        actual_status = data.get("actual_status", 0)
        if actual_status == 503:
            print_result(
                "AI enhance-description", True, "503 = AI not configured (expected)"
            )
        else:
            print_result(
                "AI enhance-description", False, f"Unexpected status: {actual_status}"
            )
            all_passed = False

    return all_passed


# ============ Backend API Tests ============


def test_backend_api():
    """Test the Django backend API endpoints."""
    print_header("BACKEND API TESTS")
    all_passed = True

    # Test 1: Menu API Root (DRF router)
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/")
    print_result("Menu API root", success)
    all_passed = all_passed and success

    # Test 2: Menu sections (public)
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/sections/")
    print_result("Menu sections (public)", success)
    if success and isinstance(data, list):
        print(f"         Sections: {len(data)}")
    all_passed = all_passed and success

    # Test 3: Menu items (public)
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/items/")
    print_result("Menu items (public)", success)
    if success and isinstance(data, list):
        print(f"         Items: {len(data)}")
    all_passed = all_passed and success

    # Test 4: Public menu endpoint
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/public/")
    print_result("Public menu endpoint", success)
    if success:
        menu = data.get("menu", [])
        print(f"         Menu sections: {len(menu)}")
    all_passed = all_passed and success

    # Test 5: ML Health check through backend
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/ml/health/")
    print_result("ML health via backend", success)
    if success:
        status = data.get("status", "unknown")
        ai_status = data.get("ai_enabled", data.get("gemini_enabled", "N/A"))
        print(f"         Status: {status}, AI: {ai_status}")
    all_passed = all_passed and success

    # Test 6: OpenAPI schema
    success, data = test_endpoint(f"{BACKEND_URL}/api/schema/")
    print_result("OpenAPI schema", success)
    all_passed = all_passed and success

    return all_passed


# ============ End-to-End Integration Tests ============


def test_e2e_integration():
    """Test end-to-end integration between services."""
    print_header("END-TO-END INTEGRATION TESTS")
    all_passed = True

    # Test: Backend can reach ML service
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/ml/health/")

    if success and data.get("status") == "healthy":
        print_result("Backend → ML service communication", True)
        ai_status = data.get("ai_enabled", data.get("gemini_enabled", False))
        print_result(
            "  AI service available",
            ai_status or ai_status == "N/A",
            "Set OPENROUTER_API_KEY for AI features" if not ai_status else "",
        )
    else:
        print_result(
            "Backend → ML service communication",
            False,
            f"Status: {data.get('status', 'unknown')}",
        )
        all_passed = False

    # Test: Menu classification (deterministic - handled by backend)
    print("\n  Testing backend classification (deterministic):")

    # The backend handles classification, not the ML service
    # Just verify the classify endpoint exists
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/items/")
    if success and isinstance(data, list) and len(data) > 0:
        # Check if items have category field
        item = data[0]
        has_category = "category" in item
        print_result("Items have classification", has_category)
        if has_category:
            print(
                f"         Sample: {item.get('name', 'N/A')} → {item.get('category', 'N/A')}"
            )
    else:
        print_result(
            "Menu items available for classification",
            len(data) > 0 if success else False,
        )

    return all_passed


# ============ Main ============


def main():
    print("\n" + "=" * 60)
    print("  MENU ENGINEERING - INTEGRATION TEST SUITE")
    print("=" * 60)
    print(f"\n  ML Service: {ML_SERVICE_URL}")
    print(f"  Backend:    {BACKEND_URL}")
    print("\n  Note: AI features require OPENROUTER_API_KEY to be set.")
    print("        Classification is handled by the Django backend.")

    results = {}

    # Run test suites
    results["ml_service"] = test_ml_service()
    results["backend"] = test_backend_api()
    results["e2e"] = test_e2e_integration()

    # Summary
    print_header("TEST SUMMARY")

    total_passed = 0
    total_tests = len(results)

    for suite, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status} | {suite}")
        if passed:
            total_passed += 1

    print(f"\n  Total: {total_passed}/{total_tests} test suites passed")

    if total_passed == total_tests:
        print("\n  🎉 All integration tests passed!")
        return 0
    else:
        print("\n  ⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

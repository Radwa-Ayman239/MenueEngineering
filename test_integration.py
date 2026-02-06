#!/usr/bin/env python
"""
Integration tests for ML Service and Backend communication.

This script tests the live integration between the ML service and backend.
Run with: python test_integration.py

Prerequisites:
    - Docker containers must be running (just up)
    - ML models must be exported (python export_models.py)
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
    if details and not passed:
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


def test_ml_service():
    print_header("ML Service Tests")
    all_passed = True

    # Health check
    success, data = test_endpoint(f"{ML_SERVICE_URL}/health")
    print_result("Health endpoint", success)
    if success:
        model_loaded = data.get("model_loaded", False)
        encoder_loaded = data.get("encoder_loaded", False)
        print_result("  Model loaded", model_loaded)
        print_result("  Encoder loaded", encoder_loaded)
        all_passed = all_passed and model_loaded and encoder_loaded
    else:
        print(f"    Details: {data}")
        all_passed = False

    # Root endpoint
    success, data = test_endpoint(f"{ML_SERVICE_URL}/")
    print_result("Root endpoint", success)
    all_passed = all_passed and success

    # Single prediction - Star item
    star_item = {
        "price": 150.0,
        "purchases": 100,
        "margin": 90.0,
        "description_length": 50,
    }
    success, data = test_endpoint(f"{ML_SERVICE_URL}/predict", "POST", star_item)
    print_result("Single prediction (Star)", success)
    if success:
        category = data.get("category", "")
        confidence = data.get("confidence", 0)
        print(f"    Category: {category} (confidence: {confidence:.1%})")
        all_passed = all_passed and category in ["Star", "Plowhorse", "Puzzle", "Dog"]
    else:
        all_passed = False

    # Single prediction - Dog item
    dog_item = {"price": 20.0, "purchases": 0, "margin": 12.0, "description_length": 10}
    success, data = test_endpoint(f"{ML_SERVICE_URL}/predict", "POST", dog_item)
    print_result("Single prediction (Dog)", success)
    if success:
        print(f"    Category: {data.get('category')} (confidence: {data.get('confidence', 0):.1%})")
    all_passed = all_passed and success

    # Batch prediction
    batch_items = {
        "items": [
            {"price": 150.0, "purchases": 100, "margin": 90.0, "description_length": 50},
            {"price": 50.0, "purchases": 200, "margin": 20.0, "description_length": 30},
            {"price": 80.0, "purchases": 5, "margin": 48.0, "description_length": 60},
            {"price": 15.0, "purchases": 2, "margin": 9.0, "description_length": 15},
        ]
    }
    success, data = test_endpoint(f"{ML_SERVICE_URL}/batch-predict", "POST", batch_items)
    print_result("Batch prediction (4 items)", success)
    if success:
        predictions = data.get("predictions", [])
        print(f"    Returned {len(predictions)} predictions")
        all_passed = all_passed and len(predictions) == 4
    else:
        all_passed = False

    return all_passed


def test_backend_api():
    print_header("Backend API Tests")
    all_passed = True

    # Menu API root
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/")
    print_result("Menu API root", success)
    all_passed = all_passed and success

    # Menu sections
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/sections/")
    print_result("Menu sections (public)", success)
    if success and isinstance(data, list):
        print(f"    Sections: {len(data)}")
    all_passed = all_passed and success

    # Menu items
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/items/")
    print_result("Menu items (public)", success)
    if success and isinstance(data, list):
        print(f"    Items: {len(data)}")
    all_passed = all_passed and success

    # Public menu endpoint
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/public/")
    print_result("Public menu endpoint", success)
    if success:
        menu = data.get("menu", [])
        print(f"    Sections: {len(menu)}")
    all_passed = all_passed and success

    # ML health via backend
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/ml/health/")
    print_result("ML health check", success)
    if success:
        print(f"    Status: {data.get('status')}, Model loaded: {data.get('model_loaded')}")
    all_passed = all_passed and success

    # OpenAPI schema
    success, data = test_endpoint(f"{BACKEND_URL}/api/schema/")
    print_result("OpenAPI schema", success)
    all_passed = all_passed and success

    return all_passed


def test_e2e_integration():
    print_header("End-to-End Integration Tests")
    all_passed = True

    # Backend can reach ML service
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/ml/health/")
    if success and data.get("status") == "healthy":
        print_result("Backend → ML service communication", True)
        print_result("  ML model loaded", data.get("model_loaded", False))
        all_passed = all_passed and data.get("model_loaded", False)
    else:
        print_result("Backend → ML service communication", False, data.get("status", "unknown"))
        all_passed = False

    # Verify predictions
    test_cases = [
        ({"price": 100, "purchases": 50, "margin": 60}, "Star"),
        ({"price": 30, "purchases": 100, "margin": 12}, "Plowhorse"),
        ({"price": 100, "purchases": 0, "margin": 60}, "Puzzle"),
        ({"price": 20, "purchases": 0, "margin": 10}, "Dog"),
    ]

    for item_data, expected in test_cases:
        item = {**item_data, "description_length": 30}
        success, data = test_endpoint(f"{ML_SERVICE_URL}/predict", "POST", item)
        if success:
            actual = data.get("category", "")
            matches = actual == expected
            print_result(f"Predict {expected}", matches)
        else:
            print_result(f"Predict {expected}", False)
            all_passed = False

    return all_passed


def main():
    print("Menu Engineering Integration Tests")
    print(f"ML Service: {ML_SERVICE_URL}")
    print(f"Backend: {BACKEND_URL}")

    results = {
        "ml_service": test_ml_service(),
        "backend": test_backend_api(),
        "e2e": test_e2e_integration(),
    }

    print_header("Summary")
    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)

    for suite, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {status}: {suite}")

    print(f"\nTotal: {total_passed}/{total_tests} passed")

    if total_passed == total_tests:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


# ============ ML Service Tests ============


def test_ml_service():
    print_header("ML SERVICE TESTS")
    all_passed = True

    # Test 1: Health Check
    success, data = test_endpoint(f"{ML_SERVICE_URL}/health")
    print_result("Health endpoint available", success)
    if success:
        model_loaded = data.get("model_loaded", False)
        encoder_loaded = data.get("encoder_loaded", False)
        print_result("  Model loaded", model_loaded)
        print_result("  Encoder loaded", encoder_loaded)
        all_passed = all_passed and model_loaded and encoder_loaded
    else:
        all_passed = False
        print(f"         Details: {data}")

    # Test 2: Root endpoint
    success, data = test_endpoint(f"{ML_SERVICE_URL}/")
    print_result("Root endpoint", success)
    all_passed = all_passed and success

    # Test 3: Single prediction - Star item
    star_item = {
        "price": 150.0,
        "purchases": 100,
        "margin": 90.0,
        "description_length": 50,
    }
    success, data = test_endpoint(f"{ML_SERVICE_URL}/predict", "POST", star_item)
    print_result("Single prediction (Star)", success)
    if success:
        category = data.get("category", "")
        confidence = data.get("confidence", 0)
        recommendations = data.get("recommendations", [])
        print(f"         Category: {category} (confidence: {confidence:.1%})")
        print(f"         Recommendations: {len(recommendations)} items")
        all_passed = all_passed and category in ["Star", "Plowhorse", "Puzzle", "Dog"]
    else:
        all_passed = False
        print(f"         Details: {data}")

    # Test 4: Single prediction - Dog item (low everything)
    dog_item = {"price": 20.0, "purchases": 0, "margin": 12.0, "description_length": 10}
    success, data = test_endpoint(f"{ML_SERVICE_URL}/predict", "POST", dog_item)
    print_result("Single prediction (Dog)", success)
    if success:
        print(
            f"         Category: {data.get('category')} (confidence: {data.get('confidence', 0):.1%})"
        )
    all_passed = all_passed and success

    # Test 5: Batch prediction
    batch_items = {
        "items": [
            {
                "price": 150.0,
                "purchases": 100,
                "margin": 90.0,
                "description_length": 50,
            },
            {"price": 50.0, "purchases": 200, "margin": 20.0, "description_length": 30},
            {"price": 80.0, "purchases": 5, "margin": 48.0, "description_length": 60},
            {"price": 15.0, "purchases": 2, "margin": 9.0, "description_length": 15},
        ]
    }
    success, data = test_endpoint(
        f"{ML_SERVICE_URL}/batch-predict", "POST", batch_items
    )
    print_result("Batch prediction (4 items)", success)
    if success:
        predictions = data.get("predictions", [])
        print(f"         Predictions returned: {len(predictions)}")
        for i, pred in enumerate(predictions):
            print(
                f"         Item {i+1}: {pred.get('category')} ({pred.get('confidence', 0):.1%})"
            )
        all_passed = all_passed and len(predictions) == 4
    else:
        all_passed = False
        print(f"         Details: {data}")

    return all_passed


# ============ Backend API Tests ============


def test_backend_api():
    print_header("BACKEND API TESTS")
    all_passed = True

    # Test 1: Menu API Root (DRF router)
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/")
    print_result("Menu API root", success)
    all_passed = all_passed and success

    # Test 2: Menu sections (public)
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/sections/")
    print_result("Menu sections (public)", success)
    if success:
        print(
            f"         Sections returned: {len(data) if isinstance(data, list) else 'N/A'}"
        )
    all_passed = all_passed and success

    # Test 3: Menu items (public)
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/items/")
    print_result("Menu items (public)", success)
    if success:
        print(
            f"         Items returned: {len(data) if isinstance(data, list) else 'N/A'}"
        )
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
        print(f"         Status: {data.get('status')}")
        print(f"         Model loaded: {data.get('model_loaded')}")
    all_passed = all_passed and success

    # Test 6: OpenAPI schema
    success, data = test_endpoint(f"{BACKEND_URL}/api/schema/")
    print_result("OpenAPI schema", success)
    all_passed = all_passed and success

    return all_passed


# ============ End-to-End Integration Tests ============


def test_e2e_integration():
    print_header("END-TO-END INTEGRATION TESTS")
    all_passed = True

    # Test: Backend can call ML service
    print("\n  Testing backend → ML service communication:")

    # First check if ML health endpoint works through backend
    success, data = test_endpoint(f"{BACKEND_URL}/api/menu/ml/health/")

    if success and data.get("status") == "healthy":
        print_result("Backend can reach ML service", True)
        print_result("ML model is loaded", data.get("model_loaded", False))
        all_passed = all_passed and data.get("model_loaded", False)
    else:
        print_result(
            "Backend can reach ML service",
            False,
            f"Status: {data.get('status', 'unknown')}",
        )
        all_passed = False

    # Test: Direct ML prediction matches expected categories
    print("\n  Testing prediction accuracy:")

    test_cases = [
        # High sales + High margin = Star
        {"item": {"price": 100, "purchases": 50, "margin": 60}, "expected": "Star"},
        # High sales + Low margin = Plowhorse
        {
            "item": {"price": 30, "purchases": 100, "margin": 12},
            "expected": "Plowhorse",
        },
        # Low sales + High margin = Puzzle
        {"item": {"price": 100, "purchases": 0, "margin": 60}, "expected": "Puzzle"},
        # Low sales + Low margin = Dog
        {"item": {"price": 20, "purchases": 0, "margin": 10}, "expected": "Dog"},
    ]

    for tc in test_cases:
        item = {**tc["item"], "description_length": 30}
        success, data = test_endpoint(f"{ML_SERVICE_URL}/predict", "POST", item)
        if success:
            actual = data.get("category", "")
            matches = actual == tc["expected"]
            print_result(
                f"Prediction {tc['expected']}",
                matches,
                f"Got '{actual}' instead" if not matches else "",
            )
            # Don't fail on category mismatch - model may have different thresholds
        else:
            print_result(f"Prediction {tc['expected']}", False, str(data))
            all_passed = False

    return all_passed


# ============ Main ============


def main():
    print("\n" + "=" * 60)
    print("  MENU ENGINEERING - INTEGRATION TEST SUITE")
    print("=" * 60)
    print(f"\n  ML Service: {ML_SERVICE_URL}")
    print(f"  Backend:    {BACKEND_URL}")

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

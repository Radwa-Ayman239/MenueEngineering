"""
Pytest tests for the ML Service (AI features only).

Tests cover:
- AI-powered endpoints (enhance-description, sales-suggestions, etc.)
- Health checks
- Error handling

Run with: docker compose exec ml_service pytest ml_service/tests/test_ml_service.py
"""

import pytest
import sys
import os
import httpx
from unittest.mock import patch, MagicMock

# ============ Dependency Management ============
# Fix Compatibility between Starlette < 0.36.3 and HTTPX >= 0.28.0
# HTTPX 0.28+ removed `app` argument from Client, but older Starlette TestClient passes it.
# We monkeypatch httpx.Client.__init__ to handle 'app' argument by creating ASGITransport.

_original_client_init = httpx.Client.__init__


def _client_init_shim(self, *args, **kwargs):
    if "app" in kwargs:
        app = kwargs.pop("app")
        if "transport" not in kwargs and hasattr(httpx, "ASGITransport"):
            kwargs["transport"] = httpx.ASGITransport(app=app)

    _original_client_init(self, *args, **kwargs)


httpx.Client.__init__ = _client_init_shim

# ============ Imports ============

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from fastapi.testclient import TestClient

# ============ Fixtures ============


@pytest.fixture
def client():
    """Create a test client for the ML service."""
    # Now TestClient should work thanks to the shim
    return TestClient(app)


@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response."""
    choice = MagicMock()
    choice.message.content = '{"enhanced_description": "Delicious grilled chicken", "key_selling_points": ["Fresh", "Tender"], "tips": ["Add herbs"]}'

    response = MagicMock()
    response.choices = [choice]
    return response


# ============ Health & Root Endpoint Tests ============


class TestHealthEndpoints:
    """Tests for health and info endpoints."""

    def test_health_check(self, client):
        """Test health endpoint returns correct structure."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "ai_enabled" in data
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "endpoints" in data


# ============ AI Endpoint Tests ============


class TestAIEndpoints:
    """Tests for OpenRouter AI-powered endpoints."""

    def test_enhance_description_valid(self, client, mock_openrouter_response):
        """Test description enhancement with valid input."""
        with patch("openrouter_service.get_client") as mock_get_client:
            mock_client_instance = MagicMock()
            mock_client_instance.chat.completions.create.return_value = (
                mock_openrouter_response
            )
            mock_get_client.return_value = mock_client_instance

            response = client.post(
                "/enhance-description",
                json={
                    "item_name": "Grilled Chicken",
                    "current_description": "Chicken with vegetables",
                    "category": "Puzzle",
                    "price": 18.99,
                    "cuisine_type": "American",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "enhanced_description" in data or "raw_response" in data

    def test_enhance_description_minimal_input(self, client, mock_openrouter_response):
        """Test description enhancement with minimal input."""
        with patch("openrouter_service.get_client") as mock_get_client:
            mock_client_instance = MagicMock()
            mock_client_instance.chat.completions.create.return_value = (
                mock_openrouter_response
            )
            mock_get_client.return_value = mock_client_instance

            response = client.post("/enhance-description", json={"item_name": "Burger"})

            assert response.status_code == 200

    def test_enhance_description_with_custom_instructions(
        self, client, mock_openrouter_response
    ):
        """Test description enhancement with custom instructions."""
        with patch("openrouter_service.get_client") as mock_get_client:
            mock_client_instance = MagicMock()
            mock_client_instance.chat.completions.create.return_value = (
                mock_openrouter_response
            )
            mock_get_client.return_value = mock_client_instance

            response = client.post(
                "/enhance-description",
                json={
                    "item_name": "Grilled Salmon",
                    "custom_instructions": "Mention sustainable sourcing",
                    "tone": "elegant",
                    "include_allergens": True,
                },
            )

            assert response.status_code == 200

    def test_sales_suggestions_valid(self, client):
        """Test sales suggestions with valid input."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            '{"priority": "high", "suggested_price": 45.99, "immediate_actions": ["Action 1"], "marketing_tips": ["Tip 1"], "estimated_impact": "20% increase"}'
        )

        with patch("openrouter_service.get_client") as mock_get_client:
            mock_client_instance = MagicMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client_instance

            response = client.post(
                "/sales-suggestions",
                json={
                    "item_name": "Lobster Tail",
                    "category": "Star",
                    "price": 45.99,
                    "cost": 18.00,
                    "purchases": 120,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "priority" in data or "raw_response" in data

    def test_menu_structure_valid(self, client):
        """Test menu structure analysis with valid input."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            '{"overall_score": 7, "section_order_recommendation": ["Appetizers", "Mains"], "general_recommendations": ["Rec 1"]}'
        )

        with patch("openrouter_service.get_client") as mock_get_client:
            mock_client_instance = MagicMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client_instance

            response = client.post(
                "/menu-structure",
                json={
                    "sections": [
                        {
                            "name": "Appetizers",
                            "items": [
                                {"name": "Wings", "price": 12.99, "category": "Star"}
                            ],
                        },
                        {
                            "name": "Mains",
                            "items": [
                                {"name": "Steak", "price": 29.99, "category": "Puzzle"}
                            ],
                        },
                    ]
                },
            )

            assert response.status_code == 200

    def test_customer_recommendations_valid(self, client):
        """Test customer recommendations with valid input."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            '{"top_recommendation": {"item": "Fries", "reason": "Pairs well", "pitch": "Great with your burger!"}, "alternatives": [], "upsells": []}'
        )

        with patch("openrouter_service.get_client") as mock_get_client:
            mock_client_instance = MagicMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = mock_client_instance

            response = client.post(
                "/customer-recommendations",
                json={
                    "current_items": ["Burger"],
                    "menu_items": [
                        {"name": "Fries", "price": 5.99, "section": "Sides"},
                        {"name": "Salad", "price": 7.99, "section": "Sides"},
                    ],
                },
            )

            assert response.status_code == 200

    def test_generate_report_valid(self, client):
        """Test report generation."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"executive_summary": "Good"}'

        with patch("openrouter_service.get_client") as mock_get_client:
            mock_get_client.return_value.chat.completions.create.return_value = (
                mock_response
            )
            response = client.post(
                "/generate-report",
                json={
                    "summary_data": {"total_sales": 1},
                    "period": "weekly",
                },
            )
            assert response.status_code == 200

    def test_api_not_configured(self, client):
        """Test 503 when API disabled."""
        with patch("main.AI_ENABLED", False):
            response = client.post("/enhance-description", json={"item_name": "Test"})
            assert response.status_code == 503

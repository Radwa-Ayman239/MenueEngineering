"""
Pytest tests for the ML Service (AI features only).

Tests cover:
- AI-powered endpoints (enhance-description, sales-suggestions, etc.)
- Health checks
- Error handling

Run with: pytest ml_service/tests/test_ml_service.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ============ Fixtures ============


@pytest.fixture
def client():
    """Create a test client for the ML service."""
    from main import app

    return TestClient(app)


@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response."""
    return MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"enhanced_description": "Delicious grilled chicken", "key_selling_points": ["Fresh", "Tender"], "tips": ["Add herbs"]}'
                )
            )
        ]
    )


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
        assert data["service"] == "Menu Engineering AI API"
        assert data["version"] == "3.0.0"
        assert "endpoints" in data
        assert any("enhance-description" in ep for ep in data["endpoints"])


# ============ AI Endpoint Tests ============


class TestAIEndpoints:
    """Tests for OpenRouter AI-powered endpoints."""

    def test_enhance_description_valid(self, client, mock_openrouter_response):
        """Test description enhancement with valid input."""
        with patch("openrouter_service.get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = (
                mock_openrouter_response
            )

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
        with patch("openrouter_service.get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = (
                mock_openrouter_response
            )

            response = client.post("/enhance-description", json={"item_name": "Burger"})

            assert response.status_code == 200

    def test_enhance_description_with_custom_instructions(
        self, client, mock_openrouter_response
    ):
        """Test description enhancement with custom instructions."""
        with patch("openrouter_service.get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = (
                mock_openrouter_response
            )

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
        mock_response = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content='{"priority": "high", "suggested_price": 45.99, "immediate_actions": ["Action 1"], "marketing_tips": ["Tip 1"], "estimated_impact": "20% increase"}'
                    )
                )
            ]
        )

        with patch("openrouter_service.get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = (
                mock_response
            )

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
        mock_response = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content='{"overall_score": 7, "section_order_recommendation": ["Appetizers", "Mains"], "general_recommendations": ["Rec 1"]}'
                    )
                )
            ]
        )

        with patch("openrouter_service.get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = (
                mock_response
            )

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
        mock_response = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content='{"top_recommendation": {"item": "Fries", "reason": "Pairs well", "pitch": "Great with your burger!"}, "alternatives": [], "upsells": []}'
                    )
                )
            ]
        )

        with patch("openrouter_service.get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = (
                mock_response
            )

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
        """Test owner report generation with valid input."""
        mock_response = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content='{"executive_summary": "Good week", "highlights": ["Sales up"], "concerns": [], "top_recommendations": [], "next_steps": ["Continue marketing"]}'
                    )
                )
            ]
        )

        with patch("openrouter_service.get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = (
                mock_response
            )

            response = client.post(
                "/generate-report",
                json={
                    "summary_data": {
                        "total_sales": 15000,
                        "top_items": ["Burger", "Pizza"],
                        "category_breakdown": {
                            "Star": 5,
                            "Plowhorse": 8,
                            "Puzzle": 3,
                            "Dog": 2,
                        },
                    },
                    "period": "weekly",
                },
            )

            assert response.status_code == 200

    def test_ai_endpoint_api_not_configured(self, client):
        """Test AI endpoint when API is not configured."""
        with patch("main.AI_ENABLED", False):
            response = client.post(
                "/enhance-description", json={"item_name": "Test Item"}
            )

            assert response.status_code == 503
            assert "not available" in response.json()["detail"]


# ============ JSON Parsing Tests ============


class TestJSONParsing:
    """Tests for JSON response parsing."""

    def test_parse_clean_json(self):
        """Test parsing clean JSON response."""
        from openrouter_service import parse_json_response

        result = parse_json_response('{"key": "value", "number": 42}')
        assert result == {"key": "value", "number": 42}

    def test_parse_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        from openrouter_service import parse_json_response

        result = parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_with_just_backticks(self):
        """Test parsing JSON with just backticks."""
        from openrouter_service import parse_json_response

        result = parse_json_response('```\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns error."""
        from openrouter_service import parse_json_response

        result = parse_json_response("This is not JSON")
        assert "error" in result
        assert "raw_response" in result

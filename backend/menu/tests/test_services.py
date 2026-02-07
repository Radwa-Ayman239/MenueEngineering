import unittest
from unittest.mock import patch, Mock
import httpx
from ..services import MLService, MLServiceError


class MLServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = MLService()
        self.base_url = "http://ml_service:8001"

    @patch("httpx.Client")
    def test_health_check_healthy(self, mock_client_cls):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy", "ai_enabled": True}

        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        result = self.service.health_check()
        self.assertEqual(result["status"], "healthy")

    @patch("httpx.Client")
    def test_enhance_description_sync(self, mock_client_cls):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "enhanced_description": "Tasty burger",
            "key_selling_points": ["Juicy"],
            "tips": [],
        }

        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        result = self.service.enhance_description_sync(
            item_name="Burger", current_description="Good"
        )
        self.assertEqual(result["enhanced_description"], "Tasty burger")
        mock_client_instance.post.assert_called_with(
            f"{self.base_url}/enhance-description",
            json={
                "item_name": "Burger",
                "current_description": "Good",
                "category": "Unknown",
                "price": 0.0,
                "cuisine_type": "restaurant",
            },
        )

    @patch("httpx.Client")
    def test_get_sales_suggestions_sync(self, mock_client_cls):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "priority": "high",
            "suggested_price": 12.99,
        }

        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        result = self.service.get_sales_suggestions_sync(
            item_name="Burger",
            category="Star",
            price=10.0,
            cost=5.0,
            purchases=100,
        )
        self.assertEqual(result["priority"], "high")

    @patch("httpx.Client")
    def test_analyze_menu_structure_sync(self, mock_client_cls):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"overall_score": 8}

        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        sections = [{"name": "Mains", "items": []}]
        result = self.service.analyze_menu_structure_sync(sections)
        self.assertEqual(result["overall_score"], 8)

    @patch("httpx.Client")
    def test_get_customer_recommendations_sync(self, mock_client_cls):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"top_recommendation": "Burger"}

        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        result = self.service.get_customer_recommendations_sync(
            current_items=[], menu_items=[]
        )
        self.assertEqual(result["top_recommendation"], "Burger")

    @patch("httpx.Client")
    def test_generate_owner_report_sync(self, mock_client_cls):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"executive_summary": "Good job"}

        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        result = self.service.generate_owner_report_sync(summary_data={})
        self.assertEqual(result["executive_summary"], "Good job")

    @patch("httpx.Client")
    def test_service_error_handling(self, mock_client_cls):
        """Test error handling for 503 and other errors"""
        mock_response = Mock()
        mock_response.status_code = 503

        error = httpx.HTTPStatusError(
            "Service Unavailable", request=Mock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = error

        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        with self.assertRaises(MLServiceError):
            self.service.enhance_description_sync(item_name="Burger")

import unittest
from unittest.mock import patch, Mock, AsyncMock
import httpx
from ..services import MLService, MLServiceError


class MLServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.service = MLService()
        self.base_url = "http://ml_service:8001"
        self.sample_payload = {
            "price": 100.0,
            "purchases": 50,
            "margin": 20.0,
            "description_length": 10,
        }
        self.success_response = {
            "category": "star",
            "confidence": 0.95,
            "recommendations": ["Promote heavily"],
        }

    # ==========================================
    # Synchronous Tests (predict_sync)
    # ==========================================

    @patch("httpx.Client")
    def test_predict_sync_success(self, mock_client_cls):
        """Test successful synchronous prediction."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.success_response

        # Setup mock client context manager
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        # Call service
        result = self.service.predict_sync(**self.sample_payload)

        # Assertions
        self.assertEqual(result["category"], "star")
        mock_client_instance.post.assert_called_once_with(
            f"{self.base_url}/predict", json=self.sample_payload
        )

    @patch("httpx.Client")
    def test_predict_sync_connection_error(self, mock_client_cls):
        """Test handling of connection errors."""
        mock_client_instance = Mock()
        mock_client_instance.post.side_effect = httpx.ConnectError("Connection refused")
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        with self.assertRaises(MLServiceError) as context:
            self.service.predict_sync(**self.sample_payload)

        self.assertIn("unavailable", str(context.exception))

    @patch("httpx.Client")
    def test_predict_sync_http_error(self, mock_client_cls):
        """Test handling of non-200 HTTP responses."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        # Configure raise_for_status to actually raise an error
        error = httpx.HTTPStatusError("Error", request=Mock(), response=mock_response)
        mock_response.raise_for_status.side_effect = error

        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        with self.assertRaises(MLServiceError) as context:
            self.service.predict_sync(**self.sample_payload)

        self.assertIn("ML service error", str(context.exception))

    # ==========================================
    # Asynchronous Tests (predict)
    # ==========================================

    @patch("httpx.AsyncClient")
    async def test_predict_async_success(self, mock_client_cls):
        """Test successful async prediction."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.success_response

        # Setup async mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client_instance

        # Call service (await it)
        result = await self.service.predict(**self.sample_payload)

        # Assertions
        self.assertEqual(result["category"], "star")
        mock_client_instance.post.assert_called_once()

    # ==========================================
    # Batch Prediction Tests
    # ==========================================

    @patch("httpx.Client")
    def test_batch_predict_sync(self, mock_client_cls):
        """Test batch prediction."""
        batch_items = [self.sample_payload, self.sample_payload]
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "predictions": [self.success_response, self.success_response]
        }

        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        results = self.service.batch_predict_sync(batch_items)

        self.assertEqual(len(results), 2)
        mock_client_instance.post.assert_called_with(
            f"{self.base_url}/batch-predict", json={"items": batch_items}
        )

    # ==========================================
    # Health Check Tests
    # ==========================================

    @patch("httpx.Client")
    def test_health_check_healthy(self, mock_client_cls):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy", "model_loaded": True}

        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        result = self.service.health_check()
        self.assertEqual(result["status"], "healthy")

    @patch("httpx.Client")
    def test_health_check_unhealthy(self, mock_client_cls):
        """Test health check when service is down."""
        mock_client_instance = Mock()
        # Simulate any exception (connection, timeout, etc)
        mock_client_instance.get.side_effect = Exception("Down")
        mock_client_cls.return_value.__enter__.return_value = mock_client_instance

        result = self.service.health_check()
        self.assertEqual(result["status"], "unhealthy")
        self.assertFalse(result["model_loaded"])

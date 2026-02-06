"""
Service layer for connecting Django to the FastAPI ML service.
"""

import httpx
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MLServiceError(Exception):
    """Custom exception for ML service errors"""

    pass


class MLService:
    """
    Client for the FastAPI ML service.

    Usage:
        ml_service = MLService()
        result = await ml_service.predict(price=129.0, purchases=50, margin=77.4)
        # or synchronously:
        result = ml_service.predict_sync(price=129.0, purchases=50, margin=77.4)
    """

    def __init__(self):
        self.base_url = getattr(settings, "ML_SERVICE_URL", "http://ml_service:8001")
        self.timeout = 10.0  # seconds

    def predict_sync(
        self, price: float, purchases: int, margin: float, description_length: int = 0
    ) -> dict:
        """
        Synchronous prediction - blocks until result is ready.

        Returns:
            dict with keys: category, confidence, recommendations
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/predict",
                    json={
                        "price": price,
                        "purchases": purchases,
                        "margin": margin,
                        "description_length": description_length,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError:
            logger.error(f"Cannot connect to ML service at {self.base_url}")
            raise MLServiceError("ML service is unavailable. Please try again later.")
        except httpx.TimeoutException:
            logger.error("ML service request timed out")
            raise MLServiceError("ML service request timed out.")
        except httpx.HTTPStatusError as e:
            logger.error(f"ML service returned error: {e.response.status_code}")
            raise MLServiceError(f"ML service error: {e.response.text}")
        except Exception as e:
            logger.error(f"Unexpected ML service error: {e}")
            raise MLServiceError(f"Unexpected error: {str(e)}")

    async def predict(
        self, price: float, purchases: int, margin: float, description_length: int = 0
    ) -> dict:
        """
        Async prediction - non-blocking.

        Returns:
            dict with keys: category, confidence, recommendations
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/predict",
                    json={
                        "price": price,
                        "purchases": purchases,
                        "margin": margin,
                        "description_length": description_length,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError:
            logger.error(f"Cannot connect to ML service at {self.base_url}")
            raise MLServiceError("ML service is unavailable.")
        except httpx.TimeoutException:
            logger.error("ML service request timed out")
            raise MLServiceError("ML service request timed out.")
        except httpx.HTTPStatusError as e:
            logger.error(f"ML service returned error: {e.response.status_code}")
            raise MLServiceError(f"ML service error: {e.response.text}")

    def batch_predict_sync(self, items: list[dict]) -> list[dict]:
        """
        Batch prediction for multiple items (synchronous).

        Args:
            items: List of dicts with price, purchases, margin, description_length

        Returns:
            List of prediction results
        """
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/batch-predict", json={"items": items}
                )
                response.raise_for_status()
                return response.json()["predictions"]
        except Exception as e:
            logger.error(f"Batch prediction error: {e}")
            raise MLServiceError(f"Batch prediction failed: {str(e)}")

    def health_check(self) -> dict:
        """Check if ML service is healthy"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except Exception:
            return {
                "status": "unhealthy",
                "model_loaded": False,
                "encoder_loaded": False,
            }


# Singleton instance for convenience
ml_service = MLService()

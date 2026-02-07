"""
File: services.py
Authors: Hamdy El-Madbouly, Alaa Amer
Description: Service layer for integrating with the external ML service.
This module handles the HTTP communication with the FastAPI ML microservice, including
error handling, timeout management, and response parsing for AI features like
description enhancement and sales suggestions.

This service handles AI-powered features only:
- Description enhancement
- Sales suggestions
- Menu structure analysis
- Customer recommendations
- Owner reports

Note: Menu item classification (Star/Plowhorse/Puzzle/Dog) is now handled
locally by the menu_classifier module using the Menu Engineering Matrix algorithm.
"""

from .models import MenuItem

import httpx
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MLServiceError(Exception):
    """Custom exception for ML service errors"""

    pass


class MLService:
    """
    Client for the FastAPI ML service (AI features only).

    Usage:
        ml_service = MLService()
        result = ml_service.enhance_description_sync(item_name="Burger", ...)
        result = ml_service.sales_suggestions_sync(item_name="Burger", ...)
    """

    def __init__(self):
        self.base_url = getattr(settings, "ML_SERVICE_URL", "http://ml_service:8001")
        self.timeout = 10.0  # seconds
        self.ai_timeout = 60.0  # longer timeout for AI calls

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
                "ai_enabled": False,
            }

    # ============ AI-Powered Endpoints ============

    def enhance_description_sync(
        self,
        item_name: str,
        current_description: str = "",
        category: str = "Unknown",
        price: float = 0.0,
        cuisine_type: str = "restaurant",
    ) -> dict:
        """
        Use AI to enhance a menu item description.

        Returns:
            dict with enhanced_description, key_selling_points, tips
        """
        try:
            with httpx.Client(timeout=self.ai_timeout) as client:
                response = client.post(
                    f"{self.base_url}/enhance-description",
                    json={
                        "item_name": item_name,
                        "current_description": current_description,
                        "category": category,
                        "price": price,
                        "cuisine_type": cuisine_type,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise MLServiceError("AI service not available. Please try later.")
            raise MLServiceError(f"AI service error: {e.response.text}")
        except Exception as e:
            logger.error(f"Enhance description error: {e}")
            raise MLServiceError(f"Failed to enhance description: {str(e)}")

    def get_sales_suggestions_sync(
        self,
        item_name: str,
        category: str,
        price: float,
        cost: float,
        purchases: int,
        section_avg_price: float = None,
        section_avg_sales: float = None,
    ) -> dict:
        """
        Get AI-powered sales suggestions for a menu item.

        Returns:
            dict with priority, suggested_price, immediate_actions, marketing_tips, etc.
        """
        try:
            with httpx.Client(timeout=self.ai_timeout) as client:
                response = client.post(
                    f"{self.base_url}/sales-suggestions",
                    json={
                        "item_name": item_name,
                        "category": category,
                        "price": price,
                        "cost": cost,
                        "purchases": purchases,
                        "section_avg_price": section_avg_price,
                        "section_avg_sales": section_avg_sales,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise MLServiceError("AI service not available.")
            raise MLServiceError(f"AI service error: {e.response.text}")
        except Exception as e:
            logger.error(f"Sales suggestions error: {e}")
            raise MLServiceError(f"Failed to get sales suggestions: {str(e)}")

    def analyze_menu_structure_sync(self, sections: list[dict]) -> dict:
        """
        Analyze menu structure and get optimization recommendations.

        Args:
            sections: List of menu sections with their items

        Returns:
            dict with overall_score, section_order_recommendation, general_recommendations, etc.
        """
        try:
            with httpx.Client(timeout=self.ai_timeout) as client:
                response = client.post(
                    f"{self.base_url}/menu-structure",
                    json={"sections": sections},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise MLServiceError("AI service not available.")
            raise MLServiceError(f"AI service error: {e.response.text}")
        except Exception as e:
            logger.error(f"Menu structure analysis error: {e}")
            raise MLServiceError(f"Failed to analyze menu structure: {str(e)}")

    def get_customer_recommendations_sync(
        self,
        current_items: list[str],
        menu_items: list[dict],
        budget_remaining: float = None,
        preferences: list[str] = None,
    ) -> dict:
        """
        Get personalized item recommendations for a customer.

        Returns:
            dict with top_recommendation, alternatives, upsells
        """
        try:
            with httpx.Client(timeout=self.ai_timeout) as client:
                response = client.post(
                    f"{self.base_url}/customer-recommendations",
                    json={
                        "current_items": current_items,
                        "menu_items": menu_items,
                        "budget_remaining": budget_remaining,
                        "preferences": preferences,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise MLServiceError("AI service not available.")
            raise MLServiceError(f"AI service error: {e.response.text}")
        except Exception as e:
            logger.error(f"Customer recommendations error: {e}")
            raise MLServiceError(f"Failed to get recommendations: {str(e)}")

    def generate_owner_report_sync(
        self, summary_data: dict, period: str = "weekly"
    ) -> dict:
        """
        Generate an AI-powered insights report for owners.

        Args:
            summary_data: Sales data, category breakdown, etc.
            period: "daily", "weekly", or "monthly"

        Returns:
            dict with executive_summary, highlights, concerns, recommendations, etc.
        """
        try:
            with httpx.Client(timeout=self.ai_timeout) as client:
                response = client.post(
                    f"{self.base_url}/generate-report",
                    json={
                        "summary_data": summary_data,
                        "period": period,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise MLServiceError("AI service not available.")
            raise MLServiceError(f"AI service error: {e.response.text}")
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            raise MLServiceError(f"Failed to generate report: {str(e)}")


# Singleton instance for convenience
ml_service = MLService()

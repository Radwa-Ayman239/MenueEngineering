"""
File: main.py
Authors: Hamdy El-Madbouly
Description: Main entry point for the FastAPI Machine Learning service.
This microservice handles all AI-powered operations (OpenRouter/DeepSeek integration)
separate from the main Django backend. It provides endpoints for description enhancement,
sales suggestions, menu analysis, and owner reports.

Note: Menu item classification (Star/Plowhorse/Puzzle/Dog) is handled
locally by the Django backend's menu_classifier module.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional

# Import OpenRouter AI service
try:
    try:
        from .openrouter_service import (
            enhance_description,
            analyze_menu_structure,
            generate_sales_suggestions,
            get_customer_recommendations,
            generate_owner_report,
            is_gemini_available,
        )
    except (ImportError, ValueError):
        from openrouter_service import (
            enhance_description,
            analyze_menu_structure,
            generate_sales_suggestions,
            get_customer_recommendations,
            generate_owner_report,
            is_gemini_available,
        )
    AI_ENABLED = True
except Exception as e:
    import traceback

    print("CRITICAL: Failed to import AI services")
    traceback.print_exc()
    AI_ENABLED = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    if AI_ENABLED and is_gemini_available():
        print("✓ AI service enabled (OpenRouter/DeepSeek)")
    else:
        print("⚠ AI service not available - check OPENROUTER_API_KEY")

    yield  # App runs here

    print("Shutting down ML service...")


app = FastAPI(
    title="Menu Engineering AI API",
    description="AI service for menu description enhancement, recommendations, and intelligent insights",
    version="3.0.0",
    lifespan=lifespan,
)


# ============ Request/Response Models ============


class EnhanceDescriptionRequest(BaseModel):
    item_name: str
    current_description: str = ""
    category: str = "Unknown"
    price: float = 0.0
    cuisine_type: str = "restaurant"
    # Customization options
    custom_instructions: Optional[str] = None
    tone: str = "professional"  # professional, casual, playful, elegant
    include_allergens: bool = False
    target_audience: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "item_name": "Grilled Chicken",
                "current_description": "Chicken with vegetables",
                "category": "Puzzle",
                "price": 18.99,
                "cuisine_type": "American",
                "custom_instructions": "Emphasize the farm-to-table sourcing",
                "tone": "elegant",
                "include_allergens": True,
            }
        }


class MenuStructureRequest(BaseModel):
    sections: list[dict]
    custom_instructions: Optional[str] = None
    focus_areas: Optional[list[str]] = None  # ["pricing", "layout", "naming"]

    class Config:
        json_schema_extra = {
            "example": {
                "sections": [
                    {
                        "name": "Appetizers",
                        "items": [
                            {"name": "Wings", "price": 12.99, "category": "Star"}
                        ],
                    }
                ],
                "focus_areas": ["pricing", "layout"],
                "custom_instructions": "Focus on upselling opportunities",
            }
        }


class SalesSuggestionsRequest(BaseModel):
    item_name: str
    category: str
    price: float
    cost: float
    purchases: int
    section_avg_price: Optional[float] = None
    section_avg_sales: Optional[float] = None
    custom_instructions: Optional[str] = None
    strategy: str = "balanced"  # aggressive, balanced, conservative


class CustomerRecommendationsRequest(BaseModel):
    current_items: list[str] = []
    menu_items: list[dict]
    budget_remaining: Optional[float] = None
    preferences: Optional[list[str]] = None
    custom_instructions: Optional[str] = None
    upsell_aggressiveness: str = "medium"  # low, medium, high


class OwnerReportRequest(BaseModel):
    summary_data: dict
    period: str = "weekly"
    custom_instructions: Optional[str] = None
    report_style: str = "executive"  # executive, detailed


# ============ AI Endpoints ============


@app.post("/enhance-description")
async def api_enhance_description(request: EnhanceDescriptionRequest):
    """Use AI to enhance a menu item description to be more appetizing"""
    if not AI_ENABLED:
        raise HTTPException(status_code=503, detail="AI service not available")

    try:
        result = await enhance_description(
            item_name=request.item_name,
            current_description=request.current_description,
            category=request.category,
            price=request.price,
            cuisine_type=request.cuisine_type,
            custom_instructions=request.custom_instructions,
            tone=request.tone,
            include_allergens=request.include_allergens,
            target_audience=request.target_audience,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/menu-structure")
async def api_analyze_menu_structure(request: MenuStructureRequest):
    """Analyze menu structure and suggest optimal layout"""
    if not AI_ENABLED:
        raise HTTPException(status_code=503, detail="AI service not available")

    try:
        result = await analyze_menu_structure(
            menu_sections=request.sections,
            custom_instructions=request.custom_instructions,
            focus_areas=request.focus_areas,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sales-suggestions")
async def api_sales_suggestions(request: SalesSuggestionsRequest):
    """Generate AI-powered sales suggestions for a menu item"""
    if not AI_ENABLED:
        raise HTTPException(status_code=503, detail="AI service not available")

    try:
        result = await generate_sales_suggestions(
            item_name=request.item_name,
            category=request.category,
            price=request.price,
            cost=request.cost,
            purchases=request.purchases,
            section_avg_price=request.section_avg_price,
            section_avg_sales=request.section_avg_sales,
            custom_instructions=request.custom_instructions,
            strategy=request.strategy,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/customer-recommendations")
async def api_customer_recommendations(request: CustomerRecommendationsRequest):
    """Get personalized item recommendations for customers"""
    if not AI_ENABLED:
        raise HTTPException(status_code=503, detail="AI service not available")

    try:
        result = await get_customer_recommendations(
            current_items=request.current_items,
            menu_items=request.menu_items,
            budget_remaining=request.budget_remaining,
            preferences=request.preferences,
            custom_instructions=request.custom_instructions,
            upsell_aggressiveness=request.upsell_aggressiveness,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-report")
async def api_generate_report(request: OwnerReportRequest):
    """Generate AI-powered insights report for restaurant owners"""
    if not AI_ENABLED:
        raise HTTPException(status_code=503, detail="AI service not available")

    try:
        result = await generate_owner_report(
            summary_data=request.summary_data,
            period=request.period,
            custom_instructions=request.custom_instructions,
            report_style=request.report_style,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Health & Info Endpoints ============


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Core service is healthy if AI_ENABLED is True (imports passed)
    is_healthy = AI_ENABLED

    # Live AI check (requires API key)
    live_ai_available = AI_ENABLED and is_gemini_available() if AI_ENABLED else False

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "mock_mode": AI_ENABLED and not live_ai_available,
        "ai_enabled": live_ai_available,
        "details": (
            "Running with mock data"
            if AI_ENABLED and not live_ai_available
            else "Full AI enabled" if live_ai_available else "Service degraded"
        ),
    }


@app.get("/")
async def root():
    """API information endpoint"""
    return {
        "service": "Menu Engineering AI API",
        "version": "3.0.0",
        "description": "AI-powered menu engineering features",
        "endpoints": [
            "POST /enhance-description - Enhance menu item descriptions with AI",
            "POST /sales-suggestions - Get AI sales improvement suggestions",
            "POST /menu-structure - Analyze menu structure with AI",
            "POST /customer-recommendations - Get personalized recommendations",
            "POST /generate-report - Generate AI owner reports",
            "GET /health - Service health check",
        ],
    }

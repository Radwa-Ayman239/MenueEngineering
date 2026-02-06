from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import joblib
import numpy as np
from pathlib import Path

# Global variables for models
classifier = None
label_encoder = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on startup, cleanup on shutdown"""
    global classifier, label_encoder

    models_path = Path("models")
    classifier_path = models_path / "menu_classifier.joblib"
    encoder_path = models_path / "label_encoder.joblib"

    if classifier_path.exists():
        classifier = joblib.load(classifier_path)
        print("✓ Classifier loaded")
    else:
        print("⚠ Classifier not found - predictions will fail")

    if encoder_path.exists():
        label_encoder = joblib.load(encoder_path)
        print("✓ Label encoder loaded")

    yield  # App runs here

    # Cleanup (if needed)
    print("Shutting down ML service...")


app = FastAPI(
    title="Menu Engineering ML API",
    description="AI service for menu item classification and recommendations",
    version="1.0.0",
    lifespan=lifespan,
)


# ============ Request/Response Models ============


class MenuItemPrediction(BaseModel):
    price: float
    purchases: int
    margin: float
    description_length: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "price": 129.0,
                "purchases": 50,
                "margin": 77.4,
                "description_length": 45,
            }
        }


class PredictionResponse(BaseModel):
    category: str  # Star, Plowhorse, Puzzle, Dog
    confidence: float
    recommendations: list[str]


class BatchPredictionRequest(BaseModel):
    items: list[MenuItemPrediction]


class BatchPredictionResponse(BaseModel):
    predictions: list[dict]


# ============ Recommendation Logic ============


def generate_recommendations(item: MenuItemPrediction, category: str) -> list[str]:
    """Generate actionable recommendations based on category"""
    recommendations = []

    if category == "Dog":
        recommendations.append("Consider removing or rebranding this item")
        recommendations.append(f"Test a 10-15% price reduction to gauge demand")
        recommendations.append("Move to less prominent menu position")
        if item.description_length < 30:
            recommendations.append("If keeping, add an appealing description")

    elif category == "Plowhorse":
        # High popularity, low profit
        recommendations.append(
            "Increase price by 5% (popular items tolerate increases)"
        )
        recommendations.append("Add premium add-ons to increase margin")
        recommendations.append(
            "Reduce portion size slightly while maintaining perceived value"
        )
        recommendations.append("Review supplier costs for cost reduction opportunities")

    elif category == "Puzzle":
        # Low popularity, high profit
        recommendations.append("Move to a more prominent menu position")
        recommendations.append("Train staff to recommend this item")
        recommendations.append("Add to popular bundle combinations")
        if item.description_length < 50:
            recommendations.append("Enhance description with sensory/appetizing words")
        recommendations.append("Consider a limited-time promotion to boost awareness")

    elif category == "Star":
        # High popularity, high profit - protect these!
        recommendations.append("Maintain current pricing and positioning")
        recommendations.append("Feature prominently on menu")
        recommendations.append("Use as anchor for bundle deals")
        recommendations.append("Monitor competitor pricing for similar items")

    return recommendations


# ============ API Endpoints ============


@app.post("/predict", response_model=PredictionResponse)
async def predict_category(item: MenuItemPrediction):
    """Predict menu engineering category for a single item"""
    if classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please ensure model files exist in /models directory.",
        )

    features = np.array([[item.price, item.purchases, item.margin]])

    # Get prediction
    category_encoded = classifier.predict(features)[0]

    # Decode category name if we have the encoder
    if label_encoder is not None:
        category = label_encoder.inverse_transform([category_encoded])[0]
    else:
        # Fallback mapping if encoder not available
        category_map = {0: "Dog", 1: "Plowhorse", 2: "Puzzle", 3: "Star"}
        category = category_map.get(category_encoded, str(category_encoded))

    # Get confidence
    probabilities = classifier.predict_proba(features)[0]
    confidence = float(max(probabilities))

    # Generate recommendations
    recommendations = generate_recommendations(item, category)

    return PredictionResponse(
        category=category, confidence=confidence, recommendations=recommendations
    )


@app.post("/batch-predict", response_model=BatchPredictionResponse)
async def batch_predict(request: BatchPredictionRequest):
    """Predict categories for multiple items at once"""
    if classifier is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    features = np.array(
        [[item.price, item.purchases, item.margin] for item in request.items]
    )

    categories_encoded = classifier.predict(features)
    probabilities = classifier.predict_proba(features)

    predictions = []
    for i, item in enumerate(request.items):
        if label_encoder is not None:
            category = label_encoder.inverse_transform([categories_encoded[i]])[0]
        else:
            category_map = {0: "Dog", 1: "Plowhorse", 2: "Puzzle", 3: "Star"}
            category = category_map.get(
                categories_encoded[i], str(categories_encoded[i])
            )

        predictions.append(
            {
                "category": category,
                "confidence": float(max(probabilities[i])),
                "recommendations": generate_recommendations(item, category),
            }
        )

    return BatchPredictionResponse(predictions=predictions)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": classifier is not None,
        "encoder_loaded": label_encoder is not None,
    }


@app.get("/")
async def root():
    """API root - basic info"""
    return {
        "service": "Menu Engineering ML API",
        "version": "1.0.0",
        "endpoints": {
            "POST /predict": "Predict category for single item",
            "POST /batch-predict": "Predict categories for multiple items",
            "GET /health": "Health check",
        },
    }

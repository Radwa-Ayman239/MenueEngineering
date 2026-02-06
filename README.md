# Menu Engineering AI Platform

A comprehensive menu engineering platform for restaurants that uses AI/ML models to predict the best possible menu design (layout, bundling, descriptions) to maximize profit.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [Questions & Answers](#questions--answers)
   - [1. Model Improvements](#1-what-can-we-improve-about-the-model-how-why)
   - [2. What's Missing](#2-what-are-we-missing)
   - [3. FastAPI Integration](#3-how-can-the-backend-communicate-with-the-model-fastapi)
   - [4. Latency Considerations](#4-latency-considerations-for-frontend-backend-communication)
   - [5. Things to Be Aware Of](#5-things-to-be-aware-of)
   - [6. Additional Recommendations](#6-additional-recommendations)
4. [Step-by-Step Development Approach](#step-by-step-development-approach)
5. [Architecture Diagram](#architecture-diagram)

---

## Project Overview

**Goal**: Build a platform that uses AI to optimize restaurant menus by:
- Classifying menu items (Star, Plowhorse, Puzzle, Dog)
- Analyzing product bundles and add-on associations
- Suggesting improvements for underperforming items
- Tracking customer activity for dynamic model updates

**Current State**:
- **Backend**: Django REST Framework with Knox authentication, PostgreSQL, Redis/Celery
- **ML Notebooks**: Decision Tree classifier + Association Rules (Apriori algorithm)
- **Data Analysis**: Customer behavior analysis with menu engineering labels
- **Frontend**: Empty (placeholder only)

---

## Current Architecture Analysis

### ML Model (`desion_tree_model.ipynb`)
```
Current Implementation:
├── Decision Tree Classifier (sklearn)
├── Features: price, purchases, margin
├── Labels: Star, Plowhorse, Puzzle, Dog
└── Performance: 100% accuracy (OVERFITTING!)
```

### Data Analysis
```
Analysis Code:
├── Menu Engineering Categories (Star/Plowhorse/Puzzle/Dog)
├── Association Rules (mlxtend Apriori) for add-on recommendations
├── Description length analysis (correlation with sales)
└── What-if scenarios for Plowhorses (price/cost adjustments)
```

### Backend (`backend/`)
```
Django REST Framework:
├── User Management (Admin, Manager, Staff)
├── 2FA Authentication (SMS OTP)
├── Knox Token Authentication
├── PostgreSQL Database
└── Redis + Celery (async tasks)
```

---

## Questions & Answers

### 1. What can we improve about the model? How? Why?

#### Current Problems

| Issue | Impact | Root Cause |
|-------|--------|------------|
| **100% Accuracy** | Overfitting - model won't generalize | Labels are derived FROM the same features used for training |
| **Simple Features** | Missing key business drivers | Only using price, purchases, margin |
| **No Time Dimension** | Can't detect trends | No temporal features like seasonality, day of week |
| **Static Model** | Can't adapt to changes | No retraining pipeline |

#### Recommended Improvements

**A. Feature Engineering (HIGH PRIORITY)**
```python
# Add these features to improve prediction:
new_features = {
    "description_length": "Length of product description",
    "description_sentiment": "NLP sentiment score of description",
    "category_position": "Position in menu section (1st, 2nd, etc.)",
    "price_relative": "Price compared to category average",
    "addon_count": "Number of available add-ons",
    "bundle_frequency": "How often item appears in bundles",
    "time_features": ["hour_of_day", "day_of_week", "month"],
    "customer_rating": "Average rating from votes",
}
```

**B. Better Model Architecture**
```python
# Replace Decision Tree with ensemble methods:
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier

# For profit prediction (regression):
from sklearn.ensemble import RandomForestRegressor
```

**C. Separate Prediction from Classification**
```python
# Current: Classify items into categories
# Better: Predict ACTUAL outcomes

# Model 1: Predict sales volume
y_sales = historical_sales_data

# Model 2: Predict profit margin
y_profit = historical_profit_data

# Then classify based on predictions, not current values
```

**D. Add External Features**
- Weather data (correlates with food preferences)
- Local events (sports games, holidays)
- Competitor pricing (if available)

---

### 2. What are we missing?

#### Missing Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| **ML Service** | API to serve model predictions | 🔴 Critical |
| **Product/Menu Models** | Database models for menu items | 🔴 Critical |
| **Order Models** | Track customer orders | 🔴 Critical |
| **Activity Tracking** | Log customer page events | 🟡 High |
| **Model Retraining Pipeline** | Update model with new data | 🟡 High |
| **Recommendation Engine** | Generate actionable suggestions | 🟡 High |
| **A/B Testing Framework** | Test menu changes | 🟢 Medium |
| **Dashboard/Analytics** | Visualize insights | 🟢 Medium |

#### Database Models Needed

```python
# backend/menu/models.py (NEW FILE)

class MenuItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    section = models.ForeignKey('MenuSection', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # AI-generated fields
    category = models.CharField(choices=CATEGORY_CHOICES)  # Star/Plowhorse/etc
    ai_confidence = models.FloatField(null=True)
    last_analyzed = models.DateTimeField(null=True)

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField()
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)

class CustomerActivity(models.Model):
    """Track customer interactions for ML model updates"""
    session_id = models.CharField(max_length=255)
    event_type = models.CharField(max_length=50)  # view, click, add_to_cart, purchase
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)  # Additional event data
```

---

### 3. How can the backend communicate with the model? (FastAPI)

#### What is FastAPI?

FastAPI is a modern, high-performance Python web framework designed for building APIs. It's ideal for ML model serving because:

| Feature | Benefit |
|---------|---------|
| **Async Support** | Handle many concurrent requests |
| **Automatic Validation** | Pydantic models validate input/output |
| **Auto Documentation** | Swagger UI out of the box |
| **Type Hints** | Better IDE support, fewer bugs |
| **Performance** | One of the fastest Python frameworks |

#### Architecture: Django + FastAPI

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│  Django Backend │────▶│   FastAPI ML    │
│   (React/Next)  │     │   (REST API)    │     │   Service       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────┐          ┌─────────────┐
                        │  PostgreSQL │          │ ML Models   │
                        │   Database  │          │ (joblib/pkl)│
                        └─────────────┘          └─────────────┘
```

#### FastAPI ML Service Implementation

**1. Create new service: `ml_service/`**

```python
# ml_service/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI(title="Menu Engineering ML API")

# Load models on startup
@app.on_event("startup")
async def load_models():
    global classifier, recommender
    classifier = joblib.load("models/menu_classifier.joblib")
    recommender = joblib.load("models/association_rules.joblib")

# Request/Response Models
class MenuItemPrediction(BaseModel):
    price: float
    purchases: int
    margin: float
    description_length: int = 0

class PredictionResponse(BaseModel):
    category: str  # Star, Plowhorse, Puzzle, Dog
    confidence: float
    recommendations: list[str]

# Endpoints
@app.post("/predict", response_model=PredictionResponse)
async def predict_category(item: MenuItemPrediction):
    features = np.array([[item.price, item.purchases, item.margin]])
    category = classifier.predict(features)[0]
    confidence = max(classifier.predict_proba(features)[0])
    
    recommendations = generate_recommendations(item, category)
    
    return PredictionResponse(
        category=category,
        confidence=float(confidence),
        recommendations=recommendations
    )

@app.post("/batch-predict")
async def batch_predict(items: list[MenuItemPrediction]):
    """Predict categories for multiple items at once"""
    features = np.array([
        [i.price, i.purchases, i.margin] for i in items
    ])
    categories = classifier.predict(features)
    return {"categories": categories.tolist()}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": classifier is not None}
```

**2. Add to docker-compose.yml**

```yaml
services:
  # ... existing services ...
  
  ml_service:
    build: ./ml_service
    container_name: menu_engineering_ml
    ports:
      - "8001:8001"
    volumes:
      - ./ml_service:/app
      - ./models:/app/models
    command: uvicorn main:app --host 0.0.0.0 --port 8001 --reload
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**3. Django Backend Integration**

```python
# backend/menu/services.py
import httpx
from django.conf import settings

class MLService:
    def __init__(self):
        self.base_url = settings.ML_SERVICE_URL  # "http://ml_service:8001"
    
    async def predict_category(self, item_data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/predict",
                json=item_data,
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
    
    async def batch_predict(self, items: list[dict]) -> list[str]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/batch-predict",
                json=items,
                timeout=30.0
            )
            return response.json()["categories"]
```

---

### 4. Latency Considerations for Frontend-Backend Communication

#### Expected Latency Sources

| Source | Typical Latency | Impact |
|--------|----------------|--------|
| Network (LAN) | 1-5ms | Minimal |
| Django Processing | 10-50ms | Low |
| Database Query | 5-100ms | Medium |
| ML Prediction | 50-500ms | High |
| External APIs | 100-2000ms | Very High |

#### Strategies to Handle Latency

**A. Asynchronous Operations**

```python
# Use Celery for long-running ML tasks
from celery import shared_task

@shared_task
def analyze_menu_items():
    """Background task to re-analyze all menu items"""
    items = MenuItem.objects.filter(needs_analysis=True)
    for item in items:
        prediction = ml_service.predict_category(item.to_dict())
        item.category = prediction["category"]
        item.ai_confidence = prediction["confidence"]
        item.save()
```

**B. Caching Predictions**

```python
# Cache ML predictions in Redis
from django.core.cache import cache

def get_item_prediction(item_id):
    cache_key = f"prediction:{item_id}"
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    prediction = ml_service.predict_category(item.to_dict())
    cache.set(cache_key, prediction, timeout=3600)  # 1 hour
    return prediction
```

**C. Frontend Optimistic Updates**

```javascript
// React example - show loading state
const [prediction, setPrediction] = useState(null);
const [loading, setLoading] = useState(false);

const analyzeMeni = async (itemId) => {
  setLoading(true);
  try {
    const response = await api.analyzeMenuItem(itemId);
    setPrediction(response.data);
  } catch (error) {
    showError("Analysis failed. Retrying...");
    // Implement retry logic
  } finally {
    setLoading(false);
  }
};
```

**D. API Design for Latency**

```python
# Provide both sync and async endpoints
class MenuItemViewSet(viewsets.ModelViewSet):
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Synchronous - wait for result"""
        item = self.get_object()
        prediction = ml_service.predict_sync(item)
        return Response(prediction)
    
    @action(detail=True, methods=['post'])
    def analyze_async(self, request, pk=None):
        """Asynchronous - return task ID"""
        item = self.get_object()
        task = analyze_item_task.delay(item.id)
        return Response({"task_id": task.id, "status": "pending"})
    
    @action(detail=False, methods=['get'])
    def task_status(self, request):
        """Check async task status"""
        task_id = request.query_params.get('task_id')
        result = AsyncResult(task_id)
        return Response({
            "status": result.status,
            "result": result.result if result.ready() else None
        })
```

**E. WebSockets for Real-time Updates**

```python
# For real-time activity tracking
# Use Django Channels

# consumers.py
class ActivityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        # Log activity
        await self.channel_layer.send_activity(data)
```

---

### 5. Things to Be Aware Of

#### Technical Considerations

| Area | Issue | Mitigation |
|------|-------|------------|
| **Model Drift** | Predictions degrade over time | Schedule regular retraining |
| **Data Privacy** | Customer behavior tracking | GDPR compliance, anonymization |
| **Service Availability** | ML service downtime | Fallback to cached predictions |
| **Scalability** | Many concurrent predictions | Load balancing, model replicas |
| **Security** | API exposed to attacks | Rate limiting, input validation |

#### Business Considerations

- **Cold Start Problem**: New items have no purchase history
  - *Solution*: Use similar item features for initial classification
  
- **Feedback Loop**: Acting on predictions changes behavior
  - *Solution*: Track both predictions and outcomes
  
- **Human Override**: Staff may disagree with AI
  - *Solution*: Allow manual category override, log for training

#### Code Quality

```python
# NEVER do this in production:
df = pd.read_csv("https://github.com/...")  # Notebook-style URLs

# DO this instead:
class MenuDataRepository:
    def get_menu_items(self) -> QuerySet:
        return MenuItem.objects.filter(is_active=True)
    
    def get_items_for_training(self) -> pd.DataFrame:
        items = self.get_menu_items().values(...)
        return pd.DataFrame(items)
```

---

### 6. Additional Recommendations

#### A. Model Versioning & MLOps

```yaml
# Use MLflow or similar for model tracking
ml_service:
  model_registry: "mlflow://models/menu_classifier"
  model_version: "production"
  fallback_version: "v1.2.0"
```

#### B. A/B Testing Framework

```python
class ABTest(models.Model):
    name = models.CharField(max_length=255)
    description_variant_a = models.TextField()
    description_variant_b = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    winner = models.CharField(null=True)  # Set when test concludes
```

#### C. Recommendation Engine

```python
# Generate actionable recommendations
def generate_recommendations(item, category):
    recommendations = []
    
    if category == "Dog":
        recommendations.append("Consider removing or rebranding this item")
        recommendations.append(f"Reduce price by 10-15% to test demand")
    
    elif category == "Plowhorse":
        recommendations.append("Increase price by 5% (what-if: +$X profit)")
        recommendations.append("Add premium add-ons to increase margin")
    
    elif category == "Puzzle":
        recommendations.append("Move to prominent menu position")
        recommendations.append("Add to popular bundle combinations")
        recommendations.append("Enhance description with sensory words")
    
    return recommendations
```

#### D. Monitoring & Alerts

```python
# backend/menu/monitoring.py
from prometheus_client import Counter, Histogram

ml_predictions = Counter('ml_predictions_total', 'Total ML predictions', ['category'])
ml_latency = Histogram('ml_prediction_seconds', 'ML prediction latency')

def track_prediction(category, latency):
    ml_predictions.labels(category=category).inc()
    ml_latency.observe(latency)
```

---

## Step-by-Step Development Approach

### Phase 1: Foundation (Week 1-2)
- [ ] Create Django models for `MenuItem`, `MenuSection`, `Order`, `OrderItem`
- [ ] Create migrations and admin interface
- [ ] Set up basic CRUD API endpoints for menu management
- [ ] Import existing CSV data into database

### Phase 2: ML Service (Week 2-3)
- [ ] Create FastAPI service structure
- [ ] Export trained model from notebook to `.joblib`
- [ ] Implement prediction endpoints
- [ ] Add to docker-compose
- [ ] Create Django client for ML service

### Phase 3: Integration (Week 3-4)
- [ ] Connect Django backend to FastAPI ML service
- [ ] Implement caching layer for predictions
- [ ] Add async analysis via Celery
- [ ] Create API endpoints for frontend

### Phase 4: Activity Tracking (Week 4-5)
- [ ] Create `CustomerActivity` model
- [ ] Implement activity logging endpoints
- [ ] Create data pipeline for model updates
- [ ] Set up scheduled retraining

### Phase 5: Frontend (Week 5-7)
- [ ] Set up React/Next.js project
- [ ] Create menu management dashboard
- [ ] Implement order entry interface
- [ ] Build analytics visualizations
- [ ] Add real-time updates (WebSocket)

### Phase 6: Advanced Features (Week 7-8)
- [ ] Implement A/B testing framework
- [ ] Add recommendation engine
- [ ] Create automated reports
- [ ] Set up monitoring and alerts

---

## Architecture Diagram

```
                                    ┌─────────────────────────────────────────┐
                                    │              Frontend                    │
                                    │         (React/Next.js)                  │
                                    │  ┌─────────┐ ┌─────────┐ ┌─────────┐    │
                                    │  │Dashboard│ │Orders   │ │Analytics│    │
                                    │  └─────────┘ └─────────┘ └─────────┘    │
                                    └───────────────────┬─────────────────────┘
                                                        │ REST/WebSocket
                                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                              Nginx (Reverse Proxy)                             │
└───────────────────────────────────────────────────────────────────────────────┘
           │                              │                          │
           ▼                              ▼                          ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────┐
│    Django Backend       │   │    FastAPI ML Service   │   │  Static Files   │
│    (REST API)           │   │    (Model Serving)      │   │  (WhiteNoise)   │
│  ┌───────────────────┐  │   │  ┌─────────────────┐   │   └─────────────────┘
│  │ Menu Management   │  │   │  │ /predict        │   │
│  │ Order Management  │◀─┼───┼─▶│ /batch-predict  │   │
│  │ User Auth (2FA)   │  │   │  │ /retrain        │   │
│  │ Activity Tracking │  │   │  └─────────────────┘   │
│  └───────────────────┘  │   │          │             │
└───────────┬─────────────┘   └──────────┼─────────────┘
            │                            │
            │    ┌───────────────────────┘
            │    │
            ▼    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Data Layer                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   PostgreSQL    │  │     Redis       │  │     ML Models               │  │
│  │   (Primary DB)  │  │  (Cache/Queue)  │  │   (joblib/pickle)           │  │
│  │                 │  │                 │  │   - menu_classifier.joblib  │  │
│  │  - menu_items   │  │  - predictions  │  │   - association_rules.pkl   │  │
│  │  - orders       │  │  - sessions     │  │                             │  │
│  │  - activities   │  │  - celery tasks │  │                             │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Background Tasks (Celery)                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ Model Retraining│  │ Report Gen      │  │ Activity Processing         │  │
│  │ (scheduled)     │  │ (on-demand)     │  │ (real-time/batch)           │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd MenueEngineering

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Create admin user
docker-compose exec backend python manage.py createsuperuser

# Access services:
# - Backend API: http://localhost:8000
# - ML Service: http://localhost:8001 (after implementation)
# - Admin Panel: http://localhost:8000/admin
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React/Next.js | User interface |
| Backend | Django REST Framework | Business logic, API |
| ML Service | FastAPI | Model serving |
| Database | PostgreSQL | Primary data store |
| Cache | Redis | Predictions, sessions |
| Queue | Celery | Background tasks |
| Container | Docker Compose | Deployment |
| ML | scikit-learn, XGBoost | Model training |

---

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -m "Add your feature"`
3. Push to branch: `git push origin feature/your-feature`
4. Open Pull Request

---

## License

[Add your license here]
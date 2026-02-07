# System Architecture - Menu Engineering Platform

## Overview

This document describes the architecture of the automated menu system with AI-powered recommendations for restaurants.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│                                                                   │
│  ┌────────────────────┐         ┌────────────────────┐          │
│  │  Customer Interface│         │ Manager Dashboard  │          │
│  │  • Browse Menu     │         │ • View Analytics   │          │
│  │  • Get Suggestions │         │ • AI Suggestions   │          │
│  │  • Shopping Cart   │         │ • Accept/Reject    │          │
│  │  • FBT Items       │         │ • Bulk Analysis    │          │
│  └────────────────────┘         └────────────────────┘          │
│           │                              │                       │
│           └──────────────┬───────────────┘                       │
│                          │                                       │
│                   React Application                              │
│                   • Context API (Cart)                           │
│                   • API Service Layer                            │
│                   • Component-based UI                           │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            │ REST API (JSON)
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Django REST Framework                  │  │
│  │  • ViewSets (CRUD operations)                            │  │
│  │  • Permissions (Public/Staff/Manager)                    │  │
│  │  • Serializers (Data validation)                         │  │
│  │  • Authentication (Knox tokens)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     BUSINESS LOGIC LAYER                         │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Menu Engineering Classifier                 │   │
│  │  • Menu Engineering Matrix Algorithm                     │   │
│  │  • Threshold-based Classification                        │   │
│  │  • Categories: Star, Puzzle, Plowhorse, Dog             │   │
│  │  • Confidence Scoring                                    │   │
│  │  • Batch Processing                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Recommendation Engine                       │   │
│  │  • Market Basket Analysis                                │   │
│  │  • Co-purchase Pattern Detection                         │   │
│  │  • Multi-factor Scoring:                                 │   │
│  │    - Category Score (35%)                                │   │
│  │    - Margin Score (30%)                                  │   │
│  │    - Co-purchase Score (20%)                             │   │
│  │    - Popularity Score (10%)                              │   │
│  │    - Context Score (5%)                                  │   │
│  │  • Strategies: Balanced, Upsell, Cross-sell             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              AI Services (Optional)                      │   │
│  │  • Description Enhancement                               │   │
│  │  • Sales Suggestions                                     │   │
│  │  • Menu Structure Analysis                               │   │
│  │  • Owner Reports                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                       DATA ACCESS LAYER                          │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Django ORM                            │   │
│  │  • Models: MenuItem, MenuSection, Order, OrderItem      │   │
│  │  • Relationships & Constraints                           │   │
│  │  • Query Optimization                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                       DATABASE LAYER                             │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                PostgreSQL / SQLite                       │   │
│  │                                                           │   │
│  │  Tables:                                                 │   │
│  │  • menu_menusection                                      │   │
│  │  • menu_menuitem                                         │   │
│  │  • menu_order                                            │   │
│  │  • menu_orderitem                                        │   │
│  │  • menu_customeractivity                                 │   │
│  │  • users_customuser                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend Components

#### Customer Interface
- **CustomerMenu.js**: Main menu display with sections and items
- **Cart.js**: Shopping cart management
- **CartContext.js**: Global cart state management

#### Manager Interface
- **ManagerDashboard.js**: Analytics and AI suggestions dashboard

#### Shared Services
- **api.js**: Centralized API communication layer

### Backend Components

#### API Endpoints

**Public Endpoints** (No Authentication):
```
GET  /api/menu/public/                          → Full menu
GET  /api/menu/sections/                        → Menu sections
GET  /api/menu/items/                           → Menu items list
GET  /api/menu/items/{id}/                      → Item details
GET  /api/menu/recommendations/                 → General recommendations
POST /api/menu/recommendations/for-cart/        → Cart-based recommendations
GET  /api/menu/items/{id}/frequently-together/  → Co-purchase associations
POST /api/menu/activities/                      → Log customer activity
```

**Manager Endpoints** (Authentication Required):
```
POST /api/menu/items/{id}/analyze/              → Analyze single item
POST /api/menu/items/bulk_analyze/              → Analyze all items
GET  /api/menu/items/stats/                     → Category statistics
POST /api/menu/ai/sales-suggestions/            → AI sales suggestions
POST /api/menu/ai/menu-analysis/                → Menu structure analysis
POST /api/menu/ai/owner-report/                 → Owner insights report
```

#### Core Services

**MenuEngineeringClassifier**:
- Implements Menu Engineering Matrix algorithm
- Classifies items into 4 categories based on popularity and profitability
- Provides confidence scores and actionable recommendations

**RecommendationEngine**:
- Market basket analysis using support, confidence, and lift metrics
- Multi-factor scoring system for personalized recommendations
- Three strategies: balanced, upsell, cross-sell

**CoPurchaseAnalyzer**:
- Discovers frequently bought together patterns
- Calculates association rules between items
- Caches results for performance

## Data Models

### MenuItem
```python
{
    id: UUID
    title: String
    description: Text
    price: Decimal
    cost: Decimal
    section: ForeignKey(MenuSection)
    category: Choice(Star, Puzzle, Plowhorse, Dog)
    ai_confidence: Float
    total_purchases: Float
    total_revenue: Decimal
    total_profit: Decimal
    is_active: Boolean
}
```

### Order & OrderItem
```python
Order {
    id: UUID
    created_by: ForeignKey(User)
    status: Choice(pending, confirmed, preparing, ready, completed, cancelled)
    total: Decimal
    created_at: DateTime
}

OrderItem {
    id: UUID
    order: ForeignKey(Order)
    menu_item: ForeignKey(MenuItem)
    quantity: Integer
    price_at_order: Decimal
}
```

### CustomerActivity
```python
{
    id: UUID
    session_id: String
    event_type: Choice(view, click, add_to_cart, remove_from_cart, purchase)
    menu_item: ForeignKey(MenuItem)
    timestamp: DateTime
    metadata: JSON
}
```

## Menu Engineering Matrix

### Classification Logic

```
                    High Profitability
                           │
                           │
        Puzzle (💎)        │        Star (⭐)
    Low Popularity ────────┼──────── High Popularity
        Dog (🐕)           │        Plowhorse (🐴)
                           │
                    Low Profitability
```

### Category Strategies

**⭐ Stars** (High Popularity + High Profit):
- Maintain current pricing and positioning
- Feature prominently on menu
- Use as anchor for bundle deals

**💎 Puzzles** (Low Popularity + High Profit):
- Move to prominent menu position
- Train staff to recommend
- Enhance descriptions
- Limited-time promotions

**🐴 Plowhorses** (High Popularity + Low Profit):
- Increase price by 5-10%
- Add premium add-ons
- Reduce portion size slightly
- Review supplier costs

**🐕 Dogs** (Low Popularity + Low Profit):
- Consider removing or rebranding
- Test price reduction
- Move to less prominent position

## Recommendation Algorithm

### Scoring Formula

```
Final Score = (Category × 0.35) + (Margin × 0.30) + 
              (CoPurchase × 0.20) + (Popularity × 0.10) + 
              (Context × 0.05)
```

### Strategy Adjustments

**Balanced** (Default):
- Equal consideration of all factors
- Best for general recommendations

**Upsell**:
- Margin weight: 45% (increased)
- Category weight: 30%
- Focus on high-profit items

**Cross-sell**:
- Co-purchase weight: 35% (increased)
- Context weight: 10%
- Suggest complementary items

## Data Flow Examples

### Customer Browsing Flow

```
1. Customer opens app
   ↓
2. Frontend: GET /api/menu/public/
   ↓
3. Backend: Query active sections and items
   ↓
4. Frontend: Display menu with category badges
   ↓
5. Customer clicks item
   ↓
6. Frontend: POST /api/menu/activities/ (log view)
   ↓
7. Frontend: GET /api/menu/items/{id}/frequently-together/
   ↓
8. Backend: Run co-purchase analysis
   ↓
9. Frontend: Display item details + FBT suggestions
```

### Cart Recommendation Flow

```
1. Customer adds items to cart
   ↓
2. Cart state updated in React Context
   ↓
3. Frontend: POST /api/menu/recommendations/for-cart/
   Body: { item_ids: [...], strategy: "balanced" }
   ↓
4. Backend: RecommendationEngine.get_recommendations()
   ↓
5. Calculate co-purchase scores for cart items
   ↓
6. Score all candidate items
   ↓
7. Sort by score, return top N
   ↓
8. Frontend: Display recommendations with reasons
```

### Manager Analysis Flow

```
1. Manager clicks "Analyze All Items"
   ↓
2. Frontend: POST /api/menu/items/bulk_analyze/
   ↓
3. Backend: Get all active items
   ↓
4. Calculate batch averages (purchases, margin %)
   ↓
5. MenuEngineeringClassifier.classify_batch()
   ↓
6. For each item:
   - Compare to thresholds
   - Assign category
   - Calculate confidence
   - Generate recommendations
   ↓
7. Update all items in database
   ↓
8. Frontend: Reload dashboard with new classifications
```

## Performance Optimizations

### Caching Strategy

**Affinity Matrix** (15 min cache):
- Co-purchase associations
- Rebuilt when cache expires or on demand

**Frequently Bought Together** (30 min cache):
- Per-item associations
- Invalidated on new orders

**Menu Statistics** (5 min cache):
- Category counts and revenue
- Refreshed frequently for accuracy

### Database Optimization

- Indexes on frequently queried fields (category, is_active)
- Select_related() for foreign keys
- Prefetch_related() for reverse relationships
- Query result caching for expensive operations

## Security Considerations

### Authentication & Authorization

**Public Access**:
- Menu viewing
- Recommendations
- Activity logging

**Staff Access**:
- Order creation
- Order management

**Manager/Admin Access**:
- Menu item CRUD
- AI analysis
- Statistics and reports

### Data Protection

- CSRF protection enabled
- CORS configured for frontend origin
- SQL injection prevention via ORM
- Input validation via serializers
- Rate limiting (recommended for production)

## Scalability Considerations

### Horizontal Scaling

- Stateless API design
- Session data in database/cache
- Load balancer compatible

### Vertical Scaling

- Database connection pooling
- Query optimization
- Async task processing (Celery ready)

### Caching Layer

- Redis for production caching
- Distributed cache support
- Cache invalidation strategies

## Monitoring & Analytics

### Key Metrics

**Customer Metrics**:
- Menu views per session
- Add-to-cart rate
- Recommendation click-through rate
- Average cart value

**Business Metrics**:
- Category distribution
- Revenue by category
- Margin analysis
- Item performance trends

**System Metrics**:
- API response times
- Cache hit rates
- Database query performance
- Error rates

## Future Enhancements

### Planned Features

1. **Real-time Updates**: WebSocket integration for live menu changes
2. **Advanced Analytics**: Time-series analysis, trend prediction
3. **A/B Testing**: Test different recommendation strategies
4. **Image Recognition**: Auto-categorize items from photos
5. **Multi-location**: Support for restaurant chains
6. **Inventory Integration**: Real-time availability
7. **Dynamic Pricing**: Time-based pricing suggestions
8. **Customer Profiles**: Personalized recommendations based on history

### Technical Improvements

1. **GraphQL API**: More efficient data fetching
2. **Microservices**: Separate recommendation service
3. **Machine Learning**: Deep learning for better predictions
4. **Mobile Apps**: Native iOS/Android applications
5. **Offline Support**: PWA with offline capabilities
6. **Internationalization**: Multi-language support

## Deployment Architecture

### Development
```
Frontend: localhost:3000 (React Dev Server)
Backend: localhost:8000 (Django runserver)
Database: SQLite
```

### Production
```
Frontend: CDN (CloudFront, Netlify, Vercel)
Backend: Application Server (Gunicorn + Nginx)
Database: PostgreSQL (RDS, managed service)
Cache: Redis (ElastiCache)
Static Files: S3 or CDN
```

## Technology Stack Summary

### Frontend
- React 19
- Context API
- Fetch API
- CSS3 (Flexbox, Grid)

### Backend
- Django 4.x
- Django REST Framework
- Knox (Authentication)
- PostgreSQL/SQLite

### AI/ML
- Menu Engineering Matrix (Deterministic)
- Market Basket Analysis (Association Rules)
- Optional: OpenAI API for enhanced suggestions

### DevOps
- Git (Version Control)
- Docker (Containerization)
- Docker Compose (Local Development)

---

This architecture provides a solid foundation for a scalable, maintainable menu engineering platform with AI-powered recommendations.

# Complete Setup Guide - Menu Engineering System

This guide will help you set up both the backend (Django) and frontend (React) for the automated menu system.

## System Overview

The system has two main interfaces:

1. **Customer Interface**: Browse menu, get recommendations, add items to cart, see frequently bought together items
2. **Manager Dashboard**: View AI classifications, get sales suggestions, analyze menu performance, accept/reject recommendations

## Prerequisites

- Python 3.8+
- Node.js 14+
- PostgreSQL (or SQLite for development)
- pip and npm

## Backend Setup (Django)

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements/dev.txt
```

### 4. Configure Environment

Create `.env.local` file (already exists, verify settings):

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser (Manager Account)

```bash
python manage.py createsuperuser
```

Follow prompts to create admin account.

### 7. Import Sample Menu Data (Optional)

If you have the CSV file:

```bash
python manage.py import_menu menu_engineering_input_items.csv
```

### 8. Start Development Server

```bash
python manage.py runserver
```

Backend will be available at `http://localhost:8000`

### 9. Test API Endpoints

Visit `http://localhost:8000/api/menu/public/` to see the public menu.

## Frontend Setup (React)

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment

The `.env` file is already created. Verify it contains:

```env
REACT_APP_API_URL=http://localhost:8000/api/menu
```

### 4. Start Development Server

```bash
npm start
```

Frontend will open automatically at `http://localhost:3000`

## Using the System

### Customer View

1. **Browse Menu**: See all menu items organized by sections
2. **View Recommendations**: AI-powered suggestions appear at the top
3. **Click Items**: See details and frequently bought together items
4. **Add to Cart**: Click "Add to Cart" buttons
5. **Manage Cart**: Click "🛒 Cart" button to view and modify cart

### Manager Dashboard

1. **Switch View**: Click "Manager Dashboard" in navigation
2. **View Statistics**: See category breakdown and revenue
3. **Analyze Items**: Click "🔄 Analyze All Items" to run AI classification
4. **Filter by Category**: Use filter buttons to focus on specific categories
5. **View Suggestions**: Click "View Suggestions" on any item
6. **Accept Recommendations**: Review AI suggestions and click "Apply" or "Accept"

## Key Features Explained

### Menu Engineering Categories

Items are classified into 4 categories:

- **⭐ Stars**: High popularity + High profit → Promote heavily
- **💎 Puzzles**: Low popularity + High profit → Push for visibility  
- **🐴 Plowhorses**: High popularity + Low profit → Increase margins
- **🐕 Dogs**: Low popularity + Low profit → Consider removing

### AI Recommendations

The system provides:

1. **For Customers**:
   - Personalized item suggestions
   - Frequently bought together items
   - Cart-based recommendations

2. **For Managers**:
   - Pricing suggestions
   - Marketing tips
   - Menu positioning advice
   - Action items per category

### Recommendation Strategies

- **Balanced**: Mix of all factors (default)
- **Upsell**: Focus on high-margin items
- **Cross-sell**: Suggest complementary items

## API Endpoints Reference

### Public (No Authentication)

```
GET  /api/menu/public/                          # Full menu
GET  /api/menu/sections/                        # Menu sections
GET  /api/menu/items/                           # Menu items
GET  /api/menu/items/{id}/                      # Item details
GET  /api/menu/recommendations/                 # General recommendations
POST /api/menu/recommendations/for-cart/        # Cart recommendations
GET  /api/menu/items/{id}/frequently-together/  # Co-purchase data
POST /api/menu/activities/                      # Log activity
```

### Manager (Authentication Required)

```
POST /api/menu/items/{id}/analyze/              # Analyze item
POST /api/menu/items/bulk_analyze/              # Analyze all
GET  /api/menu/items/stats/                     # Statistics
POST /api/menu/ai/sales-suggestions/            # Sales suggestions
POST /api/menu/ai/menu-analysis/                # Menu analysis
POST /api/menu/ai/owner-report/                 # Owner report
```

## Authentication for Manager Features

The frontend currently doesn't include a login UI. To use manager features:

### Option 1: Add Token Manually

1. Get auth token from Django admin or API
2. Open browser console on frontend
3. Run: `localStorage.setItem('authToken', 'your-token-here')`
4. Refresh page

### Option 2: Use Django Admin

1. Visit `http://localhost:8000/admin/`
2. Login with superuser credentials
3. Use Django admin to manage menu items

### Option 3: Implement Login (Future Enhancement)

Add login component that calls Django auth endpoints and stores token.

## Data Flow

### Customer Journey

1. Customer views menu → Frontend calls `/api/menu/public/`
2. System logs view activity → POST to `/api/menu/activities/`
3. Customer adds to cart → Cart stored in React Context
4. System fetches recommendations → POST to `/api/menu/recommendations/for-cart/`
5. Customer clicks item → GET `/api/menu/items/{id}/frequently-together/`

### Manager Journey

1. Manager opens dashboard → GET `/api/menu/items/` and `/api/menu/items/stats/`
2. Manager runs analysis → POST `/api/menu/items/bulk_analyze/`
3. Backend runs Menu Engineering classifier → Updates item categories
4. Manager views item → POST `/api/menu/ai/sales-suggestions/`
5. AI generates suggestions → Returns pricing, marketing, and action recommendations
6. Manager accepts suggestion → Frontend updates item (future: PATCH `/api/menu/items/{id}/`)

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
python manage.py runserver 8001
```

**Database errors:**
```bash
python manage.py migrate --run-syncdb
```

**CORS errors:**
Check `CORS_ALLOWED_ORIGINS` in settings includes `http://localhost:3000`

### Frontend Issues

**API connection failed:**
- Verify backend is running
- Check `.env` has correct `REACT_APP_API_URL`
- Check browser console for CORS errors

**Blank page:**
- Check browser console for errors
- Verify all dependencies installed: `npm install`

**Recommendations not showing:**
- Ensure items have been analyzed (run bulk analyze)
- Check that orders exist in database for co-purchase analysis

## Next Steps

1. **Add Sample Data**: Import menu items and create test orders
2. **Run Analysis**: Use "Analyze All Items" to classify menu
3. **Test Recommendations**: Add items to cart and see suggestions
4. **Explore Manager Features**: View suggestions for different categories
5. **Customize**: Modify styles, add features, integrate with POS system

## Production Deployment

### Backend

1. Set `DEBUG=False` in environment
2. Configure production database (PostgreSQL)
3. Set up static file serving
4. Use gunicorn/uwsgi for WSGI server
5. Configure nginx as reverse proxy
6. Set up SSL certificates

### Frontend

1. Build production bundle: `npm run build`
2. Serve `build/` directory with nginx or CDN
3. Update `REACT_APP_API_URL` to production backend
4. Enable production optimizations

## Support

For issues or questions:
- Check backend logs: Django console output
- Check frontend logs: Browser console (F12)
- Review API responses in Network tab
- Verify environment variables are set correctly

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (React)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Customer   │  │   Manager    │  │     Cart     │      │
│  │     Menu     │  │  Dashboard   │  │   Context    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                     ┌──────▼──────┐                          │
│                     │  API Service │                         │
│                     └──────┬──────┘                          │
└────────────────────────────┼────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────▼────────────────────────────────┐
│                      Backend (Django)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     Views    │  │  Serializers │  │    Models    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼───────┐    │
│  │              AI/ML Services                         │    │
│  │  • Menu Classifier (Menu Engineering Matrix)       │    │
│  │  • Recommendation Engine (Co-purchase Analysis)    │    │
│  │  • Sales Suggestions (AI-powered)                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                     ┌──────▼──────┐                          │
│                     │   Database  │                          │
│                     │  (PostgreSQL)│                         │
│                     └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## Features Summary

✅ Customer menu with AI recommendations
✅ Shopping cart with quantity management  
✅ Frequently bought together suggestions
✅ Manager dashboard with statistics
✅ Menu Engineering Matrix classification
✅ AI-powered sales suggestions
✅ Category filtering and analysis
✅ Activity tracking for ML improvements
✅ Responsive design
✅ Real-time recommendations based on cart

Happy menu engineering! 🍽️

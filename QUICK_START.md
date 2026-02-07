# Quick Start Guide

Get the Menu Engineering System running in 5 minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.8+)
python --version

# Check Node.js version (need 14+)
node --version

# Check npm
npm --version
```

## 1. Backend Setup (2 minutes)

```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements/dev.txt

# Run migrations
python manage.py migrate

# Create admin user (follow prompts)
python manage.py createsuperuser

# Start server
python manage.py runserver
```

✅ Backend running at `http://localhost:8000`

## 2. Frontend Setup (2 minutes)

Open a NEW terminal:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

✅ Frontend opens automatically at `http://localhost:3000`

## 3. First Steps (1 minute)

### View Customer Interface

1. Browser should open automatically to `http://localhost:3000`
2. You'll see the customer menu view
3. Click "Manager Dashboard" to switch views

### Add Sample Data

In the backend terminal:

```bash
# If you have the CSV file
python manage.py import_menu menu_engineering_input_items.csv
```

Or use Django admin:
1. Visit `http://localhost:8000/admin/`
2. Login with superuser credentials
3. Add menu sections and items manually

### Run AI Analysis

1. Switch to "Manager Dashboard" in the frontend
2. Click "🔄 Analyze All Items" button
3. Wait for analysis to complete
4. Items will be classified into categories

## What You Can Do Now

### As a Customer:
- ✅ Browse menu by sections
- ✅ See AI recommendations
- ✅ Add items to cart
- ✅ View frequently bought together items
- ✅ See category badges (⭐ Stars, 💎 Puzzles, etc.)

### As a Manager:
- ✅ View menu statistics by category
- ✅ Run AI analysis on all items
- ✅ Filter items by category
- ✅ View AI suggestions for each item
- ✅ See pricing and marketing recommendations

## Common Issues

### Backend won't start
```bash
# Try a different port
python manage.py runserver 8001

# Update frontend/.env
REACT_APP_API_URL=http://localhost:8001/api/menu
```

### Frontend shows "Failed to load menu"
- Check backend is running
- Check `frontend/.env` has correct API URL
- Check browser console for CORS errors

### No recommendations showing
- Run "Analyze All Items" first
- Add some menu items if database is empty
- Create test orders for co-purchase analysis

## Next Steps

1. **Add More Data**: Create menu sections and items
2. **Create Orders**: Add order history for better recommendations
3. **Test Features**: Try different recommendation strategies
4. **Customize**: Modify styles and add features
5. **Read Docs**: Check SETUP_GUIDE.md for detailed info

## Quick Reference

### Important URLs
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/menu/`
- Django Admin: `http://localhost:8000/admin/`
- Public Menu API: `http://localhost:8000/api/menu/public/`

### Key Files
- Frontend config: `frontend/.env`
- Backend config: `backend/.env.local`
- API service: `frontend/src/services/api.js`
- Main app: `frontend/src/App.js`

### Useful Commands

**Backend:**
```bash
python manage.py runserver              # Start server
python manage.py migrate                # Run migrations
python manage.py createsuperuser        # Create admin
python manage.py import_menu <file>     # Import menu data
```

**Frontend:**
```bash
npm start                               # Start dev server
npm run build                           # Build for production
npm test                                # Run tests
```

## Architecture at a Glance

```
Customer View          Manager Dashboard
     │                        │
     └────────┬───────────────┘
              │
         React App
              │
         API Service
              │
      ┌───────┴───────┐
      │               │
   Django API    AI Services
      │               │
      └───────┬───────┘
              │
         Database
```

## Features Summary

### Menu Engineering Categories

| Category | Icon | Meaning | Strategy |
|----------|------|---------|----------|
| Star | ⭐ | High popularity + High profit | Maintain & promote |
| Puzzle | 💎 | Low popularity + High profit | Push visibility |
| Plowhorse | 🐴 | High popularity + Low profit | Increase margins |
| Dog | 🐕 | Low popularity + Low profit | Consider removing |

### Recommendation Strategies

- **Balanced**: Mix of all factors (default)
- **Upsell**: Focus on high-margin items
- **Cross-sell**: Suggest complementary items

## Support

Need help? Check these resources:

1. **SETUP_GUIDE.md** - Detailed setup instructions
2. **SYSTEM_ARCHITECTURE.md** - Technical architecture
3. **FRONTEND_README.md** - Frontend documentation
4. **Backend logs** - Django console output
5. **Browser console** - Frontend errors (F12)

---

Happy menu engineering! 🍽️✨

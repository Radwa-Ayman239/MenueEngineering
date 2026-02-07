# Menu Engineering Frontend

An automated menu system with AI-powered recommendations for both managers and customers.

## Features

### Customer View
- **Smart Menu Display**: Items organized by sections with category badges (⭐ Stars, 💎 Puzzles, 🐴 Plowhorses)
- **AI Recommendations**: Personalized suggestions based on cart contents and popularity
- **Frequently Bought Together**: See items commonly purchased together
- **Shopping Cart**: Add, remove, and manage items with quantity controls
- **Activity Tracking**: Automatic tracking of views and interactions for ML improvements

### Manager Dashboard
- **Menu Overview**: Statistics by category with revenue tracking
- **AI Analysis**: Bulk analyze all items using Menu Engineering Matrix
- **Category Filtering**: Filter items by Star, Puzzle, Plowhorse, or Dog categories
- **Sales Suggestions**: Get AI-powered recommendations for each item:
  - Pricing suggestions
  - Marketing tips
  - Recommended actions
  - Priority levels
- **Accept/Reject Suggestions**: Review and apply AI recommendations

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the `frontend` directory:

```bash
cd frontend
cp .env.example .env
```

Edit `.env` and set your backend API URL:
```
REACT_APP_API_URL=http://localhost:8000/api/menu
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Start Development Server

```bash
npm start
```

The app will open at `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
```

## Backend Requirements

The frontend expects the following backend endpoints:

### Public Endpoints (No Auth)
- `GET /api/menu/public/` - Full menu with sections and items
- `GET /api/menu/sections/` - Menu sections
- `GET /api/menu/items/` - Menu items (with filters)
- `GET /api/menu/items/{id}/` - Single item details
- `GET /api/menu/recommendations/` - General recommendations
- `POST /api/menu/recommendations/for-cart/` - Cart-based recommendations
- `GET /api/menu/items/{id}/frequently-together/` - Frequently bought together
- `POST /api/menu/activities/` - Log customer activity

### Manager Endpoints (Auth Required)
- `POST /api/menu/items/{id}/analyze/` - Analyze single item
- `POST /api/menu/items/bulk_analyze/` - Analyze all items
- `GET /api/menu/items/stats/` - Category statistics
- `POST /api/menu/ai/sales-suggestions/` - Get AI sales suggestions
- `POST /api/menu/ai/menu-analysis/` - Menu structure analysis
- `POST /api/menu/ai/owner-report/` - Owner insights report

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── customer/
│   │   │   ├── CustomerMenu.js      # Main customer menu view
│   │   │   ├── CustomerMenu.css
│   │   │   ├── Cart.js              # Shopping cart
│   │   │   └── Cart.css
│   │   └── manager/
│   │       ├── ManagerDashboard.js  # Manager dashboard
│   │       └── ManagerDashboard.css
│   ├── contexts/
│   │   └── CartContext.js           # Cart state management
│   ├── services/
│   │   └── api.js                   # API service layer
│   ├── App.js                       # Main app component
│   ├── App.css                      # Global styles
│   └── index.js                     # Entry point
├── public/
├── package.json
└── .env
```

## Key Technologies

- **React 19**: UI framework
- **Context API**: State management for cart
- **Fetch API**: HTTP requests
- **CSS3**: Styling with flexbox and grid

## Features Breakdown

### Menu Engineering Categories

The system uses the Menu Engineering Matrix to classify items:

1. **⭐ Stars**: High popularity + High profit
   - Featured prominently
   - Maintain current positioning

2. **💎 Puzzles**: Low popularity + High profit
   - Highlighted as "Hidden Gems"
   - Recommended for upselling

3. **🐴 Plowhorses**: High popularity + Low profit
   - Marked as "Bestsellers"
   - Suggestions to increase margins

4. **🐕 Dogs**: Low popularity + Low profit
   - Minimal visibility
   - Recommendations to remove or rebrand

### Recommendation Engine

The system provides three recommendation strategies:

1. **Balanced**: Mix of popularity, profitability, and co-purchase patterns
2. **Upsell**: Focus on high-margin items
3. **Cross-sell**: Suggest complementary items from different sections

### Manager Actions

Managers can:
- View AI confidence scores for classifications
- See detailed metrics (price, cost, margin, purchases)
- Get actionable suggestions for each item
- Accept or reject AI recommendations
- Bulk analyze entire menu
- Filter by category for focused management

## API Integration

The `api.js` service handles all backend communication:

```javascript
import api from './services/api';

// Public APIs
const menu = await api.getPublicMenu();
const recommendations = await api.getRecommendations({ limit: 5 });

// Manager APIs (requires auth token)
api.setToken('your-auth-token');
const analysis = await api.analyzeMenuItem(itemId);
```

## Customization

### Styling
- Edit CSS files in `components/` directories
- Modify `App.css` for global styles
- Color scheme uses `#667eea` (purple) as primary

### API Endpoints
- Update `API_BASE_URL` in `services/api.js`
- Or set `REACT_APP_API_URL` in `.env`

### Features
- Add new views in `components/`
- Extend `CartContext` for additional cart features
- Add new API methods in `services/api.js`

## Troubleshooting

### CORS Issues
Ensure your Django backend has CORS configured:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
```

### API Connection
Check that `REACT_APP_API_URL` matches your backend URL

### Authentication
Manager features require a valid auth token. Implement login flow or use Knox tokens from backend.

## Future Enhancements

- [ ] User authentication UI
- [ ] Order placement and tracking
- [ ] Real-time updates with WebSockets
- [ ] Advanced filtering and search
- [ ] Mobile-responsive improvements
- [ ] Image upload for menu items
- [ ] Sales analytics charts
- [ ] Bundle/combo creation
- [ ] Promotional campaigns management

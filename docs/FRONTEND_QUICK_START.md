# Frontend Quick Start Guide

## Running the Frontend Locally

### Prerequisites
- Node.js 18+ installed
- npm available in PATH
- Backend service running (or API endpoint configured)

### Quick Setup (2 minutes)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at: **http://localhost:3000**

## Testing the Three User Roles

### 1. Customer (Public Access) ✅
**No login required**

1. Open http://localhost:3000
2. Browse the menu
3. Click items to add to cart
4. View cart summary in sidebar
5. Navigate to staff/manager portals from footer links

**Demo Features**:
- Real-time total calculation
- Add/remove items from cart
- Cart persists across page refreshes

---

### 2. Staff Portal 👥
**Login Required: Email/Password + OTP**

1. Click "👨‍💼 Staff" link on homepage
2. Enter credentials:
   - **Email**: staff@example.com
   - **Password**: password
3. Receive OTP in backend logs or email
4. Enter OTP (should be in backend response logs)
5. Create orders for customers:
   - Select menu items with quantities
   - Enter customer name (required)
   - Enter customer email (optional)
   - Click "Create Order"

**Demo Features**:
- Two-factor authentication
- Bulk order creation
- Item quantity adjustment
- Customer details collection
- Order summary with total

---

### 3. Manager Portal 📊
**Login Required: Email/Password + OTP**

1. Click "📊 Manager" link on homepage
2. Enter credentials:
   - **Email**: manager@example.com
   - **Password**: password
3. Receive and enter OTP
4. Access three tabs:
   - **Dashboard**: View analytics and AI recommendations
   - **Staff Management**: Add/manage team members
   - **Reports**: Business insights and performance data

**Demo Features**:
- Sales analytics
- Top performing items
- AI-powered recommendations
- Staff member management
- Team performance metrics

---

## Environment Configuration

### Default Configuration
The frontend automatically connects to:
- **Local Dev**: `http://localhost:8000/api`
- **Docker**: `http://backend:8000/api`

### Custom API URL
Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://your-backend:8000/api
```

Then restart the dev server.

---

## Build for Production

```bash
# Create production build
npm run build

# Start production server (if needed)
npm start
```

The build output will be in `.next/` directory.

---

## Docker Deployment

### Build and Run All Services
```bash
# From project root
docker-compose up --build

# Services will start:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - ML Service: http://localhost:8001
```

### View Frontend Logs
```bash
docker logs -f menu_engineering_frontend
```

---

## API Testing

### Quick API Health Check
```bash
# Check if backend is responding
curl http://localhost:8000/api/menu/items/

# Response should be a list of menu items
```

### Frontend Console Debugging
1. Open browser DevTools (F12)
2. Go to Console tab
3. All API calls are logged
4. Check Network tab to see requests/responses

---

## Troubleshooting

### Build Errors
```bash
# Clear cache and reinstall
rm -r node_modules package-lock.json
npm install
npm run build
```

### API Connection Issues
- Check backend is running: `curl http://localhost:8000/api/`
- Verify NEXT_PUBLIC_API_URL in `.env.local`
- Check browser console for CORS errors
- Ensure backend has proper CORS headers

### Login Issues
- Check backend auth endpoints exist
- Verify OTP is being sent by backend
- Check localStorage in browser DevTools
- Verify tokens are saved correctly

### Port Already in Use
```bash
# Frontend: Change port in package.json or use:
npm run dev -- -p 3001

# Backend: Change port in Django settings or:
python manage.py runserver 8001
```

---

## File Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Customer homepage
│   ├── staff/
│   │   ├── login/
│   │   │   └── page.tsx   # Staff login (2FA)
│   │   └── page.tsx       # Staff portal
│   └── manager/
│       ├── login/
│       │   └── page.tsx   # Manager login (2FA)
│       └── page.tsx       # Manager dashboard
├── components/            # Reusable components
│   └── ui/               # shadcn/ui components
├── lib/
│   ├── api.ts            # API service (35+ methods)
│   ├── contexts/         # React contexts
│   └── utils.ts          # Utilities
├── public/               # Static assets
└── Dockerfile            # Container image
```

---

## Key Features Implemented

- ✅ Three user role portals (Customer, Staff, Manager)
- ✅ Two-factor authentication (Email/Password + OTP)
- ✅ Shopping cart with localStorage persistence
- ✅ Order creation and management
- ✅ Analytics dashboard
- ✅ Staff member management
- ✅ AI-powered recommendations
- ✅ Responsive design (mobile-first)
- ✅ TypeScript type safety
- ✅ Comprehensive error handling

---

## Performance Optimization

- Pre-rendered static pages (faster load times)
- Code splitting per route (minimal bundle size)
- Image optimization enabled
- CSS-in-JS for styling
- SSR-safe state management

---

## Next Steps

1. ✅ Start frontend dev server: `npm run dev`
2. ✅ Test each user role login
3. ✅ Verify API connections work
4. ✅ Test order creation workflow
5. ✅ Check analytics dashboard
6. ✅ Deploy with Docker: `docker-compose up`

---

**Questions?** Check browser console (F12 → Console tab) for detailed API error messages.

import React, { useState } from 'react';
import { CartProvider } from './contexts/CartContext';
import CustomerMenu from './components/customer/CustomerMenu';
import Cart from './components/customer/Cart';
import ManagerDashboard from './components/manager/ManagerDashboard';
import './App.css';

function App() {
  const [view, setView] = useState('customer'); // 'customer' or 'manager'
  const [showCart, setShowCart] = useState(false);

  return (
    <CartProvider>
      <div className="App">
        <nav className="main-nav">
          <div className="nav-content">
            <h1 className="logo">🍽️ Menu Engineering</h1>
            <div className="nav-buttons">
              <button
                className={view === 'customer' ? 'active' : ''}
                onClick={() => setView('customer')}
              >
                Customer View
              </button>
              <button
                className={view === 'manager' ? 'active' : ''}
                onClick={() => setView('manager')}
              >
                Manager Dashboard
              </button>
              {view === 'customer' && (
                <button
                  className="cart-toggle"
                  onClick={() => setShowCart(!showCart)}
                >
                  🛒 Cart
                </button>
              )}
            </div>
          </div>
        </nav>

        <main className="main-content">
          {view === 'customer' ? (
            <div className="customer-view">
              <div className={`menu-container ${showCart ? 'with-cart' : ''}`}>
                <CustomerMenu />
              </div>
              {showCart && (
                <div className="cart-sidebar">
                  <Cart />
                </div>
              )}
            </div>
          ) : (
            <ManagerDashboard />
          )}
        </main>

        <footer className="main-footer">
          <p>
            Powered by AI-driven Menu Engineering | Categories: ⭐ Stars | 💎 Puzzles | 🐴
            Plowhorses | 🐕 Dogs
          </p>
        </footer>
      </div>
    </CartProvider>
  );
}

export default App;

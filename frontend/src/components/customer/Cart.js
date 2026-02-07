import React from 'react';
import { useCart } from '../../contexts/CartContext';
import './Cart.css';

const Cart = () => {
  const { cart, updateQuantity, removeFromCart, getCartTotal, clearCart } = useCart();

  if (cart.length === 0) {
    return (
      <div className="cart-empty">
        <h2>Your Cart</h2>
        <p>Your cart is empty. Start adding delicious items!</p>
      </div>
    );
  }

  return (
    <div className="cart">
      <div className="cart-header">
        <h2>Your Cart ({cart.length})</h2>
        <button className="btn-clear" onClick={clearCart}>
          Clear All
        </button>
      </div>

      <div className="cart-items">
        {cart.map((item) => (
          <div key={item.id} className="cart-item">
            <div className="cart-item-info">
              <h3>{item.title}</h3>
              <p className="cart-item-price">${parseFloat(item.price).toFixed(2)}</p>
            </div>
            <div className="cart-item-controls">
              <button
                className="btn-qty"
                onClick={() => updateQuantity(item.id, item.quantity - 1)}
              >
                -
              </button>
              <span className="cart-item-qty">{item.quantity}</span>
              <button
                className="btn-qty"
                onClick={() => updateQuantity(item.id, item.quantity + 1)}
              >
                +
              </button>
              <button
                className="btn-remove"
                onClick={() => removeFromCart(item.id)}
              >
                Remove
              </button>
            </div>
            <div className="cart-item-total">
              ${(parseFloat(item.price) * item.quantity).toFixed(2)}
            </div>
          </div>
        ))}
      </div>

      <div className="cart-summary">
        <div className="cart-total">
          <span>Total:</span>
          <span className="total-amount">${getCartTotal().toFixed(2)}</span>
        </div>
        <button className="btn-checkout">Proceed to Checkout</button>
      </div>
    </div>
  );
};

export default Cart;

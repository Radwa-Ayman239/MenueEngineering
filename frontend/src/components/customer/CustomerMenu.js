import React, { useState, useEffect, useMemo } from 'react';
import { useCart } from '../../contexts/CartContext';
import api from '../../services/api';
import './CustomerMenu.css';

const CustomerMenu = () => {
  const [menu, setMenu] = useState([]);
  const [allItems, setAllItems] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [bundles, setBundles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);
  const [frequentlyBought, setFrequentlyBought] = useState([]);
  const [activeCategory, setActiveCategory] = useState('all');
  const [activeSection, setActiveSection] = useState('all');
  const { cart, addToCart, sessionId } = useCart();

  useEffect(() => {
    loadMenu();
    loadRecommendations();
  }, []);

  useEffect(() => {
    if (cart.length > 0) {
      loadCartRecommendations();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cart]);

  const loadMenu = async () => {
    try {
      const [menuData, itemsData] = await Promise.all([
        api.getPublicMenu(),
        api.getMenuItems({ is_active: true }),
      ]);
      setMenu(menuData.menu || []);
      setAllItems(itemsData || []);
      generateBundles(itemsData);
    } catch (error) {
      console.error('Failed to load menu:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRecommendations = async () => {
    try {
      const data = await api.getRecommendations({ limit: 8, strategy: 'balanced' });
      setRecommendations(data.recommendations || []);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    }
  };

  const loadCartRecommendations = async () => {
    try {
      const itemIds = cart.map(item => item.id);
      const data = await api.getCartRecommendations(itemIds, 'upsell');
      setRecommendations(data.recommendations || []);
    } catch (error) {
      console.error('Failed to load cart recommendations:', error);
    }
  };

  const generateBundles = (items) => {
    const bundleList = [];

    // Popular Combo - Stars
    const starItems = items.filter(item => item.category === 'star').slice(0, 3);
    if (starItems.length >= 2) {
      const originalPrice = starItems.reduce((sum, item) => sum + parseFloat(item.price), 0);
      bundleList.push({
        id: 'bundle-popular',
        name: '⭐ Popular Favorites',
        description: 'Our most loved items together at a special price',
        items: starItems,
        discount: 15,
        originalPrice,
        discountedPrice: originalPrice * 0.85,
        badge: 'BESTSELLER',
        gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
      });
    }

    // Premium Selection - Puzzles (high margin, low popularity - need exposure)
    const puzzleItems = items.filter(item => item.category === 'puzzle').slice(0, 2);
    if (puzzleItems.length >= 2) {
      const originalPrice = puzzleItems.reduce((sum, item) => sum + parseFloat(item.price), 0);
      bundleList.push({
        id: 'bundle-premium',
        name: '💎 Premium Discovery',
        description: 'Discover our hidden gems with an exclusive discount',
        items: puzzleItems,
        discount: 20,
        originalPrice,
        discountedPrice: originalPrice * 0.80,
        badge: 'EXCLUSIVE',
        gradient: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
      });
    }

    // Value Bundle - mix categories
    const mixedItems = [
      ...items.filter(item => item.category === 'star').slice(0, 1),
      ...items.filter(item => item.category === 'plowhorse').slice(0, 2),
    ];
    if (mixedItems.length >= 2) {
      const originalPrice = mixedItems.reduce((sum, item) => sum + parseFloat(item.price), 0);
      bundleList.push({
        id: 'bundle-value',
        name: '🔥 Value Deal',
        description: 'Great taste at an unbeatable price',
        items: mixedItems,
        discount: 12,
        originalPrice,
        discountedPrice: originalPrice * 0.88,
        badge: 'BEST VALUE',
        gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
      });
    }

    setBundles(bundleList);
  };

  const handleItemClick = async (item) => {
    setSelectedItem(item);
    api.logActivity(sessionId, 'view', item.id);

    try {
      const data = await api.getFrequentlyBoughtTogether(item.id, 4);
      setFrequentlyBought(data.frequently_bought_together || []);
    } catch (error) {
      console.error('Failed to load frequently bought together:', error);
      setFrequentlyBought([]);
    }
  };

  const handleAddToCart = (item) => {
    addToCart(item);
    api.logActivity(sessionId, 'add_to_cart', item.id);
  };

  const handleAddBundleToCart = (bundle) => {
    bundle.items.forEach(item => addToCart(item));
    api.logActivity(sessionId, 'add_to_cart', null, { bundle: bundle.name });
  };

  const getPopularityBadge = (item) => {
    const purchases = item.total_purchases || 0;
    if (purchases > 100) return { label: '🔥 Trending', class: 'trending' };
    if (purchases > 50) return { label: '❤️ Popular', class: 'popular' };
    if (item.category === 'puzzle') return { label: '💎 Hidden Gem', class: 'hidden-gem' };
    return null;
  };

  const getCategoryInfo = (category) => {
    const info = {
      star: { icon: '⭐', label: 'Popular Choice', color: '#10b981' },
      puzzle: { icon: '💎', label: 'Premium', color: '#8b5cf6' },
      plowhorse: { icon: '🔥', label: 'Bestseller', color: '#f59e0b' },
      dog: { icon: '🍽️', label: '', color: '#6b7280' },
    };
    return info[category] || { icon: '🍽️', label: '', color: '#6b7280' };
  };

  const getSalePrice = (item) => {
    // Simulate sales based on category (Dogs get discounts to boost sales)
    if (item.category === 'dog') {
      return {
        onSale: true,
        salePrice: (parseFloat(item.price) * 0.85).toFixed(2),
        discount: 15,
      };
    }
    return { onSale: false };
  };

  // Memoized filtered items
  const filteredMenu = useMemo(() => {
    if (activeSection === 'all' && activeCategory === 'all') {
      return menu;
    }

    return menu.map(section => {
      if (activeSection !== 'all' && section.id !== activeSection) {
        return null;
      }

      const filteredItems = section.items.filter(item => {
        if (activeCategory === 'all') return true;
        // Find the full item data to check category
        const fullItem = allItems.find(i => i.id === item.id);
        return fullItem?.category === activeCategory;
      });

      if (filteredItems.length === 0) return null;
      return { ...section, items: filteredItems };
    }).filter(Boolean);
  }, [menu, allItems, activeSection, activeCategory]);

  // Sort items by category importance (Stars first, then Puzzles, etc.)
  const sortedMenu = useMemo(() => {
    const categoryOrder = { star: 0, puzzle: 1, plowhorse: 2, dog: 3 };

    return filteredMenu.map(section => ({
      ...section,
      items: [...section.items].sort((a, b) => {
        const itemA = allItems.find(i => i.id === a.id);
        const itemB = allItems.find(i => i.id === b.id);
        const orderA = categoryOrder[itemA?.category] ?? 4;
        const orderB = categoryOrder[itemB?.category] ?? 4;
        return orderA - orderB;
      })
    }));
  }, [filteredMenu, allItems]);

  const getItemImage = (item) => {
    return item.image || `https://via.placeholder.com/400x300/1a1a2e/667eea?text=${encodeURIComponent(item.title)}`;
  };

  if (loading) {
    return (
      <div className="menu-loading">
        <div className="loading-spinner"></div>
        <p>Loading delicious menu...</p>
      </div>
    );
  }

  return (
    <div className="customer-menu">
      {/* Hero Header */}
      <header className="menu-header">
        <div className="header-content">
          <h1>🍽️ Our Menu</h1>
          <p>Discover delicious dishes crafted with passion</p>
        </div>
        <div className="header-decoration"></div>
      </header>

      {/* Category Filter */}
      <div className="category-nav">
        <div className="nav-scroll">
          <button
            className={`nav-btn ${activeCategory === 'all' ? 'active' : ''}`}
            onClick={() => setActiveCategory('all')}
          >
            All Items
          </button>
          <button
            className={`nav-btn ${activeCategory === 'star' ? 'active' : ''}`}
            onClick={() => setActiveCategory('star')}
          >
            ⭐ Popular
          </button>
          <button
            className={`nav-btn ${activeCategory === 'puzzle' ? 'active' : ''}`}
            onClick={() => setActiveCategory('puzzle')}
          >
            💎 Premium
          </button>
          <button
            className={`nav-btn ${activeCategory === 'plowhorse' ? 'active' : ''}`}
            onClick={() => setActiveCategory('plowhorse')}
          >
            🔥 Bestsellers
          </button>
          {menu.map((section) => (
            <button
              key={section.id}
              className={`nav-btn section-btn ${activeSection === section.id ? 'active' : ''}`}
              onClick={() => {
                setActiveSection(activeSection === section.id ? 'all' : section.id);
                setActiveCategory('all');
              }}
            >
              {section.name}
            </button>
          ))}
        </div>
      </div>

      {/* Special Bundles */}
      {bundles.length > 0 && activeCategory === 'all' && (
        <section className="bundles-section">
          <div className="section-title">
            <h2>🎁 Special Bundles & Deals</h2>
            <p>Save more with our curated combinations</p>
          </div>
          <div className="bundles-carousel">
            {bundles.map((bundle) => (
              <div
                key={bundle.id}
                className="bundle-card"
                style={{ '--bundle-gradient': bundle.gradient }}
              >
                <div className="bundle-badge">{bundle.badge}</div>
                <div className="bundle-header">
                  <h3>{bundle.name}</h3>
                  <p>{bundle.description}</p>
                </div>

                <div className="bundle-items">
                  {bundle.items.map((item, idx) => (
                    <div key={idx} className="bundle-item-chip">
                      <span className="chip-name">{item.title}</span>
                    </div>
                  ))}
                </div>

                <div className="bundle-footer">
                  <div className="bundle-pricing">
                    <span className="original-price">${bundle.originalPrice.toFixed(2)}</span>
                    <span className="sale-price">${bundle.discountedPrice.toFixed(2)}</span>
                  </div>
                  <div className="bundle-savings">
                    Save {bundle.discount}%
                  </div>
                </div>

                <button
                  className="btn-add-bundle"
                  onClick={() => handleAddBundleToCart(bundle)}
                >
                  Add Bundle to Cart
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* AI Recommendations */}
      {recommendations.length > 0 && (
        <section className="recommendations-section">
          <div className="section-title">
            <h2>✨ {cart.length > 0 ? 'Pairs Well With Your Order' : 'Recommended For You'}</h2>
            <p>Personalized picks based on your preferences</p>
          </div>
          <div className="recommendations-scroll">
            {recommendations.map((rec) => {
              const sale = getSalePrice(rec.item);
              return (
                <div
                  key={rec.item.id}
                  className="recommendation-card"
                  onClick={() => handleItemClick(rec.item)}
                >
                  <div className="rec-image">
                    <img src={getItemImage(rec.item)} alt={rec.item.title} />
                    {sale.onSale && (
                      <span className="sale-badge">-{sale.discount}%</span>
                    )}
                  </div>
                  <div className="rec-content">
                    <h3>{rec.item.title}</h3>
                    <p className="rec-reason">{rec.reason}</p>
                    <div className="rec-footer">
                      <div className="rec-price">
                        {sale.onSale ? (
                          <>
                            <span className="price-old">${parseFloat(rec.item.price).toFixed(2)}</span>
                            <span className="price-sale">${sale.salePrice}</span>
                          </>
                        ) : (
                          <span className="price-current">${parseFloat(rec.item.price).toFixed(2)}</span>
                        )}
                      </div>
                      <button
                        className="btn-add-small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAddToCart(rec.item);
                        }}
                      >
                        Add
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Menu Sections */}
      <div className="menu-sections">
        {sortedMenu.map((section) => (
          <section key={section.id} className="menu-section">
            <div className="section-title">
              <h2>{section.name}</h2>
              {section.description && <p>{section.description}</p>}
            </div>

            <div className="menu-grid">
              {section.items.map((item) => {
                const fullItem = allItems.find(i => i.id === item.id) || item;
                const categoryInfo = getCategoryInfo(fullItem.category);
                const popularityBadge = getPopularityBadge(fullItem);
                const sale = getSalePrice(fullItem);

                return (
                  <div
                    key={item.id}
                    className="menu-card"
                    onClick={() => handleItemClick(fullItem)}
                  >
                    <div className="card-image">
                      <img src={getItemImage(item)} alt={item.title} loading="lazy" />

                      {/* Badges */}
                      <div className="card-badges">
                        {popularityBadge && (
                          <span className={`badge popularity ${popularityBadge.class}`}>
                            {popularityBadge.label}
                          </span>
                        )}
                        {sale.onSale && (
                          <span className="badge sale">-{sale.discount}% OFF</span>
                        )}
                      </div>

                      {/* Category indicator */}
                      {categoryInfo.label && (
                        <span
                          className="category-indicator"
                          style={{ backgroundColor: categoryInfo.color }}
                        >
                          {categoryInfo.icon} {categoryInfo.label}
                        </span>
                      )}
                    </div>

                    <div className="card-content">
                      <h3>{item.title}</h3>
                      <p className="item-description">
                        {item.description || 'A delicious choice for any occasion.'}
                      </p>

                      <div className="card-footer">
                        <div className="price-container">
                          {sale.onSale ? (
                            <>
                              <span className="price-original">${parseFloat(item.price).toFixed(2)}</span>
                              <span className="price-sale">${sale.salePrice}</span>
                            </>
                          ) : (
                            <span className="price">${parseFloat(item.price).toFixed(2)}</span>
                          )}
                        </div>
                        <button
                          className="btn-add"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAddToCart(fullItem);
                          }}
                        >
                          Add to Cart
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        ))}
      </div>

      {/* Item Detail Modal */}
      {selectedItem && (
        <div className="modal-overlay" onClick={() => setSelectedItem(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedItem(null)}>
              ×
            </button>

            <div className="modal-image">
              <img src={getItemImage(selectedItem)} alt={selectedItem.title} />
              {getSalePrice(selectedItem).onSale && (
                <span className="modal-sale-badge">
                  SALE -{getSalePrice(selectedItem).discount}%
                </span>
              )}
            </div>

            <div className="modal-details">
              <div className="modal-header">
                <h2>{selectedItem.title}</h2>
                {getCategoryInfo(selectedItem.category).label && (
                  <span
                    className="modal-category"
                    style={{ backgroundColor: getCategoryInfo(selectedItem.category).color }}
                  >
                    {getCategoryInfo(selectedItem.category).icon} {getCategoryInfo(selectedItem.category).label}
                  </span>
                )}
              </div>

              <p className="modal-description">
                {selectedItem.description || 'A carefully crafted dish made with the finest ingredients. Perfect for any occasion.'}
              </p>

              <div className="modal-price-section">
                {getSalePrice(selectedItem).onSale ? (
                  <>
                    <span className="modal-price-original">${parseFloat(selectedItem.price).toFixed(2)}</span>
                    <span className="modal-price-sale">${getSalePrice(selectedItem).salePrice}</span>
                    <span className="modal-savings">You save ${(parseFloat(selectedItem.price) - parseFloat(getSalePrice(selectedItem).salePrice)).toFixed(2)}</span>
                  </>
                ) : (
                  <span className="modal-price">${parseFloat(selectedItem.price).toFixed(2)}</span>
                )}
              </div>

              {frequentlyBought.length > 0 && (
                <div className="frequently-bought">
                  <h3>🍽️ Frequently Bought Together</h3>
                  <div className="fbt-grid">
                    {frequentlyBought.map((fbt) => (
                      <div key={fbt.item.id} className="fbt-card">
                        <img src={getItemImage(fbt.item)} alt={fbt.item.title} />
                        <div className="fbt-info">
                          <span className="fbt-name">{fbt.item.title}</span>
                          <span className="fbt-confidence">{fbt.message}</span>
                          <div className="fbt-footer">
                            <span className="fbt-price">${parseFloat(fbt.item.price).toFixed(2)}</span>
                            <button
                              className="btn-add-fbt"
                              onClick={() => handleAddToCart(fbt.item)}
                            >
                              Add
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button
                className="btn-add-large"
                onClick={() => {
                  handleAddToCart(selectedItem);
                  setSelectedItem(null);
                }}
              >
                Add to Cart - ${getSalePrice(selectedItem).onSale
                  ? getSalePrice(selectedItem).salePrice
                  : parseFloat(selectedItem.price).toFixed(2)}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerMenu;

import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './ManagerDashboard.css';

const ManagerDashboard = () => {
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [suggestions, setSuggestions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [filter, setFilter] = useState('all');
  const [activeTab, setActiveTab] = useState('items'); // 'items', 'recommendations', 'reports'
  const [pendingRecommendations, setPendingRecommendations] = useState([]);
  const [ownerReport, setOwnerReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [suggestionHistory, setSuggestionHistory] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [itemsData, statsData] = await Promise.all([
        api.getMenuItems({ is_active: true }),
        api.getItemStats(),
      ]);
      setItems(itemsData);
      setStats(statsData);
      
      // Generate pending recommendations from items
      const pending = itemsData
        .filter(item => item.category && !item.suggestion_applied)
        .slice(0, 10)
        .map(item => ({
          item,
          type: getRecommendationType(item.category),
          priority: getCategoryPriority(item.category),
        }));
      setPendingRecommendations(pending);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationType = (category) => {
    const types = {
      star: 'Maintain & Promote',
      puzzle: 'Increase Visibility',
      plowhorse: 'Optimize Pricing',
      dog: 'Consider Removal',
    };
    return types[category] || 'Analyze Further';
  };

  const getCategoryPriority = (category) => {
    const priorities = {
      dog: 'high',
      puzzle: 'medium',
      plowhorse: 'medium',
      star: 'low',
    };
    return priorities[category] || 'low';
  };

  const handleBulkAnalyze = async () => {
    setAnalyzing(true);
    try {
      await api.bulkAnalyzeItems();
      await loadData();
    } catch (error) {
      console.error('Failed to analyze items:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleItemClick = async (item) => {
    setSelectedItem(item);
    setSuggestions(null);
    
    try {
      const data = await api.getSalesSuggestions(item.id);
      setSuggestions(data);
    } catch (error) {
      console.error('Failed to load suggestions:', error);
      setSuggestions({ error: 'Failed to load AI suggestions' });
    }
  };

  const handleAcceptSuggestion = async (item, suggestion, action) => {
    // Add to history
    const historyEntry = {
      id: Date.now(),
      item: item.title,
      action: action,
      suggestion: suggestion,
      status: 'accepted',
      timestamp: new Date().toLocaleString(),
    };
    setSuggestionHistory(prev => [historyEntry, ...prev].slice(0, 20));
    
    // Remove from pending
    setPendingRecommendations(prev => 
      prev.filter(rec => rec.item.id !== item.id)
    );
    
    // Close modal
    setSelectedItem(null);
    setSuggestions(null);
  };

  const handleRejectSuggestion = async (item, suggestion) => {
    const historyEntry = {
      id: Date.now(),
      item: item.title,
      action: 'Rejected',
      suggestion: suggestion,
      status: 'rejected',
      timestamp: new Date().toLocaleString(),
    };
    setSuggestionHistory(prev => [historyEntry, ...prev].slice(0, 20));
    
    setPendingRecommendations(prev => 
      prev.filter(rec => rec.item.id !== item.id)
    );
    
    setSelectedItem(null);
    setSuggestions(null);
  };

  const handleGenerateReport = async (period = 'weekly') => {
    setReportLoading(true);
    try {
      const data = await api.getOwnerReport(period);
      setOwnerReport(data);
    } catch (error) {
      console.error('Failed to generate report:', error);
      setOwnerReport({ error: 'Failed to generate report. Make sure ML service is running.' });
    } finally {
      setReportLoading(false);
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      star: '#10b981',
      puzzle: '#8b5cf6',
      plowhorse: '#f59e0b',
      dog: '#ef4444',
    };
    return colors[category] || '#6b7280';
  };

  const getCategoryIcon = (category) => {
    const icons = {
      star: '⭐',
      puzzle: '💎',
      plowhorse: '🐴',
      dog: '🐕',
    };
    return icons[category] || '❓';
  };

  const getPriorityBadge = (priority) => {
    const badges = {
      high: { label: 'High Priority', class: 'priority-high' },
      medium: { label: 'Medium', class: 'priority-medium' },
      low: { label: 'Low', class: 'priority-low' },
    };
    return badges[priority] || badges.low;
  };

  const filteredItems = items.filter(item => {
    if (filter === 'all') return true;
    return item.category === filter;
  });

  const getCategoryPercentage = (category) => {
    if (!stats || !stats.categories) return 0;
    const cat = stats.categories.find(c => c.category === category);
    if (!cat || !stats.total_items) return 0;
    return ((cat.count / stats.total_items) * 100).toFixed(1);
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="manager-dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>📊 Manager Dashboard</h1>
          <p className="header-subtitle">AI-powered menu insights and recommendations</p>
        </div>
        <div className="header-actions">
          <button
            className="btn-analyze"
            onClick={handleBulkAnalyze}
            disabled={analyzing}
          >
            {analyzing ? (
              <>
                <span className="spinner-small"></span>
                Analyzing...
              </>
            ) : (
              '🔄 Analyze All Items'
            )}
          </button>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="dashboard-tabs">
        <button
          className={`tab-btn ${activeTab === 'items' ? 'active' : ''}`}
          onClick={() => setActiveTab('items')}
        >
          📋 Menu Items
        </button>
        <button
          className={`tab-btn ${activeTab === 'recommendations' ? 'active' : ''}`}
          onClick={() => setActiveTab('recommendations')}
        >
          🤖 AI Recommendations
          {pendingRecommendations.length > 0 && (
            <span className="badge-count">{pendingRecommendations.length}</span>
          )}
        </button>
        <button
          className={`tab-btn ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          📈 Owner Reports
        </button>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="stats-overview">
          <div className="stats-grid">
            <div className="stat-card stat-total">
              <div className="stat-icon">🍽️</div>
              <div className="stat-info">
                <h3>Total Items</h3>
                <p className="stat-value">{stats.total_items}</p>
              </div>
            </div>
            {['star', 'puzzle', 'plowhorse', 'dog'].map((cat) => {
              const catData = stats.categories?.find(c => c.category === cat) || { count: 0, total_revenue: 0 };
              return (
                <div
                  key={cat}
                  className="stat-card"
                  style={{ borderLeft: `4px solid ${getCategoryColor(cat)}` }}
                >
                  <div className="stat-icon">{getCategoryIcon(cat)}</div>
                  <div className="stat-info">
                    <h3>{cat.charAt(0).toUpperCase() + cat.slice(1)}s</h3>
                    <p className="stat-value">{catData.count}</p>
                    <p className="stat-detail">{getCategoryPercentage(cat)}% of menu</p>
                  </div>
                  <div className="stat-bar">
                    <div 
                      className="stat-bar-fill"
                      style={{ 
                        width: `${getCategoryPercentage(cat)}%`,
                        backgroundColor: getCategoryColor(cat)
                      }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Menu Items Tab */}
      {activeTab === 'items' && (
        <div className="items-section">
          <div className="items-header">
            <h2>Menu Items</h2>
            <div className="filter-buttons">
              {['all', 'star', 'puzzle', 'plowhorse', 'dog'].map((f) => (
                <button
                  key={f}
                  className={filter === f ? 'active' : ''}
                  onClick={() => setFilter(f)}
                >
                  {f === 'all' ? 'All' : `${getCategoryIcon(f)} ${f.charAt(0).toUpperCase() + f.slice(1)}s`}
                </button>
              ))}
            </div>
          </div>

          <div className="items-table-container">
            <table className="items-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Category</th>
                  <th>Price</th>
                  <th>Cost</th>
                  <th>Margin</th>
                  <th>Purchases</th>
                  <th>AI Confidence</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <div className="item-info">
                        <strong>{item.title}</strong>
                        <small>{item.section_name}</small>
                      </div>
                    </td>
                    <td>
                      <span
                        className="category-badge"
                        style={{ backgroundColor: getCategoryColor(item.category) }}
                      >
                        {getCategoryIcon(item.category)} {item.category || 'N/A'}
                      </span>
                    </td>
                    <td className="price">${parseFloat(item.price).toFixed(2)}</td>
                    <td className="cost">${parseFloat(item.cost || 0).toFixed(2)}</td>
                    <td className="margin">
                      <strong>${parseFloat(item.margin || 0).toFixed(2)}</strong>
                    </td>
                    <td className="purchases">{item.total_purchases || 0}</td>
                    <td>
                      <div className="confidence-bar">
                        <div 
                          className="confidence-fill"
                          style={{ width: `${(item.ai_confidence || 0) * 100}%` }}
                        ></div>
                        <span>{item.ai_confidence ? `${(item.ai_confidence * 100).toFixed(0)}%` : 'N/A'}</span>
                      </div>
                    </td>
                    <td>
                      <button
                        className="btn-view"
                        onClick={() => handleItemClick(item)}
                      >
                        View Suggestions
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* AI Recommendations Tab */}
      {activeTab === 'recommendations' && (
        <div className="recommendations-section">
          <div className="section-header">
            <h2>🤖 AI Recommendations</h2>
            <p>Review and apply AI-generated suggestions for your menu items</p>
          </div>

          {pendingRecommendations.length > 0 ? (
            <div className="recommendations-grid">
              {pendingRecommendations.map((rec) => {
                const priorityBadge = getPriorityBadge(rec.priority);
                return (
                  <div key={rec.item.id} className="recommendation-card">
                    <div className="rec-header">
                      <span
                        className="category-badge"
                        style={{ backgroundColor: getCategoryColor(rec.item.category) }}
                      >
                        {getCategoryIcon(rec.item.category)} {rec.item.category}
                      </span>
                      <span className={`priority-badge ${priorityBadge.class}`}>
                        {priorityBadge.label}
                      </span>
                    </div>
                    <h3>{rec.item.title}</h3>
                    <p className="rec-type">{rec.type}</p>
                    <div className="rec-details">
                      <span>Price: ${parseFloat(rec.item.price).toFixed(2)}</span>
                      <span>Purchases: {rec.item.total_purchases}</span>
                    </div>
                    <div className="rec-actions">
                      <button
                        className="btn-accept"
                        onClick={() => handleItemClick(rec.item)}
                      >
                        Review & Accept
                      </button>
                      <button
                        className="btn-reject"
                        onClick={() => handleRejectSuggestion(rec.item, rec.type)}
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon">✨</span>
              <h3>All caught up!</h3>
              <p>No pending recommendations. Run "Analyze All Items" to generate new suggestions.</p>
            </div>
          )}

          {/* Suggestion History */}
          {suggestionHistory.length > 0 && (
            <div className="history-section">
              <h3>📜 Recent Actions</h3>
              <div className="history-list">
                {suggestionHistory.map((entry) => (
                  <div key={entry.id} className={`history-item ${entry.status}`}>
                    <span className="history-status">
                      {entry.status === 'accepted' ? '✅' : '❌'}
                    </span>
                    <div className="history-info">
                      <strong>{entry.item}</strong>
                      <span>{entry.action}: {entry.suggestion}</span>
                    </div>
                    <span className="history-time">{entry.timestamp}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Owner Reports Tab */}
      {activeTab === 'reports' && (
        <div className="reports-section">
          <div className="section-header">
            <h2>📈 Owner Reports</h2>
            <p>Generate AI-powered business insights and recommendations</p>
          </div>

          <div className="report-controls">
            <button
              className="btn-generate"
              onClick={() => handleGenerateReport('daily')}
              disabled={reportLoading}
            >
              📅 Daily Report
            </button>
            <button
              className="btn-generate"
              onClick={() => handleGenerateReport('weekly')}
              disabled={reportLoading}
            >
              📆 Weekly Report
            </button>
            <button
              className="btn-generate"
              onClick={() => handleGenerateReport('monthly')}
              disabled={reportLoading}
            >
              📊 Monthly Report
            </button>
          </div>

          {reportLoading && (
            <div className="report-loading">
              <div className="loading-spinner"></div>
              <p>Generating AI report...</p>
            </div>
          )}

          {ownerReport && !reportLoading && (
            <div className="report-content">
              {ownerReport.error ? (
                <div className="report-error">
                  <span>⚠️</span>
                  <p>{ownerReport.error}</p>
                </div>
              ) : (
                <>
                  {ownerReport.executive_summary && (
                    <div className="report-section">
                      <h3>📋 Executive Summary</h3>
                      <p>{ownerReport.executive_summary}</p>
                    </div>
                  )}
                  
                  {ownerReport.highlights && ownerReport.highlights.length > 0 && (
                    <div className="report-section highlights">
                      <h3>✨ Highlights</h3>
                      <ul>
                        {ownerReport.highlights.map((highlight, idx) => (
                          <li key={idx}>{highlight}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {ownerReport.concerns && ownerReport.concerns.length > 0 && (
                    <div className="report-section concerns">
                      <h3>⚠️ Areas of Concern</h3>
                      <ul>
                        {ownerReport.concerns.map((concern, idx) => (
                          <li key={idx}>{concern}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {ownerReport.recommendations && ownerReport.recommendations.length > 0 && (
                    <div className="report-section recommendations">
                      <h3>💡 Recommendations</h3>
                      <ul>
                        {ownerReport.recommendations.map((rec, idx) => (
                          <li key={idx}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {!ownerReport && !reportLoading && (
            <div className="empty-state">
              <span className="empty-icon">📊</span>
              <h3>Generate a Report</h3>
              <p>Select a time period above to generate AI-powered business insights.</p>
            </div>
          )}
        </div>
      )}

      {/* Item Detail Modal */}
      {selectedItem && (
        <div className="modal-overlay" onClick={() => setSelectedItem(null)}>
          <div className="modal-content large" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedItem(null)}>
              ×
            </button>
            
            <div className="modal-header">
              <h2>{selectedItem.title}</h2>
              <span
                className="category-badge large"
                style={{ backgroundColor: getCategoryColor(selectedItem.category) }}
              >
                {getCategoryIcon(selectedItem.category)} {selectedItem.category}
              </span>
            </div>

            <div className="item-metrics">
              <div className="metric">
                <span className="metric-label">Price</span>
                <span className="metric-value">${parseFloat(selectedItem.price).toFixed(2)}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Cost</span>
                <span className="metric-value">${parseFloat(selectedItem.cost || 0).toFixed(2)}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Margin</span>
                <span className="metric-value highlight">${parseFloat(selectedItem.margin || 0).toFixed(2)}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Purchases</span>
                <span className="metric-value">{selectedItem.total_purchases || 0}</span>
              </div>
            </div>

            {suggestions ? (
              suggestions.error ? (
                <div className="suggestions-error">
                  <p>⚠️ {suggestions.error}</p>
                </div>
              ) : (
                <div className="suggestions-panel">
                  <h3>🤖 AI Recommendations</h3>
                  
                  {suggestions.priority && (
                    <div className="suggestion-priority">
                      <span className={`priority-indicator ${suggestions.priority.toLowerCase()}`}>
                        Priority: {suggestions.priority}
                      </span>
                    </div>
                  )}

                  {suggestions.suggested_price && (
                    <div className="suggestion-item">
                      <div className="suggestion-header">
                        <span className="suggestion-icon">💰</span>
                        <h4>Pricing Recommendation</h4>
                      </div>
                      <p>
                        Suggested Price: <strong>${suggestions.suggested_price}</strong>
                        {suggestions.suggested_price > selectedItem.price ? (
                          <span className="change-indicator up">↑ Increase</span>
                        ) : suggestions.suggested_price < selectedItem.price ? (
                          <span className="change-indicator down">↓ Decrease</span>
                        ) : null}
                      </p>
                      <div className="suggestion-actions">
                        <button
                          className="btn-accept"
                          onClick={() => handleAcceptSuggestion(
                            selectedItem,
                            `Price: $${suggestions.suggested_price}`,
                            'Applied pricing'
                          )}
                        >
                          ✓ Accept
                        </button>
                        <button
                          className="btn-reject"
                          onClick={() => handleRejectSuggestion(
                            selectedItem,
                            `Price: $${suggestions.suggested_price}`
                          )}
                        >
                          ✗ Reject
                        </button>
                      </div>
                    </div>
                  )}

                  {suggestions.actions && suggestions.actions.length > 0 && (
                    <div className="suggestion-item">
                      <div className="suggestion-header">
                        <span className="suggestion-icon">📋</span>
                        <h4>Recommended Actions</h4>
                      </div>
                      <ul className="actions-list">
                        {suggestions.actions.map((action, idx) => (
                          <li key={idx}>
                            <span>{action}</span>
                            <div className="action-buttons">
                              <button
                                className="btn-accept-small"
                                onClick={() => handleAcceptSuggestion(selectedItem, action, 'Applied action')}
                              >
                                ✓
                              </button>
                              <button
                                className="btn-reject-small"
                                onClick={() => handleRejectSuggestion(selectedItem, action)}
                              >
                                ✗
                              </button>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {suggestions.marketing_tips && suggestions.marketing_tips.length > 0 && (
                    <div className="suggestion-item">
                      <div className="suggestion-header">
                        <span className="suggestion-icon">📢</span>
                        <h4>Marketing Tips</h4>
                      </div>
                      <ul className="tips-list">
                        {suggestions.marketing_tips.map((tip, idx) => (
                          <li key={idx}>{tip}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )
            ) : (
              <div className="loading-suggestions">
                <div className="loading-spinner"></div>
                <p>Loading AI suggestions...</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ManagerDashboard;

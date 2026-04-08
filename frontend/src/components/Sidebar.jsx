import { useState, useEffect } from 'react';
import { getConfig } from '../api/bedrockApi';
import './Sidebar.css';

export default function Sidebar({
  numResults,
  setNumResults,
  searchMode,
  setSearchMode,
  stats,
  onClearChat,
}) {
  const [config, setConfig] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    getConfig()
      .then(setConfig)
      .catch(() => setConfig(null));
  }, []);

  return (
    <>
      <button
        className="sidebar-toggle"
        onClick={() => setIsCollapsed(!isCollapsed)}
        id="sidebar-toggle"
        aria-label="Toggle sidebar"
      >
        {isCollapsed ? '☰' : '✕'}
      </button>

      <aside className={`sidebar glass-strong ${isCollapsed ? 'collapsed' : ''}`} id="app-sidebar">
        {/* Settings Section */}
        <div className="sidebar-section">
          <h3 className="sidebar-heading">⚙️ Settings</h3>

          <div className="setting-group">
            <label className="setting-label" htmlFor="num-results">
              Results to retrieve
              <span className="setting-value">{numResults}</span>
            </label>
            <input
              type="range"
              id="num-results"
              className="setting-slider"
              min="1"
              max="10"
              value={numResults}
              onChange={(e) => setNumResults(Number(e.target.value))}
            />
          </div>

          <div className="setting-group">
            <label className="setting-label" htmlFor="search-mode">
              Mode
            </label>
            <div className="mode-toggle" id="search-mode">
              <button
                className={`mode-btn ${!searchMode ? 'active' : ''}`}
                onClick={() => setSearchMode(false)}
                id="mode-qa"
              >
                💬 Q&A
              </button>
              <button
                className={`mode-btn ${searchMode ? 'active' : ''}`}
                onClick={() => setSearchMode(true)}
                id="mode-search"
              >
                🔍 Search
              </button>
            </div>
          </div>
        </div>

        {/* Stats Section */}
        <div className="sidebar-section">
          <h3 className="sidebar-heading">📊 Session Stats</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-value">{stats.queryCount}</span>
              <span className="stat-label">Queries</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.averageResponseTime}s</span>
              <span className="stat-label">Avg. Time</span>
            </div>
          </div>
        </div>

        {/* Info Section */}
        <div className="sidebar-section">
          <h3 className="sidebar-heading">ℹ️ About</h3>
          <div className="info-list">
            <div className="info-item">
              <span className="info-key">Region</span>
              <span className="info-value">{config?.region || '—'}</span>
            </div>
            <div className="info-item">
              <span className="info-key">Model</span>
              <span className="info-value">{config?.model || '—'}</span>
            </div>
            <div className="info-item">
              <span className="info-key">KB ID</span>
              <span className="info-value info-mono">
                {config?.knowledgeBaseId?.slice(0, 10) || '—'}
              </span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="sidebar-actions">
          <button
            className="clear-btn"
            onClick={onClearChat}
            id="clear-chat-btn"
          >
            🗑️ Clear Chat
          </button>
        </div>
      </aside>
    </>
  );
}

import { useState, useEffect } from 'react';
import { getHealth } from '../api/bedrockApi';
import './Header.css';

export default function Header() {
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  async function checkHealth() {
    try {
      const data = await getHealth();
      setStatus(data.status === 'connected' ? 'connected' : 'error');
    } catch {
      setStatus('disconnected');
    }
  }

  const statusLabels = {
    checking: 'Checking...',
    connected: 'Connected',
    error: 'Error',
    disconnected: 'Disconnected',
  };

  return (
    <header className="header glass-strong" id="app-header">
      <div className="header-left">
        <div className="header-logo">🧠</div>
        <div className="header-title-group">
          <h1 className="header-title">
            <span className="gradient-text">Enterprise Knowledge Base</span>
          </h1>
          <p className="header-subtitle">Powered by Amazon Bedrock RAG</p>
        </div>
      </div>

      <div className="header-right">
        <div className={`status-badge status-${status}`} id="connection-status">
          <span className="status-dot"></span>
          <span className="status-label">{statusLabels[status]}</span>
        </div>
      </div>
    </header>
  );
}

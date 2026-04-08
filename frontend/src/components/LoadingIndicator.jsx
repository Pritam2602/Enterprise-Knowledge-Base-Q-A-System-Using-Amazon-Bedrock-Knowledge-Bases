import './LoadingIndicator.css';

export default function LoadingIndicator() {
  return (
    <div className="loading-indicator" id="loading-indicator">
      <div className="loading-avatar">🤖</div>
      <div className="loading-body">
        <div className="loading-dots">
          <span className="dot"></span>
          <span className="dot"></span>
          <span className="dot"></span>
        </div>
        <span className="loading-text">Searching knowledge base...</span>
      </div>
    </div>
  );
}

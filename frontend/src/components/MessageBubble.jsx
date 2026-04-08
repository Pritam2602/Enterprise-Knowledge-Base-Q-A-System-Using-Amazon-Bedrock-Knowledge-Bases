import CitationCard from './CitationCard';
import './MessageBubble.css';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const isError = message.isError;

  return (
    <div
      className={`message-bubble ${isUser ? 'user' : 'assistant'} ${isError ? 'error' : ''}`}
      style={{ animation: 'fadeIn 0.3s ease' }}
    >
      {/* Avatar */}
      <div className="message-avatar">
        {isUser ? '👤' : '🤖'}
      </div>

      {/* Content */}
      <div className="message-body">
        <div className="message-header">
          <span className="message-role">{isUser ? 'You' : 'Knowledge Base AI'}</span>
          {message.responseTime && (
            <span className="message-time">{message.responseTime}s</span>
          )}
        </div>

        <div className={`message-content ${isError ? 'error-content' : ''}`}>
          {message.content}
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="citations-section">
            <div className="citations-header">
              <span className="citations-icon">📎</span>
              <span className="citations-title">
                Sources ({message.citations.length})
              </span>
            </div>
            <div className="citations-list">
              {message.citations.map((citation, index) => (
                <CitationCard key={index} citation={citation} index={index} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

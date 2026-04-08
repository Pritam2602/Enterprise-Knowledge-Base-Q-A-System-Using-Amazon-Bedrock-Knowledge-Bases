import { useState, useRef, useEffect } from 'react';
import './ChatInput.css';

export default function ChatInput({ onSend, isLoading }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 150) + 'px';
    }
  }, [text]);

  function handleSubmit(e) {
    e.preventDefault();
    if (text.trim() && !isLoading) {
      onSend(text.trim());
      setText('');
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <form className="chat-input-form glass-strong" onSubmit={handleSubmit} id="chat-input-form">
      <div className="chat-input-wrapper">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder="Ask a question about your documents..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
          id="chat-input"
          aria-label="Message input"
        />
        <div className="chat-input-actions">
          {text.length > 0 && (
            <span className="char-count">{text.length}/1000</span>
          )}
          <button
            type="submit"
            className={`send-btn ${text.trim() && !isLoading ? 'active' : ''}`}
            disabled={!text.trim() || isLoading}
            id="send-btn"
            aria-label="Send message"
          >
            {isLoading ? (
              <span className="send-spinner"></span>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            )}
          </button>
        </div>
      </div>
      <p className="input-hint">Press <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line</p>
    </form>
  );
}

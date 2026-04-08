import { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import LoadingIndicator from './LoadingIndicator';
import './ChatWindow.css';

const SUGGESTED_QUESTIONS = [
  "What is the company's leave policy?",
  "How do I submit an expense report?",
  "What are the IT security guidelines?",
  "Tell me about the performance review process",
  "What are the employee benefits?",
];

export default function ChatWindow({ messages, isLoading, onSendMessage }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const isEmpty = messages.length === 0;

  return (
    <div className="chat-window" id="chat-window">
      {isEmpty ? (
        <div className="welcome-screen">
          <div className="welcome-icon">🧠</div>
          <h2 className="welcome-title gradient-text">
            Enterprise Knowledge Base
          </h2>
          <p className="welcome-description">
            Ask any question about your company documents. I'll search through the knowledge base 
            and provide accurate, citation-backed answers.
          </p>
          <div className="suggested-questions">
            <p className="suggested-label">Try asking:</p>
            <div className="suggested-grid">
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  className="suggested-btn glass"
                  onClick={() => onSendMessage(q)}
                  id={`suggested-q-${i}`}
                >
                  <span className="suggested-icon">💡</span>
                  <span className="suggested-text">{q}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="messages-list">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isLoading && <LoadingIndicator />}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}

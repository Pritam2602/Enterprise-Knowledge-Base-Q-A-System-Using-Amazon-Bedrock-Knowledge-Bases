import { useState } from 'react';
import './CitationCard.css';

export default function CitationCard({ citation, index }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const scorePercent = citation.score ? Math.round(citation.score * 100) : null;

  return (
    <div
      className={`citation-card ${isExpanded ? 'expanded' : ''}`}
      onClick={() => setIsExpanded(!isExpanded)}
      id={`citation-${index}`}
    >
      <div className="citation-summary">
        <div className="citation-left">
          <span className="citation-file-icon">📄</span>
          <span className="citation-name">{citation.documentName}</span>
        </div>
        <div className="citation-right">
          {scorePercent !== null && (
            <div className="citation-score">
              <div
                className="citation-score-bar"
                style={{ width: `${scorePercent}%` }}
              />
              <span className="citation-score-text">{scorePercent}%</span>
            </div>
          )}
          <span className={`citation-chevron ${isExpanded ? 'open' : ''}`}>▸</span>
        </div>
      </div>

      {isExpanded && citation.text && (
        <div className="citation-excerpt">
          <p className="citation-excerpt-text">{citation.text}</p>
        </div>
      )}
    </div>
  );
}

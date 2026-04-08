import { useState, useCallback, useRef } from 'react';
import { sendQuery, searchDocuments } from '../api/bedrockApi';

/**
 * Custom hook for managing chat state and interactions.
 * Handles message history, loading states, and API communication.
 */
export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    queryCount: 0,
    totalResponseTime: 0,
  });
  const sessionIdRef = useRef(null);

  /**
   * Send a message and get a RAG response.
   */
  const sendMessage = useCallback(async (text, numResults = 5) => {
    if (!text.trim() || isLoading) return;

    setError(null);

    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await sendQuery(text.trim(), numResults, sessionIdRef.current);

      // Save session ID for multi-turn
      if (response.sessionId) {
        sessionIdRef.current = response.sessionId;
      }

      // Add AI message
      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.answer,
        citations: response.citations || [],
        responseTime: response.responseTime,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, aiMessage]);

      // Update stats
      setStats(prev => ({
        queryCount: prev.queryCount + 1,
        totalResponseTime: prev.totalResponseTime + response.responseTime,
      }));
    } catch (err) {
      setError(err.message);

      // Add error message to chat
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `⚠️ ${err.message}`,
        isError: true,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  /**
   * Perform semantic search without LLM generation.
   */
  const searchOnly = useCallback(async (text, numResults = 5) => {
    if (!text.trim() || isLoading) return;

    setError(null);

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: `🔍 Search: ${text.trim()}`,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await searchDocuments(text.trim(), numResults);

      const searchMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Found ${response.results.length} relevant document chunks:`,
        citations: response.results.map(r => ({
          documentName: r.documentName,
          text: r.text,
          s3Uri: r.s3Uri,
          score: r.score,
        })),
        responseTime: response.responseTime,
        isSearch: true,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, searchMessage]);

      setStats(prev => ({
        queryCount: prev.queryCount + 1,
        totalResponseTime: prev.totalResponseTime + response.responseTime,
      }));
    } catch (err) {
      setError(err.message);
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `⚠️ ${err.message}`,
        isError: true,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  /**
   * Clear all messages and reset session.
   */
  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    sessionIdRef.current = null;
  }, []);

  const averageResponseTime = stats.queryCount > 0
    ? (stats.totalResponseTime / stats.queryCount).toFixed(2)
    : 0;

  return {
    messages,
    isLoading,
    error,
    stats: {
      ...stats,
      averageResponseTime,
    },
    sendMessage,
    searchOnly,
    clearChat,
  };
}

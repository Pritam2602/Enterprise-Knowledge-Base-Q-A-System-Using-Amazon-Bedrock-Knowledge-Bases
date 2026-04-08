import { useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import { useChat } from './hooks/useChat';

export default function App() {
  const [numResults, setNumResults] = useState(5);
  const [searchMode, setSearchMode] = useState(false);

  const {
    messages,
    isLoading,
    stats,
    sendMessage,
    searchOnly,
    clearChat,
  } = useChat();

  function handleSend(text) {
    if (searchMode) {
      searchOnly(text, numResults);
    } else {
      sendMessage(text, numResults);
    }
  }

  return (
    <>
      <Header />
      <div className="app-layout">
        <Sidebar
          numResults={numResults}
          setNumResults={setNumResults}
          searchMode={searchMode}
          setSearchMode={setSearchMode}
          stats={stats}
          onClearChat={clearChat}
        />
        <main className="main-content">
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            onSendMessage={handleSend}
          />
          <ChatInput onSend={handleSend} isLoading={isLoading} />
        </main>
      </div>
    </>
  );
}

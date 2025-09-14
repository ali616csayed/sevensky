import React, { useState, useEffect } from 'react';
import type { Conversation, Message } from './types';
import { chatAPI } from './services/api';
import ConversationList from './components/ConversationList';
import ChatWindow from './components/ChatWindow';

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [currentUserDid, setCurrentUserDid] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const fetchedConversations = await chatAPI.getConversations();
      setConversations(fetchedConversations);
      
      // Set current user DID from the first conversation or a default
      if (fetchedConversations.length > 0) {
        // This is a simplified approach - in a real app you'd get this from auth
        setCurrentUserDid('did:plc:current-user'); // Replace with actual user DID
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectConversation = (conversation: Conversation) => {
    setCurrentConversation(conversation);
  };

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-gray-600">Loading conversations...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-gray-100">
      <ConversationList
        conversations={conversations}
        currentConversationId={currentConversation?.id}
        onSelectConversation={handleSelectConversation}
      />
      
      {currentConversation ? (
        <ChatWindow
          conversation={currentConversation}
          currentUserDid={currentUserDid}
        />
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <div className="text-6xl mb-4">💬</div>
            <h2 className="text-xl font-semibold mb-2">Welcome to SevenSky Chat</h2>
            <p>Select a conversation to start chatting</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

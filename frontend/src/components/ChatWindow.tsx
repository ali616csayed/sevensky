import React, { useState, useEffect } from 'react';
import type { Message, Conversation } from '../types';
import { chatAPI } from '../services/api';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

interface ChatWindowProps {
  conversation: Conversation;
  currentUserDid: string;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ conversation, currentUserDid }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadMessages = async () => {
    try {
      const fetchedMessages = await chatAPI.getMessages(conversation.id);
      setMessages(fetchedMessages);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMessages();
  }, [conversation.id]);

  const handleMessageSent = () => {
    loadMessages();
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-gray-500">Loading messages...</div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="p-4 border-b border-gray-200 bg-white">
        <h3 className="text-lg font-semibold text-gray-800">
          {conversation.members
            .map(member => member.displayName || member.handle)
            .join(', ')}
        </h3>
      </div>
      
      <MessageList messages={messages} currentUserDid={currentUserDid} />
      <MessageInput convoId={conversation.id} onMessageSent={handleMessageSent} />
    </div>
  );
};

export default ChatWindow;

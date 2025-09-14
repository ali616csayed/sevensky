import React from 'react';
import type { Message } from '../types';

interface MessageListProps {
  messages: Message[];
  currentUserDid: string;
}

const MessageList: React.FC<MessageListProps> = ({ messages, currentUserDid }) => {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderImageEmbed = (embed: Message['embed']) => {
    if (!embed?.images || embed.images.length === 0) return null;

    return (
      <div className="mt-2 space-y-2">
        {embed.images.map((img, index) => (
          <div key={index} className="relative">
            <img
              src={`https://bsky.social/xrpc/com.atproto.sync.getBlob?did=${img.image.ref.$link.split('/')[2]}&cid=${img.image.ref.$link.split('/')[3]}`}
              alt={img.alt}
              className="max-w-xs rounded-lg shadow-sm"
              onError={(e) => {
                // Fallback for image loading
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 ? (
        <div className="text-center text-gray-500 mt-8">
          No messages yet. Start a conversation!
        </div>
      ) : (
        messages.map((message) => {
          const isCurrentUser = message.author.did === currentUserDid;
          
          return (
            <div
              key={message.id}
              className={`flex ${isCurrentUser ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  isCurrentUser
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-800'
                }`}
              >
                {!isCurrentUser && (
                  <div className="text-xs font-medium mb-1 opacity-75">
                    {message.author.displayName || message.author.handle}
                  </div>
                )}
                
                <div className="text-sm whitespace-pre-wrap">
                  {message.text}
                </div>
                
                {message.embed && renderImageEmbed(message.embed)}
                
                <div className={`text-xs mt-1 ${
                  isCurrentUser ? 'text-blue-100' : 'text-gray-500'
                }`}>
                  {formatTime(message.createdAt)}
                </div>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
};

export default MessageList;

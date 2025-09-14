import React, { useState, useRef } from 'react';
import { Send, Image, X } from 'lucide-react';
import { chatAPI } from '../services/api';

interface MessageInputProps {
  convoId: string;
  onMessageSent: () => void;
}

const MessageInput: React.FC<MessageInputProps> = ({ convoId, onMessageSent }) => {
  const [text, setText] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() && !image) return;

    setIsLoading(true);
    try {
      await chatAPI.sendMessage({
        convo_id: convoId,
        text: text.trim(),
        image: image || undefined,
      });
      
      setText('');
      setImage(null);
      onMessageSent();
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
      }
      // Validate file size (5MB limit)
      if (file.size > 5 * 1024 * 1024) {
        alert('Image size must be less than 5MB');
        return;
      }
      setImage(file);
    }
  };

  const removeImage = () => {
    setImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2 p-4 border-t bg-white">
      {image && (
        <div className="flex items-center gap-2 p-2 bg-gray-100 rounded-lg">
          <img
            src={URL.createObjectURL(image)}
            alt="Preview"
            className="w-12 h-12 object-cover rounded"
          />
          <span className="flex-1 text-sm text-gray-600 truncate">
            {image.name}
          </span>
          <button
            type="button"
            onClick={removeImage}
            className="p-1 hover:bg-gray-200 rounded"
          >
            <X size={16} />
          </button>
        </div>
      )}
      
      <div className="flex gap-2">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
          disabled={isLoading}
        >
          <Image size={20} />
        </button>
        
        <button
          type="submit"
          disabled={(!text.trim() && !image) || isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Send size={16} />
          )}
        </button>
      </div>
      
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleImageSelect}
        className="hidden"
      />
    </form>
  );
};

export default MessageInput;

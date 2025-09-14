import axios from 'axios';
import type { Message, Conversation, SendMessageRequest } from '../types';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatAPI = {
  // Get conversations
  getConversations: async (): Promise<Conversation[]> => {
    const response = await api.get('/conversations');
    return response.data;
  },

  // Get messages for a conversation
  getMessages: async (convoId: string): Promise<Message[]> => {
    const response = await api.get(`/conversations/${convoId}/messages`);
    return response.data;
  },

  // Send a message
  sendMessage: async (data: SendMessageRequest): Promise<{ message_id: string; success: boolean }> => {
    const formData = new FormData();
    formData.append('convo_id', data.convo_id);
    formData.append('text', data.text);
    
    if (data.image) {
      formData.append('image', data.image);
    }

    const response = await api.post('/send-message-with-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  // Create a new conversation
  createConversation: async (userHandle: string): Promise<{ convo_id: string; success: boolean }> => {
    const response = await api.post('/create-conversation', {
      user_handle: userHandle,
    });
    return response.data;
  },
};

export default api;

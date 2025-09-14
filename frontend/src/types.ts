export interface Message {
  id: string;
  text: string;
  author: {
    did: string;
    handle: string;
    displayName?: string;
    avatar?: string;
  };
  createdAt: string;
  embed?: {
    $type: string;
    images?: Array<{
      image: {
        ref: {
          $link: string;
        };
        mimeType: string;
        size: number;
      };
      alt: string;
    }>;
  };
}

export interface Conversation {
  id: string;
  members: Array<{
    did: string;
    handle: string;
    displayName?: string;
    avatar?: string;
  }>;
  lastMessage?: Message;
  unreadCount?: number;
}

export interface SendMessageRequest {
  convo_id: string;
  text: string;
  image?: File;
}

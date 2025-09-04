// Configuration for the chat application
export const CHAT_EVENT_SOURCE = process.env.REACT_APP_CHAT_BACKEND_URL || 'http://localhost:8000';

// API endpoints
export const API_ENDPOINTS = {
  STREAM: `${CHAT_EVENT_SOURCE}/api/stream`,
  MESSAGES: `${CHAT_EVENT_SOURCE}/api/message`,
};

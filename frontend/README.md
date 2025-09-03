# Chat Room Application

A real-time chat room built with React that connects to a backend via Server-Sent Events (SSE) and REST API.

## Features

- Real-time messaging using Server-Sent Events (SSE)
- Persistent message history
- User identification with auto-generated UUIDs
- Responsive design for mobile and desktop
- Connection status indicator
- Modern, beautiful UI with smooth animations

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure the backend URL:
   - Update `src/config.js` with your backend URL
   - Or set the environment variable `REACT_APP_CHAT_BACKEND_URL`

3. Start the development server:
   ```bash
   npm start
   ```

## Backend API Requirements

The application expects the following backend endpoints:

- `GET /api/message` - Retrieve existing messages
- `POST /api/message` - Send a new message
- `GET /api/stream` - SSE endpoint for real-time updates

## Message Format

Messages should follow this structure:
```json
{
  "id": "uuid",
  "text": "message content",
  "userName": "user's name",
  "userId": "user's uuid",
  "timestamp": "ISO timestamp"
}
```

## Environment Variables

- `REACT_APP_CHAT_BACKEND_URL` - Backend server URL (defaults to http://localhost:3001)

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

## Technologies Used

- React 18
- CSS3 with modern features
- Server-Sent Events (SSE)
- Fetch API
- UUID generation

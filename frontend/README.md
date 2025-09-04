
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
  "content": "message content",
  "userName": "user's id in the format of uuid",
  "file": "url of uploaded file"
}
```

## Environment Variables

- `REACT_APP_CHAT_BACKEND_URL` - Backend server URL (defaults to http://localhost:3001)



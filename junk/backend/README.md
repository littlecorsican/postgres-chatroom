# Backend with Prisma

This backend uses Prisma ORM with PostgreSQL for the chatroom application, including real-time PostgreSQL listeners for message changes, a modular route structure, and JWT authentication.

## Project Structure

```
backend/
├── app.js                 # Main application entry point
├── routes/                # Route modules
│   ├── index.js          # Main router that combines all routes
│   ├── health.js         # Health check endpoints
│   ├── test.js           # Testing endpoints
│   ├── messages.js       # Message CRUD operations
│   └── users.js          # User management operations
├── services/              # Business logic services
│   └── postgresListener.js # PostgreSQL listener service
├── middleware/            # Express middleware
│   └── errorHandler.js   # Error handling middleware
├── utils/                 # Utility functions
│   └── auth.js           # JWT authentication utilities
├── examples/              # Usage examples
│   └── messageOperations.js
└── prisma/               # Database schema and migrations
    └── schema.prisma
```

## Environment Variables

Create a `.env` file in the backend directory with:

```env
# Database connection
DATABASE_URL="postgresql://username:password@localhost:5432/chatroom_db?schema=public"

# JWT Authentication
AUTH_SECRET_KEY="your-super-secret-jwt-key-here"
```

## JWT Authentication

The application uses JWT (JSON Web Tokens) for secure authentication and authorization.

### Features

- **Secure Token Generation**: Uses environment variable `AUTH_SECRET_KEY` for signing
- **Token Expiration**: Default 24-hour expiration with automatic refresh
- **Multiple Token Sources**: Supports Authorization header, x-auth-token header, and query parameters
- **Role-Based Access Control**: Extensible permission system
- **Ownership Verification**: Ensures users can only access their own resources
- **Automatic Token Refresh**: Refreshes tokens before expiration

### Token Format

```json
{
  "uuid": "user-uuid",
  "name": "User Name",
  "iat": 1704067200,
  "exp": 1704153600,
  "iss": "chatroom-backend",
  "aud": "chatroom-users"
}
```

### Authentication Headers

```bash
# Bearer token (recommended)
Authorization: Bearer <jwt-token>

# Custom header
x-auth-token: <jwt-token>

# Query parameter
GET /api/users?token=<jwt-token>
```

## Database Schema

### Tables

1. **users** - User information
   - `uuid` (UUID, Primary Key)
   - `name` (VARCHAR(25))
   - `created_date` (DATETIME)
   - `updated_at` (DATETIME)

2. **groups** - Chat groups
   - `uuid` (UUID, Primary Key)
   - `created_date` (DATETIME)
   - `updated_at` (DATETIME)

3. **messages** - Chat messages
   - `id` (INT, Primary Key, Auto Increment)
   - `group_uuid` (UUID, Foreign Key to groups.uuid)
   - `content` (TEXT - supports emoticons and Unicode)
   - `file` (VARCHAR(255), optional)
   - `created_date` (DATETIME)
   - `updated_at` (DATETIME)
   - `is_deleted` (BOOLEAN)
   - `sender_uuid` (UUID, Foreign Key to users.uuid)

4. **group_participants** - Group membership
   - `id` (INT, Primary Key, Auto Increment)
   - `group_uuid` (UUID, Foreign Key to groups.uuid)
   - `user_uuid` (UUID, Foreign Key to users.uuid)
   - `joined_at` (DATETIME)

## API Endpoints

### Base URL: `/api`

#### Health & Status
- `GET /api/health` - Basic health check
- `GET /api/health/detailed` - Detailed system health information

#### Testing
- `POST /api/test/notification` - Test PostgreSQL listener
- `GET /api/test/listener-status` - Check listener status
- `POST /api/test/simulate-message` - Create test message
- `GET /api/test/auth-test` - Test JWT authentication (Auth Required)
- `POST /api/test/generate-test-token` - Generate test JWT token

#### Users
- `POST /api/users` - Create new user (Public)
- `POST /api/users/login` - Login with username (Public)
- `GET /api/users` - Get all users (Auth Required)
- `GET /api/users/:uuid` - Get specific user with details (Auth Required)
- `PUT /api/users/:uuid` - Update user (Auth + Ownership Required)
- `DELETE /api/users/:uuid` - Delete user (Auth + Ownership Required)
- `GET /api/users/:uuid/groups` - Get user's groups (Auth + Ownership Required)
- `GET /api/users/:uuid/messages` - Get user's messages (Auth + Ownership Required)
- `GET /api/users/profile/me` - Get current user profile (Auth Required)

#### Messages
- `GET /api/messages/group/:groupUuid` - Get messages for a group
- `GET /api/messages/:id` - Get specific message
- `POST /api/messages` - Create new message
- `PUT /api/messages/:id` - Update message
- `DELETE /api/messages/:id` - Soft delete message
- `GET /api/messages/search/:groupUuid` - Search messages in group

## Authentication Examples

### 1. Create a User and Get Token
```bash
POST /api/users
Body: { "name": "John Doe" }

Response:
{
  "message": "User created successfully",
  "data": { "uuid": "...", "name": "John Doe" },
  "token": "jwt-token-here"
}
```

### 2. Login and Get Token
```bash
POST /api/users/login
Body: { "name": "John Doe" }

Response:
{
  "message": "Login successful",
  "data": { "uuid": "...", "name": "John Doe" },
  "token": "jwt-token-here"
}
```

### 3. Use Token for Authenticated Requests
```bash
GET /api/users/profile/me
Headers: Authorization: Bearer <jwt-token>

Response:
{
  "user": { "uuid": "...", "name": "John Doe" }
}
```

### 4. Test Authentication
```bash
GET /api/test/auth-test
Headers: Authorization: Bearer <jwt-token>

Response:
{
  "message": "Authentication successful",
  "user": { "uuid": "...", "name": "John Doe" }
}
```

## Real-Time PostgreSQL Listener

The application includes a PostgreSQL listener service that automatically detects changes to the messages table in real-time using PostgreSQL's `NOTIFY/LISTEN` mechanism.

### Features

- **Automatic Triggers**: Database triggers automatically notify on INSERT, UPDATE, and DELETE operations
- **Real-Time Updates**: Instant notification when messages change
- **Event-Driven Architecture**: Uses Node.js event emitter pattern
- **Automatic Reconnection**: Handles connection failures gracefully
- **JSON Payloads**: Rich notification data including operation type and message details

### How It Works

1. **Database Triggers**: PostgreSQL triggers fire on message table changes
2. **Notifications**: Triggers send JSON payloads via `pg_notify()`
3. **Listener Service**: Node.js service listens to the notification channel
4. **Event Emission**: Changes are emitted as events for real-time processing

### Use Cases

- **WebSocket Broadcasting**: Send real-time updates to connected clients
- **Cache Invalidation**: Automatically invalidate cached data
- **Push Notifications**: Notify users of new messages
- **Audit Logging**: Track all message changes
- **Real-Time Analytics**: Monitor message activity

## Setup Instructions

### 1. Install Dependencies
```bash
npm install
```

### 2. Environment Configuration
Create a `.env` file in the backend directory with your database connection and JWT secret:
```env
DATABASE_URL="postgresql://username:password@localhost:5432/chatroom_db?schema=public"
AUTH_SECRET_KEY="your-super-secret-jwt-key-here"
```

### 3. Database Setup
```bash
# Generate Prisma client
npm run db:generate

# Push schema to database (creates tables and triggers)
npm run db:push

# Or use migrations for production
npm run db:migrate
```

### 4. Start the Server
```bash
npm run dev
```

## Available Scripts

- `npm run dev` - Start the development server
- `npm run db:generate` - Generate Prisma client
- `npm run db:push` - Push schema changes to database
- `npm run db:migrate` - Create and apply database migrations
- `npm run db:studio` - Open Prisma Studio (database GUI)

## PostgreSQL Listener API

### Event: `message_change`

The listener emits a `message_change` event whenever a message is modified:

```javascript
const PostgresListener = require('./services/postgresListener');

const listener = new PostgresListener();
await listener.connect();

listener.on('message_change', (data) => {
  console.log('Message changed:', data);
  // data.operation: 'INSERT', 'UPDATE', or 'DELETE'
  // data contains all message fields and metadata
});
```

### Example Payload

```json
{
  "operation": "INSERT",
  "table": "messages",
  "id": 1,
  "group_uuid": "uuid-here",
  "sender_uuid": "user-uuid-here",
  "content": "Hello, world! 👋",
  "file": null,
  "created_date": "2024-01-01T00:00:00.000Z",
  "is_deleted": false
}
```

## Examples

See `examples/messageOperations.js` for complete usage examples including:
- Basic message operations
- WebSocket integration
- Cache invalidation
- Push notifications

## Features

- **Modular Architecture**: Clean separation of routes, services, and middleware
- **JWT Authentication**: Secure token-based authentication system
- **Role-Based Access Control**: Extensible permission system
- **Ownership Verification**: Users can only access their own resources
- **Emoticon Support**: The `content` field uses TEXT type which supports all Unicode characters including emoticons
- **Real-Time Updates**: PostgreSQL listener for instant change detection
- **RESTful API**: Comprehensive message and user CRUD operations
- **Error Handling**: Consistent error responses with proper HTTP status codes
- **Relationships**: Proper foreign key relationships between all tables
- **Indexes**: Performance indexes on frequently queried fields
- **Cascade Deletes**: Automatic cleanup when users or groups are deleted
- **Unique Constraints**: Prevents duplicate group participants and user names
- **Timestamps**: Automatic created_date and updated_at tracking
- **Soft Deletes**: Messages can be marked as deleted without losing data
- **Automatic Reconnection**: Listener service handles connection failures gracefully
- **Search Functionality**: Full-text search within group messages and user names
- **Pagination**: Built-in pagination for large message and user lists
- **User Management**: Complete user lifecycle management with validation
- **Data Integrity**: Prevents deletion of users with existing data
- **Token Refresh**: Automatic JWT token refresh before expiration

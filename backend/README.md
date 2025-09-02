# Starlette Chatroom Backend

A high-performance ASGI backend application built with Starlette, featuring real-time messaging, PostgreSQL integration, and Redis pub/sub.

## Features

- **ASGI Framework**: Built with Starlette for high-performance async web applications
- **Real-time Streaming**: Server-Sent Events (SSE) endpoint for live message updates
- **PostgreSQL Integration**: SQLAlchemy ORM with async support
- **Redis Pub/Sub**: Real-time message broadcasting
- **PostgreSQL Listener**: Automatic database change notifications
- **Cursor Pagination**: Efficient message retrieval with cursor-based pagination
- **Multi-language Support**: Full UTF-8 support for international characters and emoticons

## Architecture

```
Client → Starlette App → PostgreSQL
              ↓
           Redis Pub/Sub
              ↓
        PostgreSQL Listener
```

## Prerequisites

- Docker and Docker Compose
- Python 3.8+
- pip

## Quick Start

1. **Clone and navigate to the project directory**
   ```bash
   cd backend
   ```

2. **Set up environment configuration**
   ```bash
   python setup_env.py
   ```
   This will create a `.env` file with default values. Review and modify as needed.

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

The application will be available at `http://localhost:8000`

## API Endpoints

### GET /message
Retrieve paginated messages with cursor-based pagination.

**Query Parameters:**
- `cursor` (optional): ISO timestamp for pagination
- `limit` (optional): Number of messages to return (default: 20, max: 100)

**Example:**
```bash
curl "http://localhost:8000/message?limit=10"
```

**Response:**
```json
{
  "messages": [
    {
      "id": 1,
      "content": "Hello, world! 👋",
      "file": null,
      "created_date": "2024-01-01T12:00:00Z",
      "sender_id": "123e4567-e89b-12d3-a456-426614174000"
    }
  ],
  "next_cursor": "2024-01-01T11:59:00Z",
  "has_more": true
}
```

### POST /message
Create a new message.

**Request Body:**
```json
{
  "content": "Hello, world! 👋",
  "file": "document.pdf",
  "sender_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/message" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello!", "sender_id": "123e4567-e89b-12d3-a456-426614174000"}'
```

### GET /stream
Server-Sent Events endpoint for real-time message streaming.

**Example:**
```bash
curl -N "http://localhost:8000/stream"
```

**Response (SSE format):**
```
data: {"type": "connected", "message": "Connected to message stream"}

data: {"type": "new_message", "data": {"operation": "INSERT", "id": 1, "content": "Hello!", ...}}
```

## Database Schema

### messages table
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    file VARCHAR(50),
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sender_id UUID NOT NULL
);
```

**Features:**
- `content`: TEXT field supporting unlimited length and UTF-8 characters
- `file`: Optional file reference (max 50 characters)
- `created_date`: Automatic timestamp with timezone
- `sender_id`: UUID for user identification
- Indexes on `created_date` and `sender_id` for performance

## Environment Configuration

The application uses environment variables for configuration. A setup script is provided to help you get started:

### Automatic Setup
```bash
python setup_env.py
```

This will create a `.env` file from `env.example` with default values.

### Manual Configuration

Environment variables can be set in `.env` file or directly:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/chatroom

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# App
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

## Real-time Features

### PostgreSQL Listener
- Automatically monitors the `messages` table for changes
- Creates database triggers for INSERT, UPDATE, and DELETE operations
- Publishes changes to Redis channels:
  - `new_messages`: New message notifications
  - `updated_messages`: Message update notifications
  - `deleted_messages`: Message deletion notifications

### Redis Pub/Sub
- Handles real-time message broadcasting
- Supports multiple subscribers
- Efficient message delivery

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Structure
```
├── main.py              # Main Starlette application
├── database.py          # SQLAlchemy models and database setup
├── redis_client.py      # Redis client with connection management
├── postgres_listener.py # PostgreSQL change listener
├── models.py            # Pydantic models for validation
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker services (Redis + PostgreSQL)
└── init.sql            # Database initialization script
```

## Performance Features

- **Async/Await**: Full asynchronous support for high concurrency
- **Connection Pooling**: Efficient database and Redis connection management
- **Cursor Pagination**: Scalable message retrieval
- **Indexed Queries**: Optimized database performance
- **Streaming Responses**: Memory-efficient real-time updates

## Security Considerations

- CORS middleware enabled for cross-origin requests
- Input validation with Pydantic models
- SQL injection protection through SQLAlchemy ORM
- UUID validation for sender identification

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Ensure PostgreSQL container is running: `docker-compose ps`
   - Check database credentials in `config.py`

2. **Redis Connection Failed**
   - Ensure Redis container is running: `docker-compose ps`
   - Check Redis host/port configuration

3. **Port Already in Use**
   - Change port in `config.py` or stop conflicting services
   - Use different ports in `docker-compose.yml`

### Logs
```bash
# View application logs
python main.py

# View Docker service logs
docker-compose logs -f postgres
docker-compose logs -f redis
```

## License

MIT License



uvicorn main:app --host 0.0.0.0 --port 8000
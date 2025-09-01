# Chat Room API - Starlette ASGI Application

A modern, async chat room API built with Starlette, SQLAlchemy, and PostgreSQL.

## Features

- **ASGI Architecture**: Built on Starlette for high-performance async operations
- **PostgreSQL Database**: Uses SQLAlchemy with async support
- **Redis Integration**: Real-time messaging with pub/sub and caching
- **JWT Authentication**: Secure user authentication and authorization
- **Real-time Streaming**: Server-Sent Events (SSE) for live message updates
- **RESTful API**: Clean, intuitive API endpoints with pagination
- **Soft Delete**: Messages are soft-deleted for data integrity

## Database Schema

### Users
- `uuid`: Unique identifier (primary key)
- `name`: User's name (max 25 characters)
- `created_date`: Account creation timestamp
- `updated_at`: Last update timestamp

### Groups
- `uuid`: Unique identifier (primary key)
- `created_date`: Group creation timestamp
- `updated_at`: Last update timestamp

### Messages
- `id`: Auto-incrementing ID (primary key)
- `group_uuid`: Group this message belongs to
- `content`: Message text content
- `file`: Optional file attachment path/URL
- `created_date`: Message creation timestamp
- `updated_at`: Last edit timestamp
- `is_deleted`: Soft delete flag
- `sender_uuid`: User who sent the message

### Group Participants
- `id`: Auto-incrementing ID (primary key)
- `group_uuid`: Group reference
- `user_uuid`: User reference
- `joined_at`: When user joined the group

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd postgres-chatroom/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your database credentials
   ```

5. **Create PostgreSQL database**
   ```sql
   CREATE DATABASE chatroom;
   ```

6. **Start services with Docker Compose (Recommended)**
   ```bash
   # Copy environment file and update credentials
   cp env.example .env
   # Edit .env with your secure passwords
   
   # Start PostgreSQL and Redis
   docker-compose up -d
   
   # Or start services individually
   docker-compose up -d postgres
   docker-compose up -d redis
   ```
   
   **Alternative: Manual setup**
   ```bash
   # Start Redis server
   redis-server
   # or using Docker
   docker run -d -p 6379:6379 redis:6-alpine
   
   # Start PostgreSQL
   docker run -d -p 5432:5432 \
     -e POSTGRES_DB=chatroom \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=your_password \
     postgres:15-alpine
   ```

8. **Run the application**
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info

### Users
- `GET /users` - Get all users
- `GET /users/{uuid}` - Get specific user
- `PUT /users/me` - Update current user
- `DELETE /users/me` - Delete current user
- `GET /users/{uuid}/messages` - Get user's messages
- `GET /users/{uuid}/groups` - Get user's groups

### Groups
- `POST /groups` - Create new group
- `GET /groups` - Get all groups
- `GET /groups/{uuid}` - Get specific group
- `DELETE /groups/{uuid}` - Delete group
- `POST /groups/{uuid}/join` - Join group
- `POST /groups/{uuid}/leave` - Leave group
- `GET /groups/{uuid}/participants` - Get group participants
- `GET /groups/{uuid}/messages` - Get group messages

### Messages
- `POST /messages` - Send message
- `GET /messages` - Get messages with pagination and filtering
- `GET /messages/search` - Search messages
- `GET /messages/{id}` - Get specific message
- `PUT /messages/{id}` - Edit message
- `DELETE /messages/{id}` - Delete message

### Real-time Streaming (SSE)
- `GET /stream/group?group_uuid={uuid}` - Stream messages for specific group
- `GET /stream/all` - Stream messages from all user's groups
- `GET /stream/health` - Redis connection health check

## Usage Examples

### Register a User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "john_doe"}'
```

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name": "john_doe"}'
```

### Create a Group
```bash
curl -X POST http://localhost:8000/groups \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Send a Message
```bash
curl -X POST http://localhost:8000/messages \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, world!",
    "group_uuid": "GROUP_UUID_HERE"
  }'
```

### Get Messages with Pagination
```bash
curl "http://localhost:8000/messages?page=1&per_page=20&group_uuid=GROUP_UUID_HERE" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Stream Messages (SSE)
```bash
# Stream messages for a specific group
curl "http://localhost:8000/stream/group?group_uuid=GROUP_UUID_HERE" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Accept: text/event-stream"

# Stream messages from all groups
curl "http://localhost:8000/stream/all" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Accept: text/event-stream"
```

## Database Migrations

The application uses SQLAlchemy's `create_all()` for automatic table creation. For production use, consider using Alembic for proper database migrations.

## Development

### Running Tests
```bash
# Add pytest to requirements.txt and run:
pytest
```

### Code Formatting
```bash
# Add black to requirements.txt and run:
black .
```

### Linting
```bash
# Add flake8 to requirements.txt and run:
flake8 .
```

## Docker Compose

The project includes a `docker-compose.yml` file for easy development setup:

### Quick Start
```bash
# Copy environment file
cp env.example .env

# Edit .env with your credentials
# POSTGRES_PASSWORD=your_secure_password
# REDIS_PASSWORD=your_redis_password

# Start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: This will delete all data)
docker-compose down -v
```

### Service Details
- **PostgreSQL 15**: Database with persistent volume storage
- **Redis 7**: In-memory cache with authentication
- **Health Checks**: Both services include health monitoring
- **Networking**: Services communicate via internal network
- **Volumes**: Data persists between container restarts

### Environment Variables
The following environment variables are used by Docker Compose:
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_PORT`: External PostgreSQL port
- `REDIS_PASSWORD`: Redis authentication password
- `REDIS_PORT`: External Redis port

## Production Deployment

1. **Set production environment variables**
   - `DEBUG=False`
   - Strong `SECRET_KEY`
   - Production database URL

2. **Use production ASGI server**
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
   ```

3. **Set up reverse proxy** (Nginx/Apache)

4. **Configure SSL/TLS**

5. **Set up monitoring and logging**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions and support, please open an issue on GitHub.

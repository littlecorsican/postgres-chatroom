# Backend with Prisma

This backend uses Prisma ORM with PostgreSQL for the chatroom application.

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

## Setup Instructions

### 1. Install Dependencies
```bash
npm install
```

### 2. Environment Configuration
Create a `.env` file in the backend directory with your database connection:
```env
DATABASE_URL="postgresql://username:password@localhost:5432/chatroom_db?schema=public"
```

### 3. Database Setup
```bash
# Generate Prisma client
npm run db:generate

# Push schema to database (creates tables)
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

## API Endpoints

- `GET /` - Basic hello world
- `GET /health` - Health check with database connection test

## Features

- **Emoticon Support**: The `content` field uses TEXT type which supports all Unicode characters including emoticons
- **Relationships**: Proper foreign key relationships between all tables
- **Indexes**: Performance indexes on frequently queried fields
- **Cascade Deletes**: Automatic cleanup when users or groups are deleted
- **Unique Constraints**: Prevents duplicate group participants
- **Timestamps**: Automatic created_date and updated_at tracking

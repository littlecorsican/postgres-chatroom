-- Create database with proper encoding for international characters and emoticons
-- Note: Database name will be set by POSTGRES_DB environment variable
-- This script will run after the database is created by Docker

-- Create messages table
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    file VARCHAR(50),
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sender_id UUID NOT NULL
);

-- Create index on created_date for efficient cursor pagination
CREATE INDEX idx_messages_created_date ON messages(created_date);

-- Create index on sender_id for efficient queries
CREATE INDEX idx_messages_sender_id ON messages(sender_id);

-- Enable row level security (optional)
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- PostgreSQL initialization script for Chat Room API
-- This script runs when the PostgreSQL container starts for the first time

-- Create database if it doesn't exist
-- Note: The database is already created by POSTGRES_DB environment variable
-- This script can be used for additional setup if needed

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- You can add additional initialization commands here
-- For example, creating additional schemas, users, or initial data

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL initialization completed successfully';
END $$;

import asyncio
import asyncpg
import json
from typing import Optional
from config import Config
from redis_client import redis_client

class PostgresListener:
    def __init__(self):
        self.connection: Optional[asyncpg.Connection] = None
        self.is_listening = False
        
    async def connect(self):
        """Connect to PostgreSQL"""
        try:
            self.connection = await asyncpg.connect(
                host=Config.POSTGRES_HOST.replace('localhost', '127.0.0.1'),  # Use IP for asyncpg
                port=Config.POSTGRES_PORT,
                user=Config.POSTGRES_USER,
                password=Config.POSTGRES_PASSWORD,
                database=Config.POSTGRES_DB
            )
            print("Connected to PostgreSQL for listening")
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from PostgreSQL"""
        if self.connection:
            await self.connection.close()
            self.connection = None
            print("Disconnected from PostgreSQL")
    
    async def create_notify_function(self):
        """Create a function to notify on table changes"""
        try:
            await self.connection.execute("""
                CREATE OR REPLACE FUNCTION notify_message_change()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF TG_OP = 'INSERT' THEN
                        PERFORM pg_notify('message_changes', json_build_object(
                            'operation', TG_OP,
                            'id', NEW.id,
                            'content', NEW.content,
                            'file', NEW.file,
                            'created_date', NEW.created_date,
                            'sender_id', NEW.sender_id
                        )::text);
                        RETURN NEW;
                    ELSIF TG_OP = 'UPDATE' THEN
                        PERFORM pg_notify('message_changes', json_build_object(
                            'operation', TG_OP,
                            'id', NEW.id,
                            'content', NEW.content,
                            'file', NEW.file,
                            'created_date', NEW.created_date,
                            'sender_id', NEW.sender_id
                        )::text);
                        RETURN NEW;
                    ELSIF TG_OP = 'DELETE' THEN
                        PERFORM pg_notify('message_changes', json_build_object(
                            'operation', TG_OP,
                            'id', OLD.id
                        )::text);
                        RETURN OLD;
                    END IF;
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Create trigger if it doesn't exist
            await self.connection.execute("""
                DROP TRIGGER IF EXISTS messages_notify_trigger ON messages;
                CREATE TRIGGER messages_notify_trigger
                AFTER INSERT OR UPDATE OR DELETE ON messages
                FOR EACH ROW EXECUTE FUNCTION notify_message_change();
            """)
            
            print("Created notify function and trigger")
        except Exception as e:
            print(f"Failed to create notify function: {e}")
            # Continue anyway as the trigger might already exist
    
    async def listen_for_changes(self):
        """Listen for PostgreSQL notifications"""
        if not self.connection:
            await self.connect()
        
        await self.create_notify_function()
        
        # Listen for notifications
        await self.connection.add_listener('message_changes', self.handle_notification)
        self.is_listening = True
        print("Listening for PostgreSQL notifications on 'message_changes' channel")
        
        # Keep the connection alive
        while self.is_listening:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
    
    async def handle_notification(self, connection, pid, channel, payload):
        """Handle PostgreSQL notifications and publish to Redis"""
        try:
            data = json.loads(payload)
            operation = data.get('operation')
            
            if operation == 'INSERT':
                # Publish new message to Redis
                await redis_client.publish('new_messages', payload)
                print(f"Published new message {data.get('id')} to Redis")
            elif operation == 'UPDATE':
                # Publish updated message to Redis
                await redis_client.publish('updated_messages', payload)
                print(f"Published updated message {data.get('id')} to Redis")
            elif operation == 'DELETE':
                # Publish deleted message to Redis
                await redis_client.publish('deleted_messages', payload)
                print(f"Published deleted message {data.get('id')} to Redis")
                
        except Exception as e:
            print(f"Error handling notification: {e}")
    
    async def start(self):
        """Start listening for PostgreSQL changes"""
        try:
            await self.listen_for_changes()
        except Exception as e:
            print(f"Error in PostgreSQL listener: {e}")
            await self.disconnect()
    
    async def stop(self):
        """Stop listening for PostgreSQL changes"""
        self.is_listening = False
        await self.disconnect()

# Global PostgreSQL listener instance
postgres_listener = PostgresListener()

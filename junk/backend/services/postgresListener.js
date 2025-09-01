const { Client } = require('pg');
const { PrismaClient } = require('@prisma/client');

class PostgresListener {
  constructor() {
    this.prisma = new PrismaClient();
    this.client = null;
    this.isListening = false;
    this.listeners = new Map();
  }

  async connect() {
    try {
      // Get connection string from Prisma
      const connectionString = process.env.DATABASE_URL;
      
      this.client = new Client({
        connectionString,
        // Enable notifications
        application_name: 'chatroom_listener'
      });

      await this.client.connect();
      console.log('PostgreSQL listener connected successfully');
      
      // Set up the trigger function and trigger if they don't exist
      await this.setupTriggers();
      
      // Start listening
      await this.startListening();
      
    } catch (error) {
      console.error('Failed to connect PostgreSQL listener:', error);
      throw error;
    }
  }

  async setupTriggers() {
    try {
      // Create the notification function if it doesn't exist
      const createFunctionQuery = `
        CREATE OR REPLACE FUNCTION notify_message_change()
        RETURNS TRIGGER AS $$
        DECLARE
          payload JSON;
        BEGIN
          -- Create payload with operation type and data
          IF TG_OP = 'INSERT' THEN
            payload = json_build_object(
              'operation', TG_OP,
              'table', TG_TABLE_NAME,
              'id', NEW.id,
              'group_uuid', NEW.group_uuid,
              'sender_uuid', NEW.sender_uuid,
              'content', NEW.content,
              'file', NEW.file,
              'created_date', NEW.created_date,
              'is_deleted', NEW.is_deleted
            );
          ELSIF TG_OP = 'UPDATE' THEN
            payload = json_build_object(
              'operation', TG_OP,
              'table', TG_TABLE_NAME,
              'id', NEW.id,
              'group_uuid', NEW.group_uuid,
              'sender_uuid', NEW.sender_uuid,
              'content', NEW.content,
              'file', NEW.file,
              'created_date', NEW.created_date,
              'is_deleted', NEW.is_deleted,
              'old_id', OLD.id,
              'old_content', OLD.content,
              'old_is_deleted', OLD.is_deleted
            );
          ELSIF TG_OP = 'DELETE' THEN
            payload = json_build_object(
              'operation', TG_OP,
              'table', TG_TABLE_NAME,
              'id', OLD.id,
              'group_uuid', OLD.group_uuid,
              'sender_uuid', OLD.sender_uuid
            );
          END IF;

          -- Send notification
          PERFORM pg_notify('message_changes', payload::text);
          RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
      `;

      // Create the trigger if it doesn't exist
      const createTriggerQuery = `
        DROP TRIGGER IF EXISTS messages_notify_trigger ON messages;
        CREATE TRIGGER messages_notify_trigger
        AFTER INSERT OR UPDATE OR DELETE ON messages
        FOR EACH ROW EXECUTE FUNCTION notify_message_change();
      `;

      await this.client.query(createFunctionQuery);
      await this.client.query(createTriggerQuery);
      
      console.log('PostgreSQL triggers set up successfully');
    } catch (error) {
      console.error('Failed to set up triggers:', error);
      throw error;
    }
  }

  async startListening() {
    try {
      // Listen to the notification channel
      await this.client.query('LISTEN message_changes');
      this.isListening = true;
      
      console.log('Started listening to message_changes channel');
      
      // Set up event handler for notifications
      this.client.on('notification', (msg) => {
        this.handleNotification(msg);
      });

      // Handle connection errors
      this.client.on('error', (err) => {
        console.error('PostgreSQL listener error:', err);
        this.reconnect();
      });

      // Handle connection end
      this.client.on('end', () => {
        console.log('PostgreSQL listener connection ended');
        this.isListening = false;
        this.reconnect();
      });

    } catch (error) {
      console.error('Failed to start listening:', error);
      throw error;
    }
  }

  handleNotification(msg) {
    try {
      const payload = JSON.parse(msg.payload);
      console.log('Received notification:', payload);
      
      // Emit to registered listeners
      this.emit('message_change', payload);
      
    } catch (error) {
      console.error('Failed to parse notification payload:', error);
    }
  }

  // Event emitter methods
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in event callback:', error);
        }
      });
    }
  }

  // Remove specific listener
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  // Remove all listeners for an event
  removeAllListeners(event) {
    if (event) {
      this.listeners.delete(event);
    } else {
      this.listeners.clear();
    }
  }

  async reconnect() {
    if (this.isListening) return;
    
    console.log('Attempting to reconnect PostgreSQL listener...');
    
    try {
      if (this.client) {
        await this.client.end();
      }
      
      // Wait a bit before reconnecting
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      await this.connect();
    } catch (error) {
      console.error('Reconnection failed:', error);
      // Try again after a longer delay
      setTimeout(() => this.reconnect(), 10000);
    }
  }

  async disconnect() {
    try {
      if (this.client) {
        await this.client.query('UNLISTEN message_changes');
        await this.client.end();
        this.isListening = false;
        console.log('PostgreSQL listener disconnected');
      }
    } catch (error) {
      console.error('Error disconnecting PostgreSQL listener:', error);
    }
  }

  // Test method to manually trigger a notification
  async testNotification() {
    try {
      await this.client.query(`
        SELECT pg_notify('message_changes', '{"operation": "TEST", "table": "messages", "message": "Test notification"}');
      `);
      console.log('Test notification sent');
    } catch (error) {
      console.error('Failed to send test notification:', error);
    }
  }
}

module.exports = PostgresListener;

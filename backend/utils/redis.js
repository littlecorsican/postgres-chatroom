const redis = require('redis');

class RedisHelper {
  constructor() {
    this.client = null;
    this.publisher = null;
    this.subscriber = null;
  }

  /**
   * Connect to Redis
   * @param {Object} options - Redis connection options (overrides .env variables)
   * @param {string} options.host - Redis host (overrides REDIS_HOST)
   * @param {string} options.port - Redis port (overrides REDIS_PORT)
   * @param {string} options.password - Redis password (overrides REDIS_PASSWORD)
   * @param {number} options.db - Redis database number (overrides REDIS_DB)
   */
  async connect(options = {}) {
    const config = {
      host: options.host || process.env.REDIS_HOST || 'localhost',
      port: parseInt(options.port || process.env.REDIS_PORT || '6379'),
      password: options.password || process.env.REDIS_PASSWORD || undefined,
      db: parseInt(options.db || process.env.REDIS_DB || '0'),
      retry_strategy: (times) => {
        const delay = Math.min(times * 50, 2000);
        return delay;
      }
    };

    try {
      // Create main client
      this.client = redis.createClient(config);
      
      // Create publisher client
      this.publisher = redis.createClient(config);
      
      // Create subscriber client
      this.subscriber = redis.createClient(config);

      // Set up event handlers for main client
      this.client.on('error', (err) => {
        console.error('Redis Client Error:', err);
      });

      this.client.on('connect', () => {
        console.log('Redis Client Connected');
      });

      this.client.on('ready', () => {
        console.log('Redis Client Ready');
      });

      // Set up event handlers for publisher
      this.publisher.on('error', (err) => {
        console.error('Redis Publisher Error:', err);
      });

      // Set up event handlers for subscriber
      this.subscriber.on('error', (err) => {
        console.error('Redis Subscriber Error:', err);
      });

      // Connect all clients
      await this.client.connect();
      await this.publisher.connect();
      await this.subscriber.connect();

      console.log('All Redis clients connected successfully');
    } catch (error) {
      console.error('Failed to connect to Redis:', error);
      throw error;
    }
  }

  /**
   * Disconnect from Redis
   */
  async disconnect() {
    try {
      if (this.client) {
        await this.client.quit();
        this.client = null;
      }
      if (this.publisher) {
        await this.publisher.quit();
        this.publisher = null;
      }
      if (this.subscriber) {
        await this.subscriber.quit();
        this.subscriber = null;
      }
      console.log('All Redis clients disconnected');
    } catch (error) {
      console.error('Error disconnecting from Redis:', error);
      throw error;
    }
  }

  /**
   * Get Redis client instance
   */
  getClient() {
    return this.client;
  }

  /**
   * Get Redis publisher instance
   */
  getPublisher() {
    return this.publisher;
  }

  /**
   * Get Redis subscriber instance
   */
  getSubscriber() {
    return this.subscriber;
  }

  /**
   * Set a key-value pair in Redis
   * @param {string} key - The key to set
   * @param {string|number|Object} value - The value to set
   * @param {Object} options - Additional options
   * @param {number} options.expire - Expiration time in seconds
   */
  async set(key, value, options = {}) {
    if (!this.client) {
      throw new Error('Redis client not connected');
    }

    try {
      let serializedValue = value;
      if (typeof value === 'object') {
        serializedValue = JSON.stringify(value);
      }

      if (options.expire) {
        await this.client.setEx(key, options.expire, serializedValue);
      } else {
        await this.client.set(key, serializedValue);
      }
      
      return true;
    } catch (error) {
      console.error('Error setting key in Redis:', error);
      throw error;
    }
  }

  /**
   * Get a value from Redis by key
   * @param {string} key - The key to get
   * @param {boolean} parseJson - Whether to parse JSON response (default: true)
   */
  async get(key, parseJson = true) {
    if (!this.client) {
      throw new Error('Redis client not connected');
    }

    try {
      const value = await this.client.get(key);
      
      if (value === null) {
        return null;
      }

      if (parseJson) {
        try {
          return JSON.parse(value);
        } catch (parseError) {
          // If JSON parsing fails, return the raw value
          return value;
        }
      }

      return value;
    } catch (error) {
      console.error('Error getting key from Redis:', error);
      throw error;
    }
  }

  /**
   * Publish a message to a channel
   * @param {string} channel - The channel to publish to
   * @param {string|Object} message - The message to publish
   */
  async publish(channel, message) {
    if (!this.publisher) {
      throw new Error('Redis publisher not connected');
    }

    try {
      let serializedMessage = message;
      if (typeof message === 'object') {
        serializedMessage = JSON.stringify(message);
      }

      const result = await this.publisher.publish(channel, serializedMessage);
      return result;
    } catch (error) {
      console.error('Error publishing message to Redis:', error);
      throw error;
    }
  }

  /**
   * Subscribe to a channel
   * @param {string} channel - The channel to subscribe to
   * @param {Function} callback - Callback function to handle messages
   */
  async subscribe(channel, callback) {
    if (!this.subscriber) {
      throw new Error('Redis subscriber not connected');
    }

    try {
      await this.subscriber.subscribe(channel, (message) => {
        try {
          const parsedMessage = JSON.parse(message);
          callback(parsedMessage);
        } catch (parseError) {
          // If JSON parsing fails, pass the raw message
          callback(message);
        }
      });
      
      console.log(`Subscribed to channel: ${channel}`);
    } catch (error) {
      console.error('Error subscribing to Redis channel:', error);
      throw error;
    }
  }

  /**
   * Unsubscribe from a channel
   * @param {string} channel - The channel to unsubscribe from
   */
  async unsubscribe(channel) {
    if (!this.subscriber) {
      throw new Error('Redis subscriber not connected');
    }

    try {
      await this.subscriber.unsubscribe(channel);
      console.log(`Unsubscribed from channel: ${channel}`);
    } catch (error) {
      console.error('Error unsubscribing from Redis channel:', error);
      throw error;
    }
  }

  /**
   * Check if Redis is connected
   */
  isConnected() {
    return this.client && this.client.isReady;
  }

  /**
   * Get Redis info
   */
  async getInfo() {
    if (!this.client) {
      throw new Error('Redis client not connected');
    }

    try {
      return await this.client.info();
    } catch (error) {
      console.error('Error getting Redis info:', error);
      throw error;
    }
  }
}

// Create and export a singleton instance
const redisHelper = new RedisHelper();

module.exports = redisHelper;

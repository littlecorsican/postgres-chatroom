// index.js
const express = require('express');
const { PrismaClient } = require('@prisma/client');
const PostgresListener = require('./services/postgresListener');
const routes = require('./routes');
const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');

const app = express();
const port = 5000;
const prisma = new PrismaClient();
const postgresListener = new PostgresListener();

// Middleware
app.use(express.json());

// Make postgresListener available to routes
app.set('postgresListener', postgresListener);

// Initialize PostgreSQL listener
async function initializeListener() {
  try {
    await postgresListener.connect();
    
    // Listen for message changes
    postgresListener.on('message_change', (data) => {
      console.log('🔔 Message change detected:', data);
      
      // Here you can implement real-time features like:
      // - WebSocket broadcasting
      // - Server-Sent Events
      // - Push notifications
      // - Cache invalidation
      
      // Example: Broadcast to connected clients
      // io.emit('message_update', data);
    });
    
    console.log('✅ PostgreSQL listener initialized successfully');
  } catch (error) {
    console.error('❌ Failed to initialize PostgreSQL listener:', error);
  }
}

// Mount all routes
app.use('/api', routes);

// Error handling middleware (must be last)
app.use(notFoundHandler);
app.use(errorHandler);

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🔄 Shutting down gracefully...');
  await postgresListener.disconnect();
  await prisma.$disconnect();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\n🔄 Shutting down gracefully...');
  await postgresListener.disconnect();
  await prisma.$disconnect();
  process.exit(0);
});

// Start the server
app.listen(port, async () => {
  console.log(`🚀 Server is running at http://localhost:${port}`);
  console.log(`📡 API endpoints available at http://localhost:${port}/api`);
  
  // Initialize the PostgreSQL listener after server starts
  await initializeListener();
});

const express = require('express');
const { PrismaClient } = require('@prisma/client');

const router = express.Router();
const prisma = new PrismaClient();

// Health check endpoint
router.get('/', async (req, res) => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    
    // Get listener status from app context
    const listener = req.app.get('postgresListener');
    const listenerStatus = listener && listener.isListening ? 'Active' : 'Inactive';
    
    res.json({ 
      status: 'OK', 
      database: 'Connected',
      listener: listenerStatus,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ 
      status: 'Error', 
      database: 'Disconnected', 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Detailed health check
router.get('/detailed', async (req, res) => {
  try {
    // Database health
    const dbStart = Date.now();
    await prisma.$queryRaw`SELECT 1`;
    const dbLatency = Date.now() - dbStart;
    
    // Listener health
    const listener = req.app.get('postgresListener');
    const listenerHealth = {
      isListening: listener ? listener.isListening : false,
      status: listener ? 'Connected' : 'Not Initialized'
    };
    
    res.json({
      status: 'OK',
      database: {
        status: 'Connected',
        latency: `${dbLatency}ms`
      },
      listener: listenerHealth,
      system: {
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        nodeVersion: process.version
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      status: 'Error',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

module.exports = router;

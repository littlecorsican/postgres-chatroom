const express = require('express');
const { authenticateToken, generateToken } = require('../utils/auth');

const router = express.Router();

// Test endpoint to trigger a notification
router.post('/notification', async (req, res) => {
  try {
    const listener = req.app.get('postgresListener');
    
    if (!listener) {
      return res.status(500).json({ 
        error: 'PostgreSQL listener not initialized' 
      });
    }
    
    await listener.testNotification();
    res.json({ 
      message: 'Test notification sent successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Test endpoint to check listener status
router.get('/listener-status', (req, res) => {
  const listener = req.app.get('postgresListener');
  
  if (!listener) {
    return res.json({
      status: 'Not Initialized',
      message: 'PostgreSQL listener has not been initialized'
    });
  }
  
  res.json({
    status: listener.isListening ? 'Active' : 'Inactive',
    isListening: listener.isListening,
    timestamp: new Date().toISOString()
  });
});

// Test endpoint to simulate database operations
router.post('/simulate-message', async (req, res) => {
  try {
    const { PrismaClient } = require('@prisma/client');
    const prisma = new PrismaClient();
    
    // Create a test user if it doesn't exist
    let user = await prisma.user.findFirst({
      where: { name: 'Test User' }
    });
    
    if (!user) {
      user = await prisma.user.create({
        data: { name: 'Test User' }
      });
    }
    
    // Create a test group if it doesn't exist
    let group = await prisma.group.findFirst();
    
    if (!group) {
      group = await prisma.group.create({});
    }
    
    // Add user to group if not already a participant
    const existingParticipant = await prisma.groupParticipant.findFirst({
      where: {
        group_uuid: group.uuid,
        user_uuid: user.uuid
      }
    });
    
    if (!existingParticipant) {
      await prisma.groupParticipant.create({
        data: {
          group_uuid: group.uuid,
          user_uuid: user.uuid
        }
      });
    }
    
    // Create a test message (this will trigger the listener)
    const message = await prisma.message.create({
      data: {
        group_uuid: group.uuid,
        content: `Test message at ${new Date().toISOString()} 🧪`,
        sender_uuid: user.uuid
      }
    });
    
    await prisma.$disconnect();
    
    res.json({
      message: 'Test message created successfully',
      messageId: message.id,
      content: message.content,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    res.status(500).json({ 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Test endpoint to verify JWT authentication
router.get('/auth-test', authenticateToken, (req, res) => {
  res.json({
    message: 'Authentication successful',
    user: req.user,
    timestamp: new Date().toISOString()
  });
});

// Test endpoint to generate a test token
router.post('/generate-test-token', async (req, res) => {
  try {
    const { name } = req.body;
    
    if (!name) {
      return res.status(400).json({
        error: 'Name is required to generate test token',
        timestamp: new Date().toISOString()
      });
    }
    
    // Create or find a test user
    const { PrismaClient } = require('@prisma/client');
    const prisma = new PrismaClient();
    
    let user = await prisma.user.findFirst({
      where: { name }
    });
    
    if (!user) {
      user = await prisma.user.create({
        data: { name }
      });
    }
    
    await prisma.$disconnect();
    
    // Generate token
    const token = generateToken(user);
    
    res.json({
      message: 'Test token generated successfully',
      user: {
        uuid: user.uuid,
        name: user.name
      },
      token,
      tokenInfo: {
        expiresIn: '24h',
        issuer: 'chatroom-backend',
        audience: 'chatroom-users'
      },
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    res.status(500).json({ 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

module.exports = router;

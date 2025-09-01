const express = require('express');
const { PrismaClient } = require('@prisma/client');

const router = express.Router();
const prisma = new PrismaClient();

// Get all messages for a group
router.get('/group/:groupUuid', async (req, res) => {
  try {
    const { groupUuid } = req.params;
    const { page = 1, limit = 50, includeDeleted = false } = req.query;
    
    const skip = (parseInt(page) - 1) * parseInt(limit);
    
    const where = {
      group_uuid: groupUuid,
      ...(includeDeleted === 'true' ? {} : { is_deleted: false })
    };
    
    const [messages, total] = await Promise.all([
      prisma.message.findMany({
        where,
        include: {
          sender: {
            select: {
              uuid: true,
              name: true
            }
          }
        },
        orderBy: {
          created_date: 'desc'
        },
        skip,
        take: parseInt(limit)
      }),
      prisma.message.count({ where })
    ]);
    
    res.json({
      messages,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / parseInt(limit))
      }
    });
    
  } catch (error) {
    res.status(500).json({ 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Get a specific message
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const message = await prisma.message.findFirst({
      where: { 
        id: parseInt(id),
        is_deleted: false
      },
      include: {
        sender: {
          select: {
            uuid: true,
            name: true
          }
        },
        group: {
          select: {
            uuid: true
          }
        }
      }
    });
    
    if (!message) {
      return res.status(404).json({ 
        error: 'Message not found',
        timestamp: new Date().toISOString()
      });
    }
    
    res.json(message);
    
  } catch (error) {
    res.status(500).json({ 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Create a new message
router.post('/', async (req, res) => {
  try {
    const { group_uuid, content, file, sender_uuid } = req.body;
    
    // Validate required fields
    if (!group_uuid || !content || !sender_uuid) {
      return res.status(400).json({
        error: 'Missing required fields: group_uuid, content, sender_uuid',
        timestamp: new Date().toISOString()
      });
    }
    
    // Verify user is a participant in the group
    const participant = await prisma.groupParticipant.findFirst({
      where: {
        group_uuid,
        user_uuid: sender_uuid
      }
    });
    
    if (!participant) {
      return res.status(403).json({
        error: 'User is not a participant in this group',
        timestamp: new Date().toISOString()
      });
    }
    
    const message = await prisma.message.create({
      data: {
        group_uuid,
        content,
        file: file || null,
        sender_uuid
      },
      include: {
        sender: {
          select: {
            uuid: true,
            name: true
          }
        }
      }
    });
    
    res.status(201).json({
      message: 'Message created successfully',
      data: message,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    res.status(500).json({ 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Update a message
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { content, file } = req.body;
    const { user_uuid } = req.headers; // Assuming user UUID is passed in headers
    
    if (!user_uuid) {
      return res.status(401).json({
        error: 'User authentication required',
        timestamp: new Date().toISOString()
      });
    }
    
    // Find the message and verify ownership
    const existingMessage = await prisma.message.findFirst({
      where: { 
        id: parseInt(id),
        sender_uuid: user_uuid,
        is_deleted: false
      }
    });
    
    if (!existingMessage) {
      return res.status(404).json({
        error: 'Message not found or you do not have permission to edit it',
        timestamp: new Date().toISOString()
      });
    }
    
    const updatedMessage = await prisma.message.update({
      where: { id: parseInt(id) },
      data: {
        content: content || existingMessage.content,
        file: file !== undefined ? file : existingMessage.file
      },
      include: {
        sender: {
          select: {
            uuid: true,
            name: true
          }
        }
      }
    });
    
    res.json({
      message: 'Message updated successfully',
      data: updatedMessage,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    res.status(500).json({ 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Soft delete a message
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { user_uuid } = req.headers; // Assuming user UUID is passed in headers
    
    if (!user_uuid) {
      return res.status(401).json({
        error: 'User authentication required',
        timestamp: new Date().toISOString()
      });
    }
    
    // Find the message and verify ownership
    const existingMessage = await prisma.message.findFirst({
      where: { 
        id: parseInt(id),
        sender_uuid: user_uuid,
        is_deleted: false
      }
    });
    
    if (!existingMessage) {
      return res.status(404).json({
        error: 'Message not found or you do not have permission to delete it',
        timestamp: new Date().toISOString()
      });
    }
    
    await prisma.message.update({
      where: { id: parseInt(id) },
      data: { is_deleted: true }
    });
    
    res.json({
      message: 'Message deleted successfully',
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    res.status(500).json({ 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Search messages
router.get('/search/:groupUuid', async (req, res) => {
  try {
    const { groupUuid } = req.params;
    const { q: searchQuery, page = 1, limit = 20 } = req.query;
    
    if (!searchQuery) {
      return res.status(400).json({
        error: 'Search query is required',
        timestamp: new Date().toISOString()
      });
    }
    
    const skip = (parseInt(page) - 1) * parseInt(limit);
    
    const where = {
      group_uuid: groupUuid,
      is_deleted: false,
      content: {
        contains: searchQuery,
        mode: 'insensitive'
      }
    };
    
    const [messages, total] = await Promise.all([
      prisma.message.findMany({
        where,
        include: {
          sender: {
            select: {
              uuid: true,
              name: true
            }
          }
        },
        orderBy: {
          created_date: 'desc'
        },
        skip,
        take: parseInt(limit)
      }),
      prisma.message.count({ where })
    ]);
    
    res.json({
      messages,
      searchQuery,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / parseInt(limit))
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

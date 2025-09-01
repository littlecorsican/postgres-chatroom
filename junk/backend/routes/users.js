const express = require('express');
const { PrismaClient } = require('@prisma/client');
const { 
  authenticateToken, 
  requireOwnership, 
  generateToken,
  refreshTokenIfNeeded 
} = require('../utils/auth');

const router = express.Router();
const prisma = new PrismaClient();

// Create a new user (public endpoint - no auth required)
router.post('/', async (req, res) => {
  try {
    const { name } = req.body;
    
    // Validate required fields
    if (!name) {
      return res.status(400).json({
        error: 'Name is required',
        timestamp: new Date().toISOString()
      });
    }
    
    // Validate name length
    if (name.length > 25) {
      return res.status(400).json({
        error: 'Name must be 25 characters or less',
        timestamp: new Date().toISOString()
      });
    }
    
    // Check if user with same name already exists
    const existingUser = await prisma.user.findFirst({
      where: { name }
    });
    
    if (existingUser) {
      return res.status(409).json({
        error: 'User with this name already exists',
        timestamp: new Date().toISOString()
      });
    }
    
    // Create the user
    const user = await prisma.user.create({
      data: { name }
    });
    
    // Generate JWT token for the new user
    const token = generateToken(user);
    
    res.status(201).json({
      message: 'User created successfully',
      data: user,
      token,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    res.status(500).json({ 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Login endpoint (public endpoint - no auth required)
router.post('/login', async (req, res) => {
  try {
    const { name } = req.body;
    
    if (!name) {
      return res.status(400).json({
        error: 'Name is required',
        timestamp: new Date().toISOString()
      });
    }
    
    // Find user by name
    const user = await prisma.user.findFirst({
      where: { name }
    });
    
    if (!user) {
      return res.status(404).json({
        error: 'User not found',
        timestamp: new Date().toISOString()
      });
    }
    
    // Generate JWT token
    const token = generateToken(user);
    
    res.json({
      message: 'Login successful',
      data: user,
      token,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    res.status(500).json({ 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Get all users (requires authentication)
router.get('/', authenticateToken, refreshTokenIfNeeded, async (req, res) => {
  try {
    const { page = 1, limit = 50, search } = req.query;
    
    const skip = (parseInt(page) - 1) * parseInt(limit);
    
    const where = search ? {
      name: {
        contains: search,
        mode: 'insensitive'
      }
    } : {};
    
    const [users, total] = await Promise.all([
      prisma.user.findMany({
        where,
        select: {
          uuid: true,
          name: true,
          created_date: true,
          updated_at: true,
          _count: {
            select: {
              messages: true,
              groupParticipants: true
            }
          }
        },
        orderBy: {
          created_date: 'desc'
        },
        skip,
        take: parseInt(limit)
      }),
      prisma.user.count({ where })
    ]);
    
    res.json({
      users,
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

// Get a specific user (requires authentication)
router.get('/:uuid', authenticateToken, refreshTokenIfNeeded, async (req, res) => {
  try {
    const { uuid } = req.params;
    
    const user = await prisma.user.findUnique({
      where: { uuid },
      select: {
        uuid: true,
        name: true,
        created_date: true,
        updated_at: true,
        messages: {
          where: { is_deleted: false },
          select: {
            id: true,
            content: true,
            created_date: true,
            group: {
              select: {
                uuid: true
              }
            }
          },
          orderBy: {
            created_date: 'desc'
          },
          take: 10
        },
        groupParticipants: {
          select: {
            joined_at: true,
            group: {
              select: {
                uuid: true
              }
            }
          }
        },
        _count: {
          select: {
            messages: true,
            groupParticipants: true
          }
        }
      }
    });
    
    if (!user) {
      return res.status(404).json({ 
        error: 'User not found',
        timestamp: new Date().toISOString()
      });
    }
    
    res.json(user);
    
  } catch (error) {
    res.status(500).json({ 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Update a user (requires authentication + ownership)
router.put('/:uuid', 
  authenticateToken, 
  refreshTokenIfNeeded,
  requireOwnership((req) => req.params.uuid), 
  async (req, res) => {
    try {
      const { uuid } = req.params;
      const { name } = req.body;
      
      if (!name) {
        return res.status(400).json({
          error: 'Name is required',
          timestamp: new Date().toISOString()
        });
      }
      
      if (name.length > 25) {
        return res.status(400).json({
          error: 'Name must be 25 characters or less',
          timestamp: new Date().toISOString()
        });
      }
      
      // Check if user exists
      const existingUser = await prisma.user.findUnique({
        where: { uuid }
      });
      
      if (!existingUser) {
        return res.status(404).json({
          error: 'User not found',
          timestamp: new Date().toISOString()
        });
      }
      
      // Check if new name conflicts with another user
      const nameConflict = await prisma.user.findFirst({
        where: {
          name,
          uuid: { not: uuid }
        }
      });
      
      if (nameConflict) {
        return res.status(409).json({
          error: 'User with this name already exists',
          timestamp: new Date().toISOString()
        });
      }
      
      // Update the user
      const updatedUser = await prisma.user.update({
        where: { uuid },
        data: { name }
      });
      
      res.json({
        message: 'User updated successfully',
        data: updatedUser,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      res.status(500).json({ 
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

// Delete a user (requires authentication + ownership)
router.delete('/:uuid', 
  authenticateToken, 
  refreshTokenIfNeeded,
  requireOwnership((req) => req.params.uuid), 
  async (req, res) => {
    try {
      const { uuid } = req.params;
      
      // Check if user exists
      const existingUser = await prisma.user.findUnique({
        where: { uuid }
      });
      
      if (!existingUser) {
        return res.status(404).json({
          error: 'User not found',
          timestamp: new Date().toISOString()
        });
      }
      
      // Check if user has any messages or group participations
      const [messageCount, participantCount] = await Promise.all([
        prisma.message.count({
          where: { sender_uuid: uuid }
        }),
        prisma.groupParticipant.count({
          where: { user_uuid: uuid }
        })
      ]);
      
      if (messageCount > 0 || participantCount > 0) {
        return res.status(400).json({
          error: 'Cannot delete user with existing messages or group participations',
          details: {
            messages: messageCount,
            groupParticipations: participantCount
          },
          timestamp: new Date().toISOString()
        });
      }
      
      // Delete the user
      await prisma.user.delete({
        where: { uuid }
      });
      
      res.json({
        message: 'User deleted successfully',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      res.status(500).json({ 
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

// Get user's groups (requires authentication + ownership)
router.get('/:uuid/groups', 
  authenticateToken, 
  refreshTokenIfNeeded,
  requireOwnership((req) => req.params.uuid), 
  async (req, res) => {
    try {
      const { uuid } = req.params;
      const { page = 1, limit = 20 } = req.query;
      
      const skip = (parseInt(page) - 1) * parseInt(limit);
      
      // Check if user exists
      const user = await prisma.user.findUnique({
        where: { uuid }
      });
      
      if (!user) {
        return res.status(404).json({
          error: 'User not found',
          timestamp: new Date().toISOString()
        });
      }
      
      const [participations, total] = await Promise.all([
        prisma.groupParticipant.findMany({
          where: { user_uuid: uuid },
          include: {
            group: {
              select: {
                uuid: true,
                created_date: true,
                _count: {
                  select: {
                    messages: true,
                    groupParticipants: true
                  }
                }
              }
            }
          },
          orderBy: {
            joined_at: 'desc'
          },
          skip,
          take: parseInt(limit)
        }),
        prisma.groupParticipant.count({
          where: { user_uuid: uuid }
        })
      ]);
      
      res.json({
        groups: participations.map(p => ({
          ...p.group,
          joined_at: p.joined_at
        })),
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
  }
);

// Get user's messages (requires authentication + ownership)
router.get('/:uuid/messages', 
  authenticateToken, 
  refreshTokenIfNeeded,
  requireOwnership((req) => req.params.uuid), 
  async (req, res) => {
    try {
      const { uuid } = req.params;
      const { page = 1, limit = 20, groupUuid } = req.query;
      
      const skip = (parseInt(page) - 1) * parseInt(limit);
      
      // Check if user exists
      const user = await prisma.user.findUnique({
        where: { uuid }
      });
      
      if (!user) {
        return res.status(404).json({
          error: 'User not found',
          timestamp: new Date().toISOString()
        });
      }
      
      const where = {
        sender_uuid: uuid,
        is_deleted: false,
        ...(groupUuid && { group_uuid: groupUuid })
      };
      
      const [messages, total] = await Promise.all([
        prisma.message.findMany({
          where,
          include: {
            group: {
              select: {
                uuid: true
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
        },
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      res.status(500).json({ 
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

// Get current user profile (requires authentication)
router.get('/profile/me', authenticateToken, refreshTokenIfNeeded, async (req, res) => {
  try {
    const user = await prisma.user.findUnique({
      where: { uuid: req.user.uuid },
      select: {
        uuid: true,
        name: true,
        created_date: true,
        updated_at: true,
        _count: {
          select: {
            messages: true,
            groupParticipants: true
          }
        }
      }
    });
    
    if (!user) {
      return res.status(404).json({
        error: 'User not found',
        timestamp: new Date().toISOString()
      });
    }
    
    res.json({
      user,
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

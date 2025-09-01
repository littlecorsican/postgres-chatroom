const jwt = require('jsonwebtoken');

// JWT secret key from environment variables
const JWT_SECRET = process.env.AUTH_SECRET_KEY;

if (!JWT_SECRET) {
  console.error('❌ AUTH_SECRET_KEY is not set in environment variables');
  process.exit(1);
}

/**
 * Generate JWT token for a user
 * @param {Object} user - User object with uuid and name
 * @param {string} user.uuid - User's UUID
 * @param {string} user.name - User's name
 * @param {Object} options - Additional options
 * @param {string} options.expiresIn - Token expiration time (default: '24h')
 * @returns {string} JWT token
 */
function generateToken(user, options = {}) {
  const payload = {
    uuid: user.uuid,
    name: user.name,
    iat: Math.floor(Date.now() / 1000),
    ...options
  };

  const tokenOptions = {
    expiresIn: options.expiresIn || '24h',
    issuer: 'chatroom-backend',
    audience: 'chatroom-users'
  };

  try {
    return jwt.sign(payload, JWT_SECRET, tokenOptions);
  } catch (error) {
    console.error('Error generating JWT token:', error);
    throw new Error('Failed to generate authentication token');
  }
}

/**
 * Verify JWT token
 * @param {string} token - JWT token to verify
 * @returns {Object} Decoded token payload
 */
function verifyToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET, {
      issuer: 'chatroom-backend',
      audience: 'chatroom-users'
    });
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      throw new Error('Token has expired');
    } else if (error.name === 'JsonWebTokenError') {
      throw new Error('Invalid token');
    } else if (error.name === 'NotBeforeError') {
      throw new Error('Token not active yet');
    } else {
      throw new Error('Token verification failed');
    }
  }
}

/**
 * Extract token from request headers
 * @param {Object} req - Express request object
 * @returns {string|null} JWT token or null if not found
 */
function extractToken(req) {
  // Check Authorization header (Bearer token)
  if (req.headers.authorization) {
    const authHeader = req.headers.authorization;
    if (authHeader.startsWith('Bearer ')) {
      return authHeader.substring(7);
    }
  }

  // Check x-auth-token header
  if (req.headers['x-auth-token']) {
    return req.headers['x-auth-token'];
  }

  // Check query parameter
  if (req.query.token) {
    return req.query.token;
  }

  return null;
}

/**
 * Authentication middleware
 * Verifies JWT token and adds user info to request
 */
function authenticateToken(req, res, next) {
  try {
    const token = extractToken(req);

    if (!token) {
      return res.status(401).json({
        error: 'Access token required',
        code: 'TOKEN_MISSING',
        timestamp: new Date().toISOString()
      });
    }

    const decoded = verifyToken(token);
    
    // Add user info to request object
    req.user = {
      uuid: decoded.uuid,
      name: decoded.name
    };

    next();
  } catch (error) {
    return res.status(401).json({
      error: error.message,
      code: 'TOKEN_INVALID',
      timestamp: new Date().toISOString()
    });
  }
}

/**
 * Optional authentication middleware
 * Verifies JWT token if present, but doesn't require it
 */
function optionalAuth(req, res, next) {
  try {
    const token = extractToken(req);

    if (token) {
      const decoded = verifyToken(token);
      req.user = {
        uuid: decoded.uuid,
        name: decoded.name
      };
    }

    next();
  } catch (error) {
    // Continue without authentication if token is invalid
    next();
  }
}

/**
 * Role-based access control middleware
 * @param {string} requiredRole - Required role for access
 */
function requireRole(requiredRole) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        error: 'Authentication required',
        code: 'AUTH_REQUIRED',
        timestamp: new Date().toISOString()
      });
    }

    // For now, we'll use a simple role system
    // You can extend this based on your user model
    if (req.user.role !== requiredRole) {
      return res.status(403).json({
        error: 'Insufficient permissions',
        code: 'INSUFFICIENT_PERMISSIONS',
        requiredRole,
        timestamp: new Date().toISOString()
      });
    }

    next();
  };
}

/**
 * Owner verification middleware
 * Ensures the authenticated user owns the resource or is an admin
 * @param {Function} getOwnerUuid - Function to get owner UUID from request
 * @param {boolean} allowAdmin - Whether to allow admin users to bypass ownership check
 */
function requireOwnership(getOwnerUuid, allowAdmin = false) {
  return async (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        error: 'Authentication required',
        code: 'AUTH_REQUIRED',
        timestamp: new Date().toISOString()
      });
    }

    try {
      const ownerUuid = getOwnerUuid(req);
      
      // Allow if user owns the resource
      if (req.user.uuid === ownerUuid) {
        return next();
      }

      // Allow admin users if specified
      if (allowAdmin && req.user.role === 'admin') {
        return next();
      }

      return res.status(403).json({
        error: 'Access denied: You can only modify your own resources',
        code: 'OWNERSHIP_REQUIRED',
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      return res.status(400).json({
        error: 'Invalid resource identifier',
        code: 'INVALID_RESOURCE',
        timestamp: new Date().toISOString()
      });
    }
  };
}

/**
 * Refresh token middleware
 * Generates a new token if the current one is about to expire
 */
function refreshTokenIfNeeded(req, res, next) {
  try {
    const token = extractToken(req);
    
    if (token) {
      const decoded = jwt.decode(token);
      
      if (decoded && decoded.exp) {
        const now = Math.floor(Date.now() / 1000);
        const timeUntilExpiry = decoded.exp - now;
        
        // If token expires in less than 1 hour, refresh it
        if (timeUntilExpiry < 3600) {
          const { PrismaClient } = require('@prisma/client');
          const prisma = new PrismaClient();
          
          prisma.user.findUnique({
            where: { uuid: decoded.uuid },
            select: { uuid: true, name: true }
          }).then(user => {
            if (user) {
              const newToken = generateToken(user);
              res.set('X-New-Token', newToken);
              res.set('X-Token-Refreshed', 'true');
            }
          }).catch(console.error);
        }
      }
    }
    
    next();
  } catch (error) {
    // Continue even if refresh fails
    next();
  }
}

module.exports = {
  generateToken,
  verifyToken,
  extractToken,
  authenticateToken,
  optionalAuth,
  requireRole,
  requireOwnership,
  refreshTokenIfNeeded
};

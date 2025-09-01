// Error handling middleware
const errorHandler = (err, req, res, next) => {
  console.error('Error:', err);

  // Default error
  let statusCode = 500;
  let message = 'Internal Server Error';

  // Handle specific error types
  if (err.name === 'ValidationError') {
    statusCode = 400;
    message = err.message;
  } else if (err.name === 'UnauthorizedError') {
    statusCode = 401;
    message = 'Unauthorized';
  } else if (err.name === 'NotFoundError') {
    statusCode = 404;
    message = 'Resource not found';
  } else if (err.code === 'P2002') {
    statusCode = 409;
    message = 'Resource already exists';
  } else if (err.code === 'P2025') {
    statusCode = 404;
    message = 'Record not found';
  } else if (err.message) {
    message = err.message;
  }

  res.status(statusCode).json({
    error: message,
    statusCode,
    timestamp: new Date().toISOString(),
    path: req.path,
    method: req.method
  });
};

// 404 handler for unmatched routes
const notFoundHandler = (req, res) => {
  res.status(404).json({
    error: 'Route not found',
    statusCode: 404,
    timestamp: new Date().toISOString(),
    path: req.path,
    method: req.method,
    availableRoutes: [
      'GET /api',
      'GET /api/health',
      'GET /api/health/detailed',
      'POST /api/test/notification',
      'GET /api/test/listener-status',
      'POST /api/test/simulate-message',
      'GET /api/messages/group/:groupUuid',
      'GET /api/messages/:id',
      'POST /api/messages',
      'PUT /api/messages/:id',
      'DELETE /api/messages/:id',
      'GET /api/messages/search/:groupUuid',
      'POST /api/users (Public)',
      'POST /api/users/login (Public)',
      'GET /api/users (Auth Required)',
      'GET /api/users/:uuid (Auth Required)',
      'PUT /api/users/:uuid (Auth + Ownership Required)',
      'DELETE /api/users/:uuid (Auth + Ownership Required)',
      'GET /api/users/:uuid/groups (Auth + Ownership Required)',
      'GET /api/users/:uuid/messages (Auth + Ownership Required)',
      'GET /api/users/profile/me (Auth Required)'
    ]
  });
};

module.exports = {
  errorHandler,
  notFoundHandler
};

const express = require('express');
const healthRoutes = require('./health');
const testRoutes = require('./test');
const messageRoutes = require('./messages');
const userRoutes = require('./users');

const router = express.Router();

// Mount route modules
router.use('/health', healthRoutes);
router.use('/test', testRoutes);
router.use('/messages', messageRoutes);
router.use('/users', userRoutes);

// Basic route
router.get('/', (req, res) => {
  res.send('Hello, world!');
});

module.exports = router;

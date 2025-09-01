const { PrismaClient } = require('@prisma/client');
const PostgresListener = require('../services/postgresListener');

// Example usage of PostgreSQL listener with message operations
async function exampleUsage() {
  const prisma = new PrismaClient();
  const listener = new PostgresListener();

  try {
    // Connect to database and start listening
    await listener.connect();
    
    // Listen for message changes
    listener.on('message_change', (data) => {
      console.log('🔔 Real-time message update:', data);
      
      switch (data.operation) {
        case 'INSERT':
          console.log(`📝 New message created: ${data.content}`);
          break;
        case 'UPDATE':
          console.log(`✏️ Message updated: ${data.content}`);
          break;
        case 'DELETE':
          console.log(`🗑️ Message deleted: ${data.id}`);
          break;
      }
    });

    // Example: Create a user
    const user = await prisma.user.create({
      data: {
        name: 'Test User'
      }
    });
    console.log('👤 User created:', user);

    // Example: Create a group
    const group = await prisma.group.create({
      data: {}
    });
    console.log('👥 Group created:', group);

    // Example: Add user to group
    await prisma.groupParticipant.create({
      data: {
        group_uuid: group.uuid,
        user_uuid: user.uuid
      }
    });
    console.log('➕ User added to group');

    // Example: Send a message (this will trigger the listener)
    const message = await prisma.message.create({
      data: {
        group_uuid: group.uuid,
        content: 'Hello, world! 👋',
        sender_uuid: user.uuid
      }
    });
    console.log('💬 Message sent:', message);

    // Wait a bit to see the notification
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Example: Update the message (this will trigger the listener)
    const updatedMessage = await prisma.message.update({
      where: { id: message.id },
      data: {
        content: 'Hello, world! 👋 Updated! ✨'
      }
    });
    console.log('✏️ Message updated:', updatedMessage);

    // Wait a bit to see the notification
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Example: Soft delete the message (this will trigger the listener)
    const deletedMessage = await prisma.message.update({
      where: { id: message.id },
      data: {
        is_deleted: true
      }
    });
    console.log('🗑️ Message soft deleted:', deletedMessage);

    // Wait a bit to see the notification
    await new Promise(resolve => setTimeout(resolve, 1000));

  } catch (error) {
    console.error('❌ Error in example:', error);
  } finally {
    // Cleanup
    await listener.disconnect();
    await prisma.$disconnect();
  }
}

// Example: WebSocket integration
function webSocketExample() {
  const listener = new PostgresListener();
  
  listener.on('message_change', (data) => {
    // Broadcast to all connected WebSocket clients
    // io.emit('message_update', data);
    
    // Or emit to specific room/group
    // io.to(data.group_uuid).emit('message_update', data);
    
    console.log('📡 Broadcasting to WebSocket clients:', data);
  });
}

// Example: Cache invalidation
function cacheInvalidationExample() {
  const listener = new PostgresListener();
  
  listener.on('message_change', (data) => {
    // Invalidate relevant cache entries
    if (data.operation === 'INSERT' || data.operation === 'UPDATE') {
      // Invalidate group message cache
      // cache.del(`group_messages_${data.group_uuid}`);
      console.log('🗑️ Invalidating cache for group:', data.group_uuid);
    }
  });
}

// Example: Push notifications
function pushNotificationExample() {
  const listener = new PostgresListener();
  
  listener.on('message_change', async (data) => {
    if (data.operation === 'INSERT') {
      // Get group participants
      // const participants = await prisma.groupParticipant.findMany({
      //   where: { group_uuid: data.group_uuid },
      //   include: { user: true }
      // });
      
      // Send push notifications to participants
      console.log('📱 Sending push notification for new message');
    }
  });
}

// Run the example if this file is executed directly
if (require.main === module) {
  exampleUsage();
}

module.exports = {
  exampleUsage,
  webSocketExample,
  cacheInvalidationExample,
  pushNotificationExample
};

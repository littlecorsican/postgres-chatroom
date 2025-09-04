import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { CHAT_EVENT_SOURCE, API_ENDPOINTS } from './config';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [userName, setUserName] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);
  const eventSourceRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load old messages on component mount
    const loadOldMessages = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.MESSAGES);
        if (response.ok) {
          const data = await response.json();
          setMessages(data.messages);
        }
      } catch (error) {
        console.error('Error loading old messages:', error);
      }
    };

    // Connect to SSE
    const connectSSE = () => {
      try {
        eventSourceRef.current = new EventSource(API_ENDPOINTS.STREAM);
        
        eventSourceRef.current.onopen = () => {
          setIsConnected(true);
          console.log('SSE connection established');
        };

        eventSourceRef.current.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            const type = message.type
            if (type == "new_message") {
              setMessages(prev => [...prev, message.data]);
            }
          } catch (error) {
            console.error('Error parsing SSE message:', error);
          }
        };

        eventSourceRef.current.onerror = (error) => {
          console.error('SSE connection error:', error);
          setIsConnected(false);
          // Attempt to reconnect after 5 seconds
          setTimeout(connectSSE, 5000);
        };
      } catch (error) {
        console.error('Error connecting to SSE:', error);
        setIsConnected(false);
      }
    };

    loadOldMessages();
    connectSSE();

    // Cleanup function
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const sendMessage = async () => {
    if (!newMessage.trim() || !userName.trim()) return;

    const messageData = {
      content: newMessage,
      sender_id: userName,
      //timestamp: new Date().toISOString()
    };

    try {
      const response = await fetch(API_ENDPOINTS.MESSAGES, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(messageData),
      });

      if (response.ok) {
        setNewMessage('');
      } else {
        console.error('Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="App">
      <div className="chat-container">
        <div className="chat-header">
          <h1>Chat Room</h1>
          <div className="connection-status">
            <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>

        <div className="user-input-section">
          <input
            type="text"
            placeholder="Enter your name"
            value={userName}
            onChange={(e) => setUserName(e.target.value)}
            className="name-input"
          />
          <span className="user-id">ID: {userName} </span>
        </div>

        <div className="messages-container">
          <div className="messages-scroll">
            {messages.map((message, index) => (
              <div
                key={message.id || index}
                className={`message ${message.sender_id === userName ? 'own-message' : 'other-message'}`}
              >
                <div className="message-header">
                  <span className="user-name">{message.sender_id || 'Anonymous'}</span>
                  <span className="timestamp">
                    {new Date(message.created_date).toLocaleTimeString()}
                  </span>
                </div>
                <div className="message-text">{message.content}</div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="message-input-section">
          <textarea
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="message-textarea"
            rows="3"
          />
          <button
            onClick={sendMessage}
            disabled={!newMessage.trim() || !userName.trim()}
            className="send-button"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;

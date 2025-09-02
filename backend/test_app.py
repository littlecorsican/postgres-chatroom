#!/usr/bin/env python3
"""
Simple test script for the Starlette chatroom backend
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_create_message():
    """Test creating a new message"""
    print("Testing message creation...")
    
    message_data = {
        "content": "Hello, world! 👋 你好世界！",
        "file": "test.txt",
        "sender_id": str(uuid.uuid4())
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/message",
            json=message_data
        ) as response:
            if response.status == 201:
                result = await response.json()
                print(f"✅ Message created: {result}")
                return result
            else:
                print(f"❌ Failed to create message: {response.status}")
                return None

async def test_get_messages():
    """Test retrieving messages"""
    print("Testing message retrieval...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/message?limit=5") as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Messages retrieved: {len(result['messages'])} messages")
                print(f"   Has more: {result['has_more']}")
                if result['next_cursor']:
                    print(f"   Next cursor: {result['next_cursor']}")
                return result
            else:
                print(f"❌ Failed to retrieve messages: {response.status}")
                return None

async def test_stream_connection():
    """Test SSE stream connection"""
    print("Testing SSE stream connection...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/stream") as response:
                if response.status == 200:
                    print("✅ SSE stream connected")
                    # Read first few lines to verify connection
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            data = json.loads(line_str[6:])
                            print(f"   Received: {data['type']}")
                            break
                    return True
                else:
                    print(f"❌ Failed to connect to stream: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Stream connection error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Starlette Chatroom Backend Tests")
    print("=" * 50)
    
    # Test message creation
    message = await test_create_message()
    
    # Test message retrieval
    messages = await test_get_messages()
    
    # Test stream connection
    stream_ok = await test_stream_connection()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Message Creation: {'✅ PASS' if message else '❌ FAIL'}")
    print(f"   Message Retrieval: {'✅ PASS' if messages else '❌ FAIL'}")
    print(f"   Stream Connection: {'✅ PASS' if stream_ok else '❌ FAIL'}")
    
    if all([message, messages, stream_ok]):
        print("\n🎉 All tests passed! The backend is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main())

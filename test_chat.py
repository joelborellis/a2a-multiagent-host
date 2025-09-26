#!/usr/bin/env python3
"""
Test script for the FastAPI chat endpoint.
Usage: uv run python test_chat.py
"""

import asyncio
import json

import httpx


async def test_chat():
    """Test the chat endpoint with a simple message."""
    async with httpx.AsyncClient() as client:
        # Test health endpoint first
        print("Testing health endpoint...")
        health_response = await client.get("http://localhost:8000/health")
        print(f"Health status: {health_response.json()}")
        
        # Test agents endpoint
        print("\nTesting agents endpoint...")
        try:
            agents_response = await client.get("http://localhost:8000/agents")
            print(f"Available agents: {agents_response.json()}")
        except Exception as e:
            print(f"Error getting agents: {e}")
        
        # Test chat endpoint
        print("\nTesting chat endpoint...")
        chat_data = {
            "message": "Why is the sky blue?",
            "user_id": "test_user"
        }
        
        try:
            async with client.stream(
                "POST", 
                "http://localhost:8000/chat", 
                json=chat_data,
                headers={"Accept": "text/event-stream"}
            ) as response:
                print(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    print("Streaming response:")
                    async for chunk in response.aiter_text():
                        if chunk.strip():
                            print(f"Received: {chunk.strip()}")
                else:
                    print(f"Error: {response.status_code} - {await response.atext()}")
        except Exception as e:
            print(f"Error testing chat: {e}")


if __name__ == "__main__":
    asyncio.run(test_chat())

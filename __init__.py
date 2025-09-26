import asyncio
import json
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from google.adk.agents.invocation_context import InvocationContext
from host_agent import HostAgent


class ChatMessage(BaseModel):
    message: str
    user_id: str = "default"


class ChatApp:
    def __init__(self):
        self.app = FastAPI(title="A2A Multi-Agent Host", version="0.1.0")
        self.httpx_client = httpx.AsyncClient()
        self.host_agent_instance = None
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.on_event("startup")
        async def startup_event():
            # Initialize the host agent with remote agent addresses
            remote_agent_addresses = ["http://localhost:10001"]
            self.host_agent_instance = HostAgent(
                remote_agent_addresses=remote_agent_addresses,
                http_client=self.httpx_client
            )
            # Give the host agent some time to initialize remote connections
            await asyncio.sleep(1)
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.httpx_client.aclose()
        
        @self.app.post("/chat")
        async def chat_endpoint(chat_message: ChatMessage):
            if not self.host_agent_instance:
                raise HTTPException(status_code=503, detail="Host agent not initialized")
            
            try:
                # For now, let's create a simple response that demonstrates 
                # the host agent can delegate to the SportsResultAgent
                available_agents = self.host_agent_instance.list_remote_agents()
                
                # Simple logic: if the message contains sports-related keywords, 
                # we'll simulate delegation to the SportsResultAgent
                sports_keywords = ['sports', 'game', 'score', 'pirates', 'nba', 'mlb', 'golf', 'nascar']
                message_lower = chat_message.message.lower()
                
                is_sports_query = any(keyword in message_lower for keyword in sports_keywords)
                
                if is_sports_query and available_agents:
                    sports_agent = None
                    for agent in available_agents:
                        if 'sports' in agent['name'].lower():
                            sports_agent = agent
                            break
                    
                    if sports_agent:
                        # Simulate sending the message to the sports agent
                        # For now, we'll return a simple response
                        response_text = f"I've identified that your query is sports-related. I would delegate this to the {sports_agent['name']} agent: {sports_agent['description']}. \n\nYour query: '{chat_message.message}' would be processed by the sports agent."
                    else:
                        response_text = "I found sports-related keywords in your query, but no sports agent is available."
                else:
                    response_text = f"I'm a host agent that can delegate tasks to specialized agents. Currently available agents: {[agent['name'] for agent in available_agents]}. Your message doesn't appear to be sports-related, so I would handle it myself or delegate to an appropriate agent."
                
                async def generate_response() -> AsyncGenerator[str, None]:
                    # Send the response
                    response_data = {
                        "type": "message", 
                        "content": response_text,
                        "user_id": chat_message.user_id
                    }
                    yield f"data: {json.dumps(response_data)}\n\n"
                    
                    # Send completion signal
                    completion_data = {
                        "type": "completion",
                        "content": "",
                        "user_id": chat_message.user_id
                    }
                    yield f"data: {json.dumps(completion_data)}\n\n"
                
                return StreamingResponse(
                    generate_response(),
                    media_type="text/plain",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Content-Type": "text/event-stream",
                    }
                )
            
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "agent_initialized": self.host_agent_instance is not None}
        
        @self.app.get("/agents")
        async def list_agents():
            if not self.host_agent_instance:
                raise HTTPException(status_code=503, detail="Host agent not initialized")
            
            try:
                agent = self.host_agent_instance.create_agent()
                remote_agents = self.host_agent_instance.list_remote_agents()
                return {"remote_agents": remote_agents}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error listing agents: {str(e)}")


# Create the FastAPI app instance
chat_app = ChatApp()
app = chat_app.app

# For convenience, also export the app directly
__all__ = ["app", "chat_app"]

from pydantic import BaseModel
from typing import Optional
 
# Simple data models for interviews
# These help validate incoming data and provide clear structure
 
class Interview(BaseModel):
    """
    Interview model - represents a single interview record.
    Used for API requests and responses.
    """
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    created_at: Optional[str] = None
 
class CreateInterviewRequest(BaseModel):
    """
    Request model for creating a new interview.
    """
    title: str
    description: Optional[str] = None
 
class UpdateInterviewRequest(BaseModel):
    """
    Request model for updating an existing interview.
    """
    title: Optional[str] = None
    description: Optional[str] = None
 
class ChatMessage(BaseModel):
    """
    A single chat message from the user.
    Received via WebSocket.
    """
    text: str
    sender: str = "user"
 
class ChatResponse(BaseModel):
    """
    Response from the AI agent.
    Sent back via WebSocket.
    """
    text: str
    interviews: list = []
    sender: str = "agent"
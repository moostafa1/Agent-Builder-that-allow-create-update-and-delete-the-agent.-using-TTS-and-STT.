import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

# ---------------------------------------------------------
# 1. AGENT MODEL
# ---------------------------------------------------------
class Agent(SQLModel, table=True):
    # Use UUIDs for secure, unguessable IDs, generated automatically
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True)
    prompt: str = Field(description="The system instruction for the LLM")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships: One Agent can have multiple Sessions
    sessions: List["Session"] = Relationship(back_populates="agent", cascade_delete=True)


# ---------------------------------------------------------
# 2. SESSION MODEL
# ---------------------------------------------------------
class Session(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Foreign Key linking to the Agent table
    agent_id: uuid.UUID = Field(foreign_key="agent.id", index=True)
    
    # Optional display name (e.g., "Chat 1 (6:45 PM)")
    name: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent: Optional[Agent] = Relationship(back_populates="sessions")
    messages: List["Message"] = Relationship(back_populates="session", cascade_delete=True)


# ---------------------------------------------------------
# 3. MESSAGE MODEL
# ---------------------------------------------------------
class Message(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Foreign Key linking to the Session table
    session_id: uuid.UUID = Field(foreign_key="session.id", index=True)
    
    # 'user' or 'assistant'
    role: str 
    
    # The actual text of the message (or transcribed text from audio)
    content: str 
    
    # If this message was created via voice, store the local path to the audio file
    audio_file_path: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    session: Optional[Session] = Relationship(back_populates="messages")
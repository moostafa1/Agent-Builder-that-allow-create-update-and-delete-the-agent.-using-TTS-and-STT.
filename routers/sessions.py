import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from pydantic import BaseModel

from database import get_session
from models import Session, Agent, Message

router = APIRouter(prefix="/api/v1", tags=["Sessions"])

# --- Request Schemas ---
class SessionCreate(BaseModel):
    agent_id: uuid.UUID
    name: str | None = "New Chat"

# --- Endpoints ---

@router.post("/sessions", response_model=Session)
async def create_session(session_data: SessionCreate, db: AsyncSession = Depends(get_session)):
    """Starts a new chat thread connected to a specific agent."""
    # First, verify the agent actually exists
    agent = await db.get(Agent, session_data.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    new_session = Session(agent_id=session_data.agent_id, name=session_data.name)
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session

@router.get("/agents/{agent_id}/sessions", response_model=list[Session])
async def list_agent_sessions(agent_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    """Fetches all chat sessions for a specific agent (for the UI dropdown)."""
    # Verify agent exists
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    result = await db.execute(
        select(Session).where(Session.agent_id == agent_id).order_by(Session.created_at.desc())
    )
    return result.scalars().all()

@router.get("/sessions/{session_id}/messages", response_model=list[Message])
async def get_session_history(session_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    """Fetches the chronological message history to load into the chat window."""
    # Verify session exists
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
    )
    return result.scalars().all()
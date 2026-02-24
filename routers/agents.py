import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from pydantic import BaseModel

# Import our database tools and models
from database import get_session
from models import Agent

# Create the router for FastAPI to use
router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])

# --- Request Schemas ---
# We use Pydantic here to define exactly what JSON the frontend should send.
# This prevents users from trying to manually send an 'id' or 'created_at' date.
class AgentCreate(BaseModel):
    name: str
    prompt: str

class AgentUpdate(BaseModel):
    name: str | None = None
    prompt: str | None = None

# --- Endpoints ---

@router.post("/", response_model=Agent)
async def create_agent(agent_data: AgentCreate, db: AsyncSession = Depends(get_session)):
    """Creates a new AI Agent persona."""
    new_agent = Agent(name=agent_data.name, prompt=agent_data.prompt)
    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)
    return new_agent

@router.get("/", response_model=list[Agent])
async def list_agents(db: AsyncSession = Depends(get_session)):
    """Fetches all agents to populate the left sidebar in the UI."""
    result = await db.execute(select(Agent))
    return result.scalars().all()

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    """Fetches the details of one specific agent."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(agent_id: uuid.UUID, agent_data: AgentUpdate, db: AsyncSession = Depends(get_session)):
    """Edits an existing agent's name or prompt."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update only the provided fields
    if agent_data.name is not None:
        agent.name = agent_data.name
    if agent_data.prompt is not None:
        agent.prompt = agent_data.prompt
        
    await db.commit()
    await db.refresh(agent)
    return agent

@router.delete("/{agent_id}")
async def delete_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    """Deletes an agent (and automatically deletes its sessions/messages due to cascade)."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await db.delete(agent)
    await db.commit()
    return {"message": "Agent deleted successfully"}
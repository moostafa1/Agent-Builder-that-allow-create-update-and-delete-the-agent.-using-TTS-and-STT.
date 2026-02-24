import os
import uuid
import logging
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from pydantic import BaseModel

from database import get_session
from models import Session, Agent, Message
from ai_service import ai_service

router = APIRouter(prefix="/api/v1/sessions", tags=["Chat"])

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Ensure the uploads directory exists
os.makedirs("uploads", exist_ok=True)

# --- Request Schemas ---
class TextMessageRequest(BaseModel):
    content: str

# --- Helper Function ---
async def get_session_and_agent(session_id: uuid.UUID, db: AsyncSession):
    """Helper to fetch the session and its associated agent."""
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    agent = await db.get(Agent, session.agent_id)
    return session, agent

async def fetch_formatted_history(session_id: uuid.UUID, db: AsyncSession):
    """Fetches history and formats it for the AI provider."""
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    # Format into [{"role": "user", "content": "hi"}, ...]
    return [{"role": msg.role, "content": msg.content} for msg in messages]

# --- Endpoints ---

@router.post("/{session_id}/messages/text", response_model=Message)
async def send_text_message(
    session_id: uuid.UUID, 
    request: TextMessageRequest, 
    db: AsyncSession = Depends(get_session)
):
    """Handles standard text-based chatting."""
    session, agent = await get_session_and_agent(session_id, db)

    # 1. Save User Message to DB
    user_msg = Message(session_id=session_id, role="user", content=request.content)
    db.add(user_msg)
    await db.commit()

    # 2. Fetch Chat History
    chat_history = await fetch_formatted_history(session_id, db)

    # 3. Call AI LLM
    try:
        ai_text_response = await ai_service.generate_chat_response(
            system_prompt=agent.prompt,
            chat_history=chat_history[:-1], # Pass history (excluding the message we just added)
            new_message=request.content
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

    # 4. Save AI Response to DB
    ai_msg = Message(session_id=session_id, role="assistant", content=ai_text_response)
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)

    # --- LOGGING LINE ---
    logger.info(f"Message Saved | ID: {ai_msg.id} | Agent: '{agent.name}' | Provider: {ai_service.provider.upper()} | Model: {ai_service.active_model_name}")
    # Return the AI's message object to the frontend
    return ai_msg


@router.post("/{session_id}/messages/voice", response_model=Message)
async def send_voice_message(
    session_id: uuid.UUID, 
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_session)
):
    """Handles asynchronous voice chatting (STT -> LLM -> TTS)."""
    session, agent = await get_session_and_agent(session_id, db)

    # 1. Save the uploaded user audio file safely
    user_audio_path = f"uploads/{uuid.uuid4()}_{file.filename}"
    async with aiofiles.open(user_audio_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    # 2. Convert User Audio to Text (STT - Whisper)
    try:
        user_text = await ai_service.transcribe_audio(user_audio_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription Error: {str(e)}")

    # 3. Save User Message to DB (including the audio path)
    user_msg = Message(session_id=session_id, role="user", content=user_text, audio_file_path=user_audio_path)
    db.add(user_msg)
    await db.commit()

    # 4. Fetch History & Call AI LLM
    chat_history = await fetch_formatted_history(session_id, db)
    try:
        ai_text_response = await ai_service.generate_chat_response(
            system_prompt=agent.prompt,
            chat_history=chat_history[:-1],
            new_message=user_text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI LLM Error: {str(e)}")

    # 5. Convert AI Text back to Audio (TTS)
    ai_audio_path = f"uploads/{uuid.uuid4()}_ai_response.mp3"
    try:
        await ai_service.text_to_speech(ai_text_response, ai_audio_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS Error: {str(e)}")

    # 6. Save AI Response to DB
    ai_msg = Message(session_id=session_id, role="assistant", content=ai_text_response, audio_file_path=ai_audio_path)
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)

    # --- LOGGING LINE ---
    logger.info(f"Voice Message Saved | ID: {ai_msg.id} | Agent: '{agent.name}' | Provider: {ai_service.provider.upper()} | Model: {ai_service.active_model_name}")
    # Return the AI's message (which now contains the text AND the audio file path)
    return ai_msg
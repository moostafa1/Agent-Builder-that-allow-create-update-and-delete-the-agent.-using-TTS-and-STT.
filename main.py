import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import our database initializer and our routers
from database import init_db
from routers import agents, sessions, chat

# ---------------------------------------------------------
# LIFESPAN (Startup & Shutdown)
# ---------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs exactly once when the server starts
    print("Starting up... Initializing database tables.")
    await init_db()
    
    # Ensure the uploads directory exists for audio files
    os.makedirs("uploads", exist_ok=True)
    
    yield # The server is now running and accepting requests
    
    # Code here would run when the server shuts down
    print("Shutting down...")

# ---------------------------------------------------------
# APP INITIALIZATION
# ---------------------------------------------------------
app = FastAPI(
    title="AI Agent Builder API",
    description="Backend for creating and chatting with custom AI agents using Groq and OpenAI.",
    version="1.0.0",
    lifespan=lifespan
)

# ---------------------------------------------------------
# CORS SECURITY
# ---------------------------------------------------------
# This allows your web frontend to make API requests to this backend without getting blocked.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# STATIC FILES (Serving the Audio)
# ---------------------------------------------------------
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ---------------------------------------------------------
# ROUTER REGISTRATION
# ---------------------------------------------------------
# Connect all the separate files we built into the main application
app.include_router(agents.router)
app.include_router(sessions.router)
app.include_router(chat.router)

# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------
@app.get("/health", tags=["Health"])
async def root():
    return {"status": "online", "message": "AI Agent API is running!"}

# ---------------------------------------------------------
# SERVE THE FRONTEND UI
# ---------------------------------------------------------
# IMPORTANT: This must be at the very bottom of the file!
# This tells FastAPI to serve your index.html from the 'frontend' folder when you visit the root IP.
app.mount("/", StaticFiles(directory="frontend", html=True), name="ui")
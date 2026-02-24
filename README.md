# 🤖 AI Agent Builder Backend

A high-performance, asynchronous REST API built with FastAPI that allows users to create, manage, and chat with custom AI agents. The system supports both text-based chatting and asynchronous voice interactions (Speech-to-Text and Text-to-Speech) using the latest models from Groq and OpenAI.

---

## ✨ Core Features

* **Custom AI Personas:** Create agents with unique system prompts to control their behavior.
* **Persistent Chat History:** Seamlessly manage multiple chat sessions per agent with full conversational memory.
* **Voice Interaction Pipeline:** Upload audio files to automatically transcribe (Whisper STT), generate an LLM response, and convert the response back to audio (TTS).
* **Multi-Provider AI Brain:** Easily switch between Gemini, OpenAI and Groq via environment variables for cost-effective testing and production scaling.
* **Fully Asynchronous:** Built from the ground up with async FastAPI and `aiosqlite` to handle concurrent user requests without blocking.

---

## 🛠️ Tech Stack

* **Framework:** FastAPI (Python 3.10+)
* **Database Engine:** SQLite (via `aiosqlite`)
* **ORM:** SQLModel (combines SQLAlchemy and Pydantic)
* **AI Providers:** OpenAI SDK, Groq API (Llama 3.3, Whisper Large v3)
* **Containerization:** Docker

---

## 🚀 Local Setup & Installation

### 1. Prerequisites

Ensure you have Python 3.10+ installed on your machine. 

### 2. Install Dependencies

Clone the repository or navigate to the project folder, then install the required libraries:

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

ACTIVE_AI_PROVIDER=groq
OPENAI_API_KEY=sk-your-openai-key-here
GROQ_API_KEY=gsk_your-groq-key-here

### 4. Run the Server

```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`. On the first run, it will automatically create the chatbot.db SQLite database and an uploads/ folder for audio files.

---

## 🐳 Docker Deployment

To run the backend in a fully isolated container without installing Python dependencies on your local machine:

### 1. Build the Image

```bash
docker build -t ai-agent-backend .
```

### 2. Run the Container

```bash
docker run -d -p 8000:8000 --env-file .env ai-agent-backend
```

## 📖 API Documentation & Testing

Once the server is running, you can interact with the API in two ways:

1. Interactive Swagger Docs: Visit `http://localhost:8000/docs` in your browser to view the auto-generated API documentation. You can test all endpoints directly from this page.

2. Postman Collection: Import the included AI_Agent_Collection.json file into Postman. This collection includes pre-configured variables to automatically track agent_id and session_id as you test the workflow.

---

## 📁 Project Structure

```text
chatbot_backend/
│
├── models.py           # (DONE) Database tables & data validation schemas
├── database.py         # Handles the SQLite connection and database sessions
├── ai_service.py       # The "Brain": Handles OpenAI, Gemini, Grok STT/TTS/LLM logic
│
├── routers/            # Folder containing our API endpoints
│   ├── agents.py       # Endpoints for creating/editing Agents
│   ├── sessions.py     # Endpoints for fetching chat history
│   └── chat.py         # Endpoints for sending text/voice to the AI
│
├── main.py             # The entry point that runs the FastAPI server
│
├── requirements.txt    # List of Python dependencies
└── Dockerfile          # For containerizing the app as requested
```

* `main.py`: Application entry point and router configuration.
* `database.py`: Async SQLite engine setup and session dependency.
* `models.py`: SQLModel definitions for Agent, Session, and Message.
* `ai_service.py`: The Factory pattern handling Groq/OpenAI integrations for LLM, STT, and TTS.
* `routers/`: Contains the modular API endpoints (agents.py, sessions.py, chat.py).
* `uploads/`: Automatically generated directory for storing user and AI audio files.

## Recorded Video

[![Watch the video](https://img.youtube.com/vi/T1Y5pO9odwM/maxresdefault.jpg)](https://www.youtube.com/watch?v=T1Y5pO9odwM)# Agent-Builder-that-allow-create-update-and-delete-the-agent.-using-TTS-and-STT.

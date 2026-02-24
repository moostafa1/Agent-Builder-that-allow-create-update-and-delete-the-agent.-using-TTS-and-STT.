from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

# The connection string for an async SQLite database
# This will create a file named "chatbot.db" in your project folder.
DATABASE_URL = "sqlite+aiosqlite:///./chatbot.db"

# Create the async engine
# echo=True prints all generated SQL queries to the terminal (great for debugging).
engine = create_async_engine(
    DATABASE_URL, 
    echo=True, 
    future=True
)

async def init_db():
    """
    Creates all the database tables defined in models.py.
    We will call this function when the FastAPI server starts up.
    """
    async with engine.begin() as conn:
        # run_sync is required because table creation is a synchronous operation 
        # happening inside our async environment.
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    """
    A FastAPI Dependency that provides a database session to our API routes.
    expire_on_commit=False prevents SQLAlchemy from throwing greenlet_spawn errors
    when we try to read data (like agent.prompt) after saving a message.
    """
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
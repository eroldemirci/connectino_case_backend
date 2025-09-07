from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Text, DateTime, func, select, cast, text
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "server_settings": {
            "jit": "off",
        }
    },
    pool_size=1,
    max_overflow=0,
    pool_pre_ping=False,
    pool_recycle=-1
)
SessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
Base = declarative_base()

class Note(Base):
    __tablename__ = "notes"
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), nullable=False)  # Use UUID type to match database
    title = Column(Text, nullable=False)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Pydantic models
class NoteCreate(BaseModel):
    title: str
    content: str = None

class NoteUpdate(BaseModel):
    title: str = None
    content: str = None

class NoteOut(BaseModel):
    id: str
    user_id: str
    title: str
    content: str = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - skip table creation for now
    yield
    # Shutdown (if needed)

app = FastAPI(lifespan=lifespan)

# Initialize database tables on first request
async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Database initialization error: {e}")
        # Continue anyway, tables might already exist

async def get_db():
    async with SessionLocal() as session:
        yield session

@app.get("/")
async def root():
    return {"message": "Notes API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/notes/", response_model=NoteOut)
async def create_note(user_id: str, note: NoteCreate, db: AsyncSession = Depends(get_db)):
    await init_db()  # Initialize tables if needed
    
    # Validate UUID format for user_id
    try:
        uuid.UUID(user_id)  # This will raise ValueError if not a valid UUID
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format. Must be a valid UUID.")
    
    new_note = Note(user_id=user_id, title=note.title, content=note.content)
    db.add(new_note)
    await db.commit()
    
    # Instead of refresh, return the note with current timestamp
    # This avoids the prepared statement issue with Supabase/pgbouncer
    from datetime import datetime, timezone
    current_time = datetime.now(timezone.utc)
    
    return NoteOut(
        id=str(new_note.id),
        user_id=str(new_note.user_id),
        title=new_note.title,
        content=new_note.content,
        created_at=str(current_time),
        updated_at=str(current_time)
    )

@app.get("/notes/", response_model=list[NoteOut])
async def list_notes(user_id: str, db: AsyncSession = Depends(get_db)):
    # Validate UUID format for user_id
    try:
        uuid.UUID(user_id)  # This will raise ValueError if not a valid UUID
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format. Must be a valid UUID.")
    
    # Use text SQL to avoid prepared statement issues with pgbouncer
    query = text("""
        SELECT id, user_id, title, content, created_at, updated_at 
        FROM notes 
        WHERE user_id = :user_id
    """)
    
    result = await db.execute(query, {"user_id": user_id})
    rows = result.fetchall()
    
    # Convert notes to NoteOut format with string timestamps
    note_list = []
    for row in rows:
        note_out = NoteOut(
            id=str(row.id),
            user_id=str(row.user_id),
            title=row.title,
            content=row.content,
            created_at=str(row.created_at),
            updated_at=str(row.updated_at)
        )
        note_list.append(note_out)
    
    return note_list

@app.get("/notes/{note_id}", response_model=NoteOut)
async def read_note(note_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    # Validate UUID format for note_id
    try:
        uuid.UUID(note_id)  # This will raise ValueError if not a valid UUID
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid note ID format. Must be a valid UUID.")
    
    # Validate UUID format for user_id
    try:
        uuid.UUID(user_id)  # This will raise ValueError if not a valid UUID
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format. Must be a valid UUID.")
    
    # Use text SQL to avoid prepared statement issues - check both note_id AND user_id
    query = text("""
        SELECT id, user_id, title, content, created_at, updated_at 
        FROM notes 
        WHERE id = :note_id AND user_id = :user_id
    """)
    
    result = await db.execute(query, {"note_id": note_id, "user_id": user_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Note not found or you don't have permission to access it")
    
    # Convert to NoteOut format with string timestamps
    return NoteOut(
        id=str(row.id),
        user_id=str(row.user_id),
        title=row.title,
        content=row.content,
        created_at=str(row.created_at),
        updated_at=str(row.updated_at)
    )

@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(note_id: str, user_id: str, note: NoteUpdate, db: AsyncSession = Depends(get_db)):
    # Validate UUID format for note_id
    try:
        uuid.UUID(note_id)  # This will raise ValueError if not a valid UUID
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid note ID format. Must be a valid UUID.")
    
    # Validate UUID format for user_id
    try:
        uuid.UUID(user_id)  # This will raise ValueError if not a valid UUID
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format. Must be a valid UUID.")
    
    # First check if note exists AND belongs to the user
    check_query = text("SELECT id FROM notes WHERE id = :note_id AND user_id = :user_id")
    check_result = await db.execute(check_query, {"note_id": note_id, "user_id": user_id})
    if not check_result.fetchone():
        raise HTTPException(status_code=404, detail="Note not found or you don't have permission to access it")
    
    # Update fields
    update_data = note.dict(exclude_unset=True)
    if not update_data:
        # No fields to update, just return current note
        query = text("""
            SELECT id, user_id, title, content, created_at, updated_at 
            FROM notes 
            WHERE id = :note_id AND user_id = :user_id
        """)
        result = await db.execute(query, {"note_id": note_id, "user_id": user_id})
        row = result.fetchone()
        return NoteOut(
            id=str(row.id),
            user_id=str(row.user_id),
            title=row.title,
            content=row.content,
            created_at=str(row.created_at),
            updated_at=str(row.updated_at)
        )
    
    # Build update query dynamically
    set_clauses = []
    params = {"note_id": note_id}
    
    if "title" in update_data:
        set_clauses.append("title = :title")
        params["title"] = update_data["title"]
    
    if "content" in update_data:
        set_clauses.append("content = :content")
        params["content"] = update_data["content"]
    
    set_clauses.append("updated_at = NOW()")
    
    # Add user_id to params for the WHERE clause
    params["update_user_id"] = user_id
    
    update_query = text(f"""
        UPDATE notes 
        SET {', '.join(set_clauses)}
        WHERE id = :note_id AND user_id = :update_user_id
        RETURNING id, user_id, title, content, created_at, updated_at
    """)
    
    result = await db.execute(update_query, params)
    await db.commit()
    row = result.fetchone()
    
    return NoteOut(
        id=str(row.id),
        user_id=str(row.user_id),
        title=row.title,
        content=row.content,
        created_at=str(row.created_at),
        updated_at=str(row.updated_at)
    )

@app.delete("/notes/{note_id}")
async def delete_note(note_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    # Validate UUID format for note_id
    try:
        uuid.UUID(note_id)  # This will raise ValueError if not a valid UUID
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid note ID format. Must be a valid UUID.")
    
    # Validate UUID format for user_id
    try:
        uuid.UUID(user_id)  # This will raise ValueError if not a valid UUID
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format. Must be a valid UUID.")
    
    # Use text SQL to avoid prepared statement issues - check both note_id AND user_id
    delete_query = text("DELETE FROM notes WHERE id = :note_id AND user_id = :user_id")
    result = await db.execute(delete_query, {"note_id": note_id, "user_id": user_id})
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found or you don't have permission to delete it")
    
    return {"ok": True}
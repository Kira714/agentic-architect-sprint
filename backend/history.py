"""
History and logging for protocol generation.
Stores all queries and generated protocols in the database.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from database import Base, AsyncSessionLocal
from datetime import datetime
from typing import Optional, Dict, Any
import json


class ProtocolHistory(Base):
    """History table for storing all protocol generation requests and results"""
    __tablename__ = "protocol_history"
    
    id = Column(String, primary_key=True)  # thread_id
    user_query = Column(Text, nullable=False)
    user_intent = Column(String, nullable=True)
    user_specifics = Column(JSON, nullable=True)
    final_protocol = Column(Text, nullable=True)
    state_snapshot = Column(JSON, nullable=True)  # Full state at completion
    status = Column(String, nullable=False)  # created, running, halted, approved, completed, error
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


async def log_protocol_creation(thread_id: str, user_query: str, user_intent: str, user_specifics: Optional[Dict[str, Any]] = None):
    """Log a new protocol creation request"""
    try:
        async with AsyncSessionLocal() as session:
            history_entry = ProtocolHistory(
                id=thread_id,
                user_query=user_query,
                user_intent=user_intent,
                user_specifics=user_specifics or {},
                status="created",
                started_at=datetime.now()
            )
            session.add(history_entry)
            await session.commit()
            print(f"[HISTORY] Logged protocol creation: {thread_id}")
    except Exception as e:
        print(f"[HISTORY] Warning: Could not log protocol creation: {e}")


async def update_protocol_status(thread_id: str, status: str, final_protocol: Optional[str] = None, state_snapshot: Optional[Dict[str, Any]] = None):
    """Update protocol status and final result"""
    try:
        async with AsyncSessionLocal() as session:
            # Try to get existing entry
            result = await session.execute(select(ProtocolHistory).where(ProtocolHistory.id == thread_id))
            entry = result.scalar_one_or_none()
            
            if entry:
                entry.status = status
                if final_protocol:
                    entry.final_protocol = final_protocol
                if state_snapshot:
                    entry.state_snapshot = state_snapshot
                if status in ["completed", "approved"]:
                    entry.completed_at = datetime.now()
                if status == "approved":
                    entry.approved_at = datetime.now()
                entry.updated_at = datetime.now()
            else:
                # Create new entry if doesn't exist
                entry = ProtocolHistory(
                    id=thread_id,
                    user_query="",
                    status=status,
                    final_protocol=final_protocol,
                    state_snapshot=state_snapshot or {}
                )
                session.add(entry)
            
            await session.commit()
            print(f"[HISTORY] Updated protocol status: {thread_id} -> {status}")
    except Exception as e:
        print(f"[HISTORY] Warning: Could not update protocol status: {e}")


async def get_protocol_history(limit: int = 50):
    """Get recent protocol history"""
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ProtocolHistory)
                .order_by(ProtocolHistory.created_at.desc())
                .limit(limit)
            )
            entries = result.scalars().all()
            return [
                {
                    "thread_id": entry.id,
                    "user_query": entry.user_query,
                    "status": entry.status,
                    "started_at": entry.started_at.isoformat() if entry.started_at else None,
                    "completed_at": entry.completed_at.isoformat() if entry.completed_at else None,
                }
                for entry in entries
            ]
    except Exception as e:
        print(f"[HISTORY] Warning: Could not retrieve history: {e}")
        return []


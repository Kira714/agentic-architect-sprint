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
    """
    Log a new protocol creation request to the database.
    
    This function creates a new entry in the protocol_history table when a user
    requests a CBT protocol. It stores the initial request information including
    the user query, intent, and any user-specific information collected.
    
    This is a non-blocking operation - if it fails, the workflow continues.
    Errors are logged but don't interrupt the protocol creation process.
    
    Args:
        thread_id: Unique identifier for this protocol request (used as primary key)
        user_query: The user's original request/query
        user_intent: The classified intent
        user_specifics: Optional dictionary of user-specific information
        
    Note:
        This function uses try-except to ensure failures don't break the workflow.
        Errors are logged with a warning message.
    """
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
    """
    Update protocol status and final result in the database.
    
    This function updates an existing protocol_history entry with the current status,
    final protocol (if completed), and optionally a full state snapshot. It's called
    at various points in the workflow lifecycle:
    - When workflow halts for human review
    - When workflow completes
    - When human approves the protocol
    
    If the entry doesn't exist, it creates a new one. This ensures history is
    maintained even if log_protocol_creation failed earlier.
    
    This is a non-blocking operation - if it fails, the workflow continues.
    Errors are logged but don't interrupt the protocol creation process.
    
    Args:
        thread_id: Unique identifier for this protocol request
        status: Current status ("created", "running", "halted", "approved", "completed", "error")
        final_protocol: Optional final protocol text (if completed)
        state_snapshot: Optional complete state snapshot for full history
        
    Note:
        This function uses try-except to ensure failures don't break the workflow.
        Errors are logged with a warning message. Timestamps (completed_at, approved_at)
        are automatically set based on the status.
    """
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
    """
    Get recent protocol history from the database.
    
    This function retrieves the most recent protocol creation requests from the
    protocol_history table, ordered by creation date (newest first). It's useful
    for displaying history in the UI or for administrative purposes.
    
    This is a non-blocking operation - if it fails, returns an empty list.
    Errors are logged but don't interrupt the caller.
    
    Args:
        limit: Maximum number of entries to return (default: 50)
        
    Returns:
        A list of dictionaries, each containing:
        - thread_id: Unique identifier
        - user_query: Original user query
        - status: Current status
        - started_at: When the request was started (ISO format)
        - completed_at: When the request was completed (ISO format, or None)
        
    Note:
        This function uses try-except to ensure failures don't break the caller.
        Errors are logged with a warning message, and an empty list is returned.
    """
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


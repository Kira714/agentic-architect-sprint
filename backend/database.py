"""
Database setup and checkpointing for LangGraph
Supports both SQLite and PostgreSQL
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from sqlalchemy.pool import Pool
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

Base = declarative_base()

# Database URL from environment
# In Docker: uses postgres service name (postgres:5432)
# Local dev outside Docker: use localhost:8007
# Default: PostgreSQL in Docker
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://cerina:cerina_password@postgres:5432/cerina_foundry")

# Determine database type
IS_POSTGRES = DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres")

# Create async engine
if IS_POSTGRES:
    # For PostgreSQL, use asyncpg
    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
else:
    # For SQLite
    engine = create_async_engine(DATABASE_URL, echo=False)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_checkpointer():
    """Create and initialize LangGraph checkpointer with proper persistence"""
    logger.info(f"[DATABASE] Creating checkpointer, IS_POSTGRES: {IS_POSTGRES}, DATABASE_URL: {DATABASE_URL[:50]}...")
    
    # PRIORITY: Try persistent checkpointers first (for production)
    # Only fall back to MemorySaver if all persistent options fail
    
    # Try SQLAlchemy checkpointer (works with both SQLite and PostgreSQL) - PREFERRED
    try:
        logger.info("[DATABASE] Attempting to use AsyncSqlAlchemySaver (works with both SQLite and PostgreSQL)")
        from langgraph.checkpoint.sqlalchemy import AsyncSqlAlchemySaver
        checkpointer = AsyncSqlAlchemySaver(engine)
        await checkpointer.setup()
        logger.info("[DATABASE] ✅ Successfully created AsyncSqlAlchemySaver checkpointer (PERSISTENT)")
        return checkpointer
    except ImportError as e:
        logger.warning(f"[DATABASE] ❌ AsyncSqlAlchemySaver ImportError: {e}")
    except Exception as e:
        logger.warning(f"[DATABASE] ❌ AsyncSqlAlchemySaver error: {e}")
    
    # Try alternative import paths
    try:
        logger.info("[DATABASE] Attempting alternative import for AsyncSqlAlchemySaver")
        from langgraph_checkpoint.sqlalchemy import AsyncSqlAlchemySaver
        checkpointer = AsyncSqlAlchemySaver(engine)
        await checkpointer.setup()
        logger.info("[DATABASE] ✅ Successfully created AsyncSqlAlchemySaver checkpointer (alt import, PERSISTENT)")
        return checkpointer
    except Exception as e:
        logger.warning(f"[DATABASE] ❌ Alternative import failed: {e}")
    
    # For PostgreSQL, try PostgreSQL-specific checkpointer
    if IS_POSTGRES:
        try:
            logger.info("[DATABASE] Attempting PostgreSQL-specific checkpointer")
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            checkpointer = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
            await checkpointer.setup()
            logger.info("[DATABASE] ✅ Successfully created AsyncPostgresSaver checkpointer (PERSISTENT)")
            return checkpointer
        except Exception as e2:
            logger.warning(f"[DATABASE] ❌ PostgreSQL checkpointer (aio) failed: {e2}")
            try:
                from langgraph.checkpoint.postgres import AsyncPostgresSaver
                checkpointer = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
                await checkpointer.setup()
                logger.info("[DATABASE] ✅ Successfully created AsyncPostgresSaver checkpointer (alt, PERSISTENT)")
                return checkpointer
            except Exception as e3:
                logger.warning(f"[DATABASE] ❌ PostgreSQL checkpointer (alt) failed: {e3}")
    
    # Fallback to MemorySaver ONLY if all persistent options fail
    logger.warning("[DATABASE] ⚠️ All persistent checkpointers failed, using MemorySaver (NO PERSISTENCE - not suitable for production)")
    try:
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
        logger.warning("[DATABASE] ⚠️ Using MemorySaver - state will be lost on restart!")
        return checkpointer
    except ImportError as e:
        logger.error(f"[DATABASE] ❌ Even MemorySaver failed: {e}")
        raise


async def get_db_session():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

"""
Database Configuration and Session Management
Supports both shared database with RLS and isolated database per tenant
"""
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings

# Base class for all models
Base = declarative_base()

# Synchronous Engine (for migrations and sync operations)
sync_engine = create_engine(
    settings.database_url_sync,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
    echo=settings.ENABLE_SQL_LOGGING,
    poolclass=QueuePool,
)

# Asynchronous Engine (for API operations)
async_engine = create_async_engine(
    settings.database_url_async,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
    echo=settings.ENABLE_SQL_LOGGING,
    poolclass=QueuePool,
)

# Session makers
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
    class_=Session
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class TenantDatabaseManager:
    """
    Manages database connections for multi-tenant architecture
    Supports both shared database (RLS) and isolated database modes
    """

    def __init__(self):
        self.engines = {}  # Cache for tenant-specific engines
        self.mode = settings.TENANCY_MODE

    def get_tenant_engine(self, tenant_id: str):
        """Get or create engine for specific tenant (isolated mode only)"""
        if self.mode != "isolated":
            return async_engine

        if tenant_id not in self.engines:
            # Create tenant-specific database URL
            tenant_db_url = self._build_tenant_db_url(tenant_id)
            self.engines[tenant_id] = create_async_engine(
                tenant_db_url,
                pool_size=10,
                max_overflow=5,
                pool_pre_ping=True,
            )

        return self.engines[tenant_id]

    def _build_tenant_db_url(self, tenant_id: str) -> str:
        """Build database URL for isolated tenant database"""
        base_url = str(settings.DATABASE_URL)
        # Replace database name with tenant-specific name
        parts = base_url.rsplit("/", 1)
        tenant_db_name = f"{settings.DEFAULT_TENANT_DB_PREFIX}{tenant_id}"
        return f"{parts[0]}/{tenant_db_name}"

    async def create_tenant_database(self, tenant_id: str):
        """Create a new isolated database for tenant"""
        if self.mode != "isolated":
            return

        # Connect to default database to create new tenant database
        async with async_engine.begin() as conn:
            await conn.execute(
                text(f"CREATE DATABASE {settings.DEFAULT_TENANT_DB_PREFIX}{tenant_id}")
            )

        # Run migrations on new tenant database
        tenant_engine = self.get_tenant_engine(tenant_id)
        async with tenant_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tenant_database(self, tenant_id: str):
        """Drop tenant database (use with caution!)"""
        if self.mode != "isolated":
            return

        # Close existing connections
        if tenant_id in self.engines:
            await self.engines[tenant_id].dispose()
            del self.engines[tenant_id]

        # Drop database
        async with async_engine.begin() as conn:
            await conn.execute(
                text(f"DROP DATABASE IF EXISTS {settings.DEFAULT_TENANT_DB_PREFIX}{tenant_id}")
            )


# Global tenant database manager
tenant_db_manager = TenantDatabaseManager()


def set_tenant_context(db_session: Session, tenant_id: Optional[str]):
    """
    Set tenant context for Row-Level Security (RLS)
    This ensures all queries are automatically filtered by tenant_id
    """
    if settings.TENANCY_MODE == "shared" and tenant_id:
        # Set PostgreSQL session variable for RLS
        db_session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )


async def set_tenant_context_async(db_session: AsyncSession, tenant_id: Optional[str]):
    """Async version of set_tenant_context"""
    if settings.TENANCY_MODE == "shared" and tenant_id:
        await db_session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )


# Synchronous session dependency
@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Dependency for getting synchronous database sessions"""
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Asynchronous session dependency
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting asynchronous database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Tenant-aware async session
@asynccontextmanager
async def get_tenant_db(tenant_id: Optional[str] = None) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with tenant context set
    Automatically applies RLS policies or connects to tenant database
    """
    if settings.TENANCY_MODE == "isolated" and tenant_id:
        engine = tenant_db_manager.get_tenant_engine(tenant_id)
        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    else:
        async with AsyncSessionLocal() as session:
            try:
                if tenant_id:
                    await set_tenant_context_async(session, tenant_id)
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


async def init_db():
    """Initialize database (create tables)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close all database connections"""
    await async_engine.dispose()
    # Close tenant engines in isolated mode
    for engine in tenant_db_manager.engines.values():
        await engine.dispose()


# Event listeners for connection pool management
@event.listens_for(sync_engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Event listener for new connections"""
    connection_record.info["pid"] = dbapi_conn.get_backend_pid()


@event.listens_for(sync_engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Event listener for connection checkout"""
    # Reset tenant context on connection reuse
    pid = connection_record.info.get("pid")
    if pid is not None:
        cursor = dbapi_conn.cursor()
        cursor.execute("RESET app.current_tenant_id")
        cursor.close()

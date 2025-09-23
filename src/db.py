# db.py
# pragma: no mutate

import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeMeta, Session, declarative_base, sessionmaker

from src.config import settings

logger = logging.getLogger(__name__)  # pragma: no mutate

# Create the sync engine
engine = create_engine(settings.database_url, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():  # type: ignore
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Annotated version for type-hinting in your FastAPI endpoints
SessionDep = Annotated[Session, Depends(get_db)]  # pragma: no mutate

# Create async engine and session maker
async_engine = create_async_engine(settings.async_database_url, echo=False)
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_async_db():  # type: ignore
    async_db = async_session_maker()
    try:
        yield async_db
    finally:
        await async_db.close()


# Annotated version for type-hinting in your FastAPI endpoints
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_db)]  # pragma: no mutate

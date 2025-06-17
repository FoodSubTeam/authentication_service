from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from contextlib import asynccontextmanager

database_url = os.getenv("DATABASE_URL")

engine = create_async_engine(database_url, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
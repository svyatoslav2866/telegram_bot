from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger, ForeignKey
from datetime import datetime
from sqlalchemy.sql import func

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger, unique=True)
    username = Column(String(50))
    full_name = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"User(id={self.id}, telegram_id={self.tg_id}, username={self.username})"

class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    name = Column(String(50))
    color = Column(String(20), default="#3498db")

class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tg_id'))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    priority = Column(Integer, default=2)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"Tasks(id={self.id}, name={self.name}, priority={self.priority})"

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session():
    async with async_session() as session:
        yield session
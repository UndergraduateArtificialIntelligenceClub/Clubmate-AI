from datetime import datetime
from sqlalchemy import VARCHAR, DateTime, Integer, String, Text, func, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, declarative_base

DATABASE_URL = "postgresql+asyncpg://soy:groovy@localhost:5432/CMAI" # Make this a .env in prod # !!! 

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_size=20, # Need to adjust this when stress testing
    max_overflow=40
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

class UserNotFoundByDiscordID(Exception):
    def __init__(self, discord_id: str) -> None:
        self.discord_id = discord_id


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)

    role: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1", default=1 # Again refer to ./customtypes.py to see if it matches the pleb role. Wouldn't want default role to be admin would we hmmmm...
    )

    discord_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)

    email: Mapped[str] = mapped_column(Text) # must have ualberta email to confirm they're a student

    name: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id}, username{self.username} role={self.role}>"


async def add_user_to_db(username: str, role: int, discord_id: str, email: str, name: str):
    async with async_session() as session:
        user = User(username=username, role=role, discord_id=discord_id, email=email, name=name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"Added {user.id}: {user.username} | {user.discord_id}")

async def get_user_from_db(discord_id: str) -> User:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.discord_id==discord_id))
        user = result.scalar_one_or_none()
        if user == None:
            raise UserNotFoundByDiscordID(discord_id=discord_id)
        return user


async def list_users_from_db() -> set[str]:
    async with async_session() as session:
        result = await session.execute(select(User).order_by(User.id))
        users = result.scalars().all()
        ret = set()
        print("\nAll users:")
        for u in users:
            ret.add(f"-- {u.id} | {u.name} | ({u.email})")
        return ret

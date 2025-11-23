from datetime import datetime

from sqlalchemy import (
    JSON,
    VARCHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declarative_base,
    mapped_column,
    sessionmaker,
)

DATABASE_URL = "postgresql+asyncpg://soy:groovy@localhost:5432/CMAI"  # Make this a .env in prod # !!!

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_size=20,  # Need to adjust this when stress testing
    max_overflow=40,
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

    username: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )

    role: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
        default=1,  # Again refer to ./customtypes.py to see if it matches the pleb role. Wouldn't want default role to be admin would we hmmmm...
    )

    discord_id: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False, index=True
    )

    email: Mapped[str] = mapped_column(
        Text
    )  # must have ualberta email to confirm they're a student

    name: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id}, username{self.username} role={self.role}>"


class Meeting(Base):
    __tablename__ = "meetings"

    # Constraints
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="meetings_time_valid"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    organizer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    location: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    meeting_link: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    attendees: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )

    google_calendar_event_id: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="scheduled",
        server_default="scheduled",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


async def add_user_to_db(user: User):
    async with async_session() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"Added {user.id}: {user.username} | {user.discord_id}")


async def get_user_from_db(discord_id: str) -> User:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.discord_id == discord_id)
        )
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


async def add_meeting_to_db(m: Meeting):
    async with async_session() as session:
        session.add(Meeting)
        await session.commit()
        await session.refresh(m)

    print(
        f"""
        added meeting:
        {m.organizer_id}
        {m.title}
        {m.description}
        {m.start_time}
        {m.end_time}
        {m.location}
        {m.meeting_link}
        {m.attendees}
        {m.google_calendar_event_id}
        {m.status}
        """
    )

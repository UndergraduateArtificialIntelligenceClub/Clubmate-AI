from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

# Use the URL from settings (or your hardcoded one if preferred)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True,
    pool_size=20,
    max_overflow=40,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


async def init_db():
    # Import all models here to ensure they are registered with Base.metadata
    from app.models.base import Base
    from app.models import user, contact, file, secure, audit  # noqa: F401

    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Uncomment to reset DB
        await conn.run_sync(Base.metadata.create_all)

    # Seed Dev Admin
    from app.models.user import User
    async with async_session_factory() as session:
        user = await session.get(User, 1)
        if not user:
            print("Seeding DevAdmin...")
            dev_admin = User(
                id=1,
                username="DevAdmin",
                discord_id="000000",
                role=0
            )
            session.add(dev_admin)
            await session.commit()
            print("Seeded DevAdmin user.")

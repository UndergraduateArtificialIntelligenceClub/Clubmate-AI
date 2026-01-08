import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://soy:groovy@127.0.0.1:5433/CMAI"

async def check_db():
    print(f"Connecting to {DATABASE_URL} ...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("SUCCESS: Connected to DB!")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())

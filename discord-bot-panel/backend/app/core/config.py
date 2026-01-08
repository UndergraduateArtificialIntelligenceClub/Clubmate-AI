import os


class Settings:
    # Using the password you confirmed works
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:admin123@localhost:5432/discord_panel",
    )

    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_this")
    ALGORITHM = "HS256"

    # Ensure you ran the python command to generate this base64 string
    AES_MASTER_KEY = os.getenv("AES_MASTER_KEY")

    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    BASE_URL = "http://localhost:8000"


settings = Settings()

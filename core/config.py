import os
from dotenv import load_dotenv

load_dotenv()

DB_USERNAME: str = os.getenv("DB_USERNAME", "postgres")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
DB_HOSTNAME: str = os.getenv("DB_HOSTNAME", "localhost")
DB_PORT: str = os.getenv("DB_PORT", "5432")
DATABASE: str = os.getenv("DATABASE", "plan")

DATABASE_URL: str = (
    f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DATABASE}"
)

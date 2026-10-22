from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()


@dataclass(frozen=True)
class Settings:
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "ecomm_db")
    postgres_user: str = os.getenv("POSTGRES_USER", "ecomm_admin")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "ecomm_passwd")


settings = Settings()

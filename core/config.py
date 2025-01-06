from logging import getLogger
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings

logger = getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent

DB_PATH = BASE_DIR / "db_sql.db"

class DataBaseConfig(BaseModel):
    url: str = f"sqlite+aiosqlite:///{DB_PATH}"
    echo: bool = True

class AuthJWT(BaseModel):

    private_key_path: Path = BASE_DIR / "cert" / "private.pem" 
    public_key_path: Path = BASE_DIR / "cert" / "public.pem"
    algorithms: str = "RS256" #алгоритм шифрования
    access_token_expire_day: int = 30


class Settings(BaseSettings):
    db: DataBaseConfig = DataBaseConfig()
    
    auth_jwt: AuthJWT = AuthJWT()


settings = Settings()

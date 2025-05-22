from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
from functools import lru_cache
import json


class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A modern chat API built with FastAPI"
    API_V1_PREFIX: str
    
    # Environment
    DEBUG: bool
    
    # PostgreSQL Configuration
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    
    # MongoDB Configuration
    MONGODB_URL: str
    MONGODB_DB: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # Redis Configuration
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    CACHE_EXPIRE_TIME: int
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str]
    
    # Python Path
    PYTHONPATH: Optional[str] = None
    
    # Database
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: str | None, values: dict) -> str:
        if isinstance(v, str):
            return v
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_HOST')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            if field_name == "ALLOWED_ORIGINS":
                try:
                    return json.loads(raw_val)
                except json.JSONDecodeError:
                    return [origin.strip() for origin in raw_val.split(",")]
            return raw_val


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Returns:
        Settings: Application settings
    """
    return Settings()


# Create global settings instance
settings = get_settings() 
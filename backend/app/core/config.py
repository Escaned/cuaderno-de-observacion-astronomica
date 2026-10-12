from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./riguel.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # Timezone
    timezone: str = "Europe/Madrid"

    # Observatory (used for seed if table empty)
    obs_nombre: str = "Riguel"
    obs_lat: float = 40.4168
    obs_lon: float = -3.7038
    obs_alt: float = 650.0
    obs_tz: str = "Europe/Madrid"

    # Images
    images_dir: str = "./data/imagenes"
    images_url_prefix: str = "/imagenes"

    # Security (optional, for LAN exposure)
    api_key: Optional[str] = None


settings = Settings()
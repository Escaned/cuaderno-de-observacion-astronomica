from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # The defaults below are relative paths, which is what running from source
    # relies on: arrancar.bat does `cd backend` first. The packaged launcher cannot
    # rely on the working directory, so it sets DATABASE_URL, IMAGES_DIR, API_HOST
    # and API_PORT before this module is imported. Environment variables take
    # precedence over the .env file, so those win when they are present.

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
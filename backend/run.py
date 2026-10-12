import uvicorn
from app.core.config import settings


def main():
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
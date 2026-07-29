from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    log_level: str = "info"
    frontend_api_base_url: str = "http://localhost:8000"
    debug: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

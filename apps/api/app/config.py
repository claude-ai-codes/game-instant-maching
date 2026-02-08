from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://gameapp:gameapp@localhost:5432/gameapp"
    session_secret: str = "change-me-to-a-random-secret-at-least-32-chars"
    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"

    recruitment_expiry_minutes: int = 60
    room_expiry_hours: int = 24
    message_ttl_hours: int = 24

    turnstile_secret_key: str = ""
    turnstile_site_key: str = ""

    # Auto-suspension: suspend user after this many reports
    report_threshold_for_suspension: int = 3
    suspension_duration_hours: int = 24

    # Admin
    admin_secret: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

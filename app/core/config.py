from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BuildCRM"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "postgresql://postgres:postgres@localhost:5432/buildcrm"

    tg_bot_token: str = ""
    tg_task_chat_id: int = 0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

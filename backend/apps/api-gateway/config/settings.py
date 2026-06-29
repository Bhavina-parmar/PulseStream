from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str 
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int 
    redis_url: str
    kafka_bootstrap_servers: str
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
settings = Settings()






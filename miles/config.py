from pydantic import Field

redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
database_url: str = Field(
    ..., env="DATABASE_URL"
)  # e.g. postgres://user:pass@host:5432/db

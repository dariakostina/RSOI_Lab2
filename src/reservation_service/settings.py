from pydantic_settings import BaseSettings
from sqlmodel import Field


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")

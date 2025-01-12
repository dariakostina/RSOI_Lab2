from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    library_service_url: str = Field(alias="LIBRARY_SERVICE_URL")
    reservation_service_url: str = Field(alias="RESERVATION_SERVICE_URL")
    rating_service_url: str = Field(alias="RATING_SERVICE_URL")

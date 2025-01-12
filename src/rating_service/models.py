from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Rating(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    stars: int = Field(default=50)  # от 0 до 100


class RatingResponse(BaseModel):
    stars: int


class ErrorResponse(BaseModel):
    error: str

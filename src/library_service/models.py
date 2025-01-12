from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Library(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    library_uid: UUID = Field(default_factory=uuid4, unique=True, index=True)
    name: str
    city: str
    address: str


class BookCondition(StrEnum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    BAD = "BAD"


class Book(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    book_uid: UUID = Field(default_factory=uuid4, unique=True, index=True)
    name: str
    author: str | None = None
    genre: str | None = None
    condition: BookCondition = Field(default=BookCondition.EXCELLENT)


class LibraryBook(SQLModel, table=True):
    book_id: int | None = Field(foreign_key="book.id", primary_key=True)
    library_id: int | None = Field(foreign_key="library.id", primary_key=True)
    available_count: int = Field(default=0)


class LibraryResponse(BaseModel):
    libraryUid: UUID
    name: str
    address: str
    city: str


class BookResponse(BaseModel):
    bookUid: UUID
    name: str
    author: str
    genre: str
    condition: str
    availableCount: int


class ErrorResponse(BaseModel):
    error: str


class ReduceBookCountResponse(BaseModel):
    ok: bool


class LibrariesResponse(BaseModel):
    page: int
    pageSize: int
    totalElements: int
    items: list[LibraryResponse]


class LibraryBooksResponse(BaseModel):
    page: int
    pageSize: int
    totalElements: int
    items: list[BookResponse]

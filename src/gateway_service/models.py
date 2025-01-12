from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, SerializationInfo, field_serializer

from library_service.models import (
    BookCondition,
    BookResponse,
    LibraryResponse,
)
from rating_service.models import RatingResponse


# ----------------- Схемы -----------------
class TakeBookRequest(BaseModel):
    bookUid: UUID
    libraryUid: UUID
    tillDate: datetime


class TakeBookResponse(BaseModel):
    class BookResponse(BaseModel):
        bookUid: UUID
        name: str
        author: str
        genre: str

    reservationUid: UUID
    status: str
    startDate: datetime
    tillDate: datetime
    book: BookResponse
    library: LibraryResponse
    rating: RatingResponse

    @field_serializer("startDate", "tillDate")
    def serialize_dt(self, dt: datetime, _: SerializationInfo):
        return dt.strftime("%Y-%m-%d")


class ReturnBookRequest(BaseModel):
    condition: BookCondition
    date: datetime


class BookReservationResponse(BaseModel):
    reservationUid: UUID
    status: str
    startDate: datetime
    tillDate: datetime
    book: BookResponse
    library: LibraryResponse

    @field_serializer("startDate", "tillDate")
    def serialize_dt(self, dt: datetime, _: SerializationInfo):
        return dt.strftime("%Y-%m-%d")

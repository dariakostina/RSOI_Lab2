import enum
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class ReservationStatus(str, enum.Enum):
    RENTED = "RENTED"
    RETURNED = "RETURNED"
    EXPIRED = "EXPIRED"


class Reservation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    reservation_uid: UUID = Field(default_factory=uuid4, unique=True, index=True)
    username: str
    book_uid: UUID
    library_uid: UUID
    status: ReservationStatus = Field(default=ReservationStatus.RENTED)
    start_date: datetime
    till_date: datetime


class ReservationRequest(SQLModel):
    reservationUid: UUID | None
    username: str
    bookUid: UUID
    libraryUid: UUID
    status: ReservationStatus
    startDate: datetime
    tillDate: datetime


# Pydantic-схема для ответа
class ReservationResponse(SQLModel):
    reservationUid: UUID
    username: str
    bookUid: UUID
    libraryUid: UUID
    status: ReservationStatus
    startDate: datetime
    tillDate: datetime


class ReturnBookResponse(BaseModel):
    status: ReservationStatus


class ErrorResponse(BaseModel):
    error: str

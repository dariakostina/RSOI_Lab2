from contextlib import asynccontextmanager
from datetime import datetime
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException
from sqlmodel import Session, SQLModel, create_engine

from reservation_service.models import (
    ErrorResponse,
    Reservation,
    ReservationRequest,
    ReservationResponse,
    ReservationStatus,
    ReturnBookResponse,
)
from reservation_service.repositories import ReservationRepository
from reservation_service.settings import Settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


@lru_cache(maxsize=1)
def get_engine():
    return create_engine(Settings().database_url, echo=False)


def init_db():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_repository():
    engine = get_engine()
    with Session(engine) as session:
        yield ReservationRepository(session)


RepoDep = Annotated[ReservationRepository, Depends(get_repository)]


router = APIRouter(prefix="/api/v1", lifespan=lifespan)


@router.get("/reservations", response_model=list[ReservationResponse])
def get_user_reservations(
    repo: RepoDep, x_user_name: str = Header(..., alias="X-User-Name")
):
    res = repo.get_reservations_by_username(x_user_name)
    return [
        ReservationResponse(
            reservationUid=r.reservation_uid,
            username=r.username,
            bookUid=r.book_uid,
            libraryUid=r.library_uid,
            status=r.status,
            startDate=r.start_date,
            tillDate=r.till_date,
        )
        for r in res
    ]


@router.get(
    "/reservations/{reservation_uid}",
    response_model=ReservationResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_reservation(
    repo: RepoDep,
    reservation_uid: UUID,
    x_user_name: str = Header(..., alias="X-User-Name"),
):
    r = repo.get_reservation_by_uid(reservation_uid)
    if not r or r.username != x_user_name:
        raise HTTPException(404, "Reservation not found")
    return ReservationResponse(
        reservationUid=r.reservation_uid,
        username=r.username,
        bookUid=r.book_uid,
        libraryUid=r.library_uid,
        status=r.status,
        startDate=r.start_date,
        tillDate=r.till_date,
    )


@router.post("/reservations", response_model=ReservationResponse)
def create_reservation(
    repo: RepoDep,
    reservation_data: ReservationRequest,
    x_user_name: str = Header(..., alias="X-User-Name"),
):
    """
    Создаёт новую бронь (книгу "взяли").
    Предполагается, что Gateway уже проверил лимит книг и т.д.
    """
    new_res = Reservation(
        username=x_user_name,
        book_uid=reservation_data.bookUid,
        library_uid=reservation_data.libraryUid,
        status=ReservationStatus.RENTED,
        start_date=reservation_data.startDate,
        till_date=reservation_data.tillDate,
    )
    repo.create_reservation(new_res)

    return ReservationResponse(
        reservationUid=new_res.reservation_uid,
        username=new_res.username,
        bookUid=new_res.book_uid,
        libraryUid=new_res.library_uid,
        status=new_res.status,
        startDate=new_res.start_date,
        tillDate=new_res.till_date,
    )


@router.post(
    "/reservations/{reservation_uid}/return",
    response_model=ReturnBookResponse,
    responses={404: {"model": ErrorResponse}},
)
def return_book(
    repo: RepoDep,
    reservation_uid: UUID,
    date: datetime,
    x_user_name: str = Header(..., alias="X-User-Name"),
):
    """
    Возврат книги. Изменяем статус на RETURNED или EXPIRED.
    """
    r = repo.get_reservation_by_uid(reservation_uid)
    if not r or r.username != x_user_name:
        raise HTTPException(404, "Reservation not found")

    if date > r.till_date:
        r.status = ReservationStatus.EXPIRED
    else:
        r.status = ReservationStatus.RETURNED

    repo.update_reservation(r)
    return ReturnBookResponse(status=r.status)


@router.post(
    "/reservations/{reservation_uid}/return/undo",
    response_model=ReturnBookResponse,
    responses={404: {"model": ErrorResponse}},
)
def undo_return_book(
    repo: RepoDep,
    reservation_uid: UUID,
    x_user_name: str = Header(..., alias="X-User-Name"),
):
    """
    Отмена возврата книги. Изменяем статус на RENTED.
    """
    r = repo.get_reservation_by_uid(reservation_uid)
    if not r or r.username != x_user_name:
        raise HTTPException(404, "Reservation not found")

    r.status = ReservationStatus.RENTED

    repo.update_reservation(r)
    return ReturnBookResponse(status=r.status)

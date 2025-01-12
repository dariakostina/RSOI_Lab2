from datetime import datetime
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException

from gateway_service.clients.library_service_client import LibraryServiceClient
from gateway_service.clients.rating_service_client import RatingServiceClient
from gateway_service.clients.reservation_service_client import ReservationServiceClient
from gateway_service.models import (
    BookReservationResponse,
    ReturnBookRequest,
    TakeBookRequest,
    TakeBookResponse,
)
from gateway_service.settings import Settings
from reservation_service.models import (
    ReservationRequest,
    ReservationStatus,
)

router = APIRouter(prefix="/api/v1")


@lru_cache(maxsize=1)
def get_library_service():
    return LibraryServiceClient(Settings().library_service_url)  # type: ignore


@lru_cache(maxsize=1)
def get_reservation_service():
    return ReservationServiceClient(Settings().reservation_service_url)  # type: ignore


@lru_cache(maxsize=1)
def get_rating_service():
    return RatingServiceClient(Settings().rating_service_url)  # type: ignore


LibraryServiceDep = Annotated[LibraryServiceClient, Depends(get_library_service)]
ReservationServiceDep = Annotated[
    ReservationServiceClient, Depends(get_reservation_service)
]
RatingServiceDep = Annotated[RatingServiceClient, Depends(get_rating_service)]


# ---------------------------------------------------------
# 1) GET /api/v1/libraries -> прокси к Library Service
# ---------------------------------------------------------
@router.get("/libraries")
def gateway_libraries(
    library_client: LibraryServiceDep, city: str, page: int = 1, size: int = 10
):
    return library_client.get_libraries(city, page, size)


# ---------------------------------------------------------
# 2) GET /api/v1/libraries/{libraryUid}/books -> прокси к Library Service
# ---------------------------------------------------------
@router.get("/libraries/{libraryUid}/books")
def gateway_library_books(
    library_client: LibraryServiceDep,
    libraryUid: UUID,
    showAll: bool = False,
    page: int = 1,
    size: int = 10,
):
    return library_client.get_library_books(libraryUid, showAll, page, size)


# ---------------------------------------------------------
# 3) GET /api/v1/reservations -> прокси к Reservation Service
# ---------------------------------------------------------
@router.get("/reservations")
def gateway_reservations(
    reservation_client: ReservationServiceDep,
    library_client: LibraryServiceDep,
    x_user_name: str = Header(..., alias="X-User-Name"),
):
    data = reservation_client.get_reservations(x_user_name)
    return [
        BookReservationResponse(
            reservationUid=x.reservationUid,
            status=x.status,
            startDate=x.startDate,
            tillDate=x.tillDate,
            book=library_client.get_library_book(
                library_uid=x.libraryUid, book_uid=x.bookUid
            ),
            library=library_client.get_library_info(x.libraryUid),
        )
        for x in data
    ]


# ---------------------------------------------------------
# 4) POST /api/v1/reservations -> логика "взять книгу"
# ---------------------------------------------------------
@router.post("/reservations", response_model=TakeBookResponse)
def gateway_take_book(
    library_client: LibraryServiceDep,
    reservation_client: ReservationServiceDep,
    rating_client: RatingServiceDep,
    req: TakeBookRequest,
    x_user_name: str = Header(..., alias="X-User-Name"),
):
    # 4.1) Проверить, есть ли книга в library
    try:
        book_found = library_client.get_library_book(req.libraryUid, req.bookUid)
    except HTTPException:
        raise HTTPException(400, "Книга недоступна или не найдена в этой библиотеке")

    # 4.2) Проверить лимит книг у пользователя
    resv_resp = reservation_client.get_reservations(x_user_name)
    reservations = resv_resp
    rented_count = sum(1 for r in reservations if r.status == ReservationStatus.RENTED)

    # 4.3) Узнать рейтинг (stars) пользователя
    rating_resp = rating_client.get_rating(x_user_name)
    user_rating = rating_resp.stars

    max_books = max(1, min(user_rating, 100))

    if rented_count >= max_books:
        raise HTTPException(
            400,
            f"Вы уже взяли {rented_count} книг из {max_books} доступных по вашему рейтингу.",
        )

    # 4.4) Уменьшить available_count в library
    library_client.reduce_book_count(req.libraryUid, req.bookUid)

    # 4.5) Создать запись в Reservation Service (status=RENTED)
    now = datetime.now()

    reservation_body = ReservationRequest(
        reservationUid=None,
        username=x_user_name,
        bookUid=req.bookUid,
        libraryUid=req.libraryUid,
        status=ReservationStatus.RENTED,
        startDate=now,
        tillDate=req.tillDate,
    )
    try:
        created_res = reservation_client.create_reservation(
            x_user_name, reservation_body
        )
    except Exception as e:
        # Вернуть книгу в библиотеку, если не удалось создать запись
        library_client.increase_book_count(req.libraryUid, req.bookUid)
        raise e

    # 4.6) Сформировать ответ
    library_data = library_client.get_library_info(req.libraryUid)

    # 4.7) При успешном взятии книги ничего не делаем с рейтингом

    # 4.8) Получим актуальный рейтинг
    rating_after = rating_client.get_rating(x_user_name)

    return TakeBookResponse(
        reservationUid=created_res.reservationUid,
        status=created_res.status,
        startDate=created_res.startDate,
        tillDate=created_res.tillDate,
        book=TakeBookResponse.BookResponse(
            bookUid=book_found.bookUid,
            name=book_found.name,
            author=book_found.author,
            genre=book_found.genre,
        ),
        library=library_data,
        rating=rating_after,
    )


# ---------------------------------------------------------
# 5) POST /api/v1/reservations/{reservationUid}/return -> вернуть книгу
# ---------------------------------------------------------
@router.post("/reservations/{reservationUid}/return", status_code=204)
def gateway_return_book(
    library_client: LibraryServiceDep,
    reservation_client: ReservationServiceDep,
    rating_client: RatingServiceDep,
    reservationUid: UUID,
    req: ReturnBookRequest,
    x_user_name: str = Header(..., alias="X-User-Name"),
):
    compensate_steps = []
    try:
        # 5.1) Узнаём данные о бронировании (Reservation Service)
        rdata = reservation_client.get_reservation(reservationUid, x_user_name)

        # 5.2) Вызываем endpoint Reservation Service -> return_book
        return_resp = reservation_client.return_book(
            reservationUid, x_user_name, req.date
        )
        compensate_steps.append(
            lambda: reservation_client.undo_return_book(reservationUid, x_user_name)
        )
        new_status = return_resp.status

        book_info = library_client.get_library_book(rdata.libraryUid, rdata.bookUid)

        library_client.update_book_condition(
            rdata.libraryUid, rdata.bookUid, req.condition
        )
        compensate_steps.append(
            lambda: library_client.update_book_condition(
                rdata.libraryUid, rdata.bookUid, book_info.condition
            )
        )

        # 5.3) Увеличиваем available_count в Library Service
        library_client.increase_book_count(rdata.libraryUid, rdata.bookUid)
        compensate_steps.append(
            lambda: library_client.reduce_book_count(rdata.libraryUid, rdata.bookUid)
        )

        # 5.4) Корректируем рейтинг:
        penalty = 0
        if new_status == ReservationStatus.EXPIRED:
            penalty += 10
        if req.condition != "EXCELLENT":
            penalty += 10
        if penalty > 0:
            rating_client.decrease_rating(x_user_name, penalty)
            compensate_steps.append(
                lambda: rating_client.increase_rating(x_user_name, penalty)
            )
        else:
            rating_client.increase_rating(x_user_name, 1)
            compensate_steps.append(
                lambda: rating_client.decrease_rating(x_user_name, 1)
            )
    except Exception as e:
        # Восстановление состояния
        for step in reversed(compensate_steps):
            try:
                step()
            except Exception:
                pass
        raise e


# ---------------------------------------------------------
# 6) GET /api/v1/rating -> прокси к Rating Service
# ---------------------------------------------------------
@router.get("/rating")
def gateway_rating(
    rating_client: RatingServiceDep, x_user_name: str = Header(..., alias="X-User-Name")
):
    return rating_client.get_rating(x_user_name)

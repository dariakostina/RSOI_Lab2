from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlmodel import Session, SQLModel

from library_service.database import get_engine
from library_service.migrations import seed_data
from library_service.models import (
    BookCondition,
    BookResponse,
    ErrorResponse,
    LibrariesResponse,
    LibraryBook,
    LibraryBooksResponse,
    LibraryResponse,
    ReduceBookCountResponse,
)
from library_service.repositories import LibraryRepository


def get_repository():
    engine = get_engine()
    with Session(engine) as session:
        yield LibraryRepository(session)


RepoDep = Annotated[LibraryRepository, Depends(get_repository)]


def init_db():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    seed_data()


@asynccontextmanager
async def lifespan(_: APIRouter):
    init_db()
    yield


router = APIRouter(prefix="/api/v1", lifespan=lifespan)


@router.get("/libraries", response_model=LibrariesResponse)
def get_libraries(
    repo: RepoDep,
    city: str,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    total = repo.count_libraries_by_city(city)
    libs = repo.get_libraries_by_city(city, (page - 1) * size, size)

    items = [
        LibraryResponse(
            libraryUid=lib.library_uid,
            name=lib.name,
            address=lib.address,
            city=lib.city,
        )
        for lib in libs
    ]

    return LibrariesResponse(page=page, pageSize=size, totalElements=total, items=items)


@router.get(
    "/libraries/{library_uid}",
    response_model=LibraryResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_library(repo: RepoDep, library_uid: UUID):
    lib = repo.get_library_by_uid(library_uid)
    if not lib:
        return ErrorResponse(error="Library not found")
    return LibraryResponse(
        libraryUid=lib.library_uid,
        name=lib.name,
        address=lib.address,
        city=lib.city,
    )


@router.get("/libraries/{library_uid}/books", response_model=LibraryBooksResponse)
def get_library_books(
    repo: RepoDep,
    library_uid: UUID,
    showAll: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=10000),
):
    lib = repo.get_library_by_uid(library_uid)
    if not lib:
        return LibraryBooksResponse(page=page, pageSize=size, totalElements=0, items=[])

    total = repo.count_books_in_library(lib.id, showAll)
    results = repo.get_books_in_library(lib.id, showAll, (page - 1) * size, size)

    items = [
        BookResponse(
            bookUid=book.book_uid,
            name=book.name,
            author=book.author or "",
            genre=book.genre or "",
            condition=book.condition,
            availableCount=lb.available_count,
        )
        for lb, book in results
    ]

    return LibraryBooksResponse(
        page=page, pageSize=size, totalElements=total, items=items
    )


@router.get("/libraries/{library_uid}/books/{book_uid}", response_model=BookResponse)
def get_library_book(repo: RepoDep, library_uid: UUID, book_uid: UUID):
    lib = repo.get_library_by_uid(library_uid)
    if not lib:
        return ErrorResponse(error="Library not found")

    book = repo.get_book_by_uid(book_uid)
    if not book:
        return ErrorResponse(error="Book not found")

    lb = repo.get_library_book(lib.id, book.id)

    return BookResponse(
        bookUid=book.book_uid,
        name=book.name,
        author=book.author or "",
        genre=book.genre or "",
        condition=book.condition,
        availableCount=lb.available_count if lb else 0,
    )


@router.post(
    "/libraries/{library_uid}/books/{book_uid}/reduce_count",
    response_model=ReduceBookCountResponse,
    responses={404: {"model": ErrorResponse}},
)
def reduce_book_count(repo: RepoDep, library_uid: UUID, book_uid: UUID):
    """
    Уменьшает на 1 количество доступных книг в библиотеке (если > 0).
    """
    lib = repo.get_library_by_uid(library_uid)
    if not lib:
        return ErrorResponse(error="Library not found")

    book = repo.get_book_by_uid(book_uid)
    if not book:
        return ErrorResponse(error="Book not found")

    lb = repo.get_library_book(lib.id, book.id)
    if not lb:
        return ErrorResponse(error="LibraryBook not found")

    if lb.available_count <= 0:
        return ErrorResponse(error="No books available")

    lb.available_count -= 1
    repo.update_library_book(lb)
    return ReduceBookCountResponse(ok=True)


@router.post(
    "/libraries/{library_uid}/books/{book_uid}/increase_count",
    response_model=ReduceBookCountResponse,
    responses={404: {"model": ErrorResponse}},
)
def increase_book_count(repo: RepoDep, library_uid: UUID, book_uid: UUID):
    """
    Увеличивает на 1 количество доступных книг (возврат).
    """
    lib = repo.get_library_by_uid(library_uid)
    if not lib:
        return ErrorResponse(error="Library not found")

    book = repo.get_book_by_uid(book_uid)
    if not book:
        return ErrorResponse(error="Book not found")

    lb = repo.get_library_book(lib.id, book.id)
    if not lb:
        lb = LibraryBook(library_id=lib.id, book_id=book.id, available_count=1)
        repo.create_library_book(lb)
    else:
        lb.available_count += 1
        repo.update_library_book(lb)

    return ReduceBookCountResponse(ok=True)


@router.patch(
    "/libraries/{library_uid}/books/{book_uid}/update_condition",
    response_model=None,
    status_code=204,
    responses={404: {"model": ErrorResponse}},
)
def update_book_condition(
    repo: RepoDep, library_uid: UUID, book_uid: UUID, condition: BookCondition
):
    """
    Обновляет состояние книги в библиотеке.
    """
    lib = repo.get_library_by_uid(library_uid)
    if not lib:
        return ErrorResponse(error="Library not found")
    book = repo.get_book_by_uid(book_uid)
    if not book:
        return ErrorResponse(error="Book not found")
    book.condition = condition
    repo.update_book(book)
    return HTMLResponse(status_code=204)

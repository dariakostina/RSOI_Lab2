from uuid import UUID

import httpx
from fastapi import HTTPException
from httpx import HTTPStatusError, Response

from library_service.models import (
    BookCondition,
    BookResponse,
    LibrariesResponse,
    LibraryBooksResponse,
    LibraryResponse,
    ReduceBookCountResponse,
)


class LibraryServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def _handle_response(self, resp: Response):
        try:
            resp.raise_for_status()
        except HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=e.response.text
            )
        return resp

    def get_libraries(self, city: str, page: int, size: int):
        resp = httpx.get(
            f"{self.base_url}/api/v1/libraries",
            params={"city": city, "page": page, "size": size},
        )
        return LibrariesResponse(**self._handle_response(resp).json())

    def get_library_books(
        self, library_uid: UUID, show_all: bool, page: int, size: int
    ):
        resp = httpx.get(
            f"{self.base_url}/api/v1/libraries/{library_uid}/books",
            params={"showAll": show_all, "page": page, "size": size},
        )
        return LibraryBooksResponse(**self._handle_response(resp).json())

    def get_library_book(self, library_uid: UUID, book_uid: UUID):
        resp = httpx.get(
            f"{self.base_url}/api/v1/libraries/{library_uid}/books/{book_uid}",
        )
        return BookResponse(**self._handle_response(resp).json())

    def reduce_book_count(self, library_uid: UUID, book_uid: UUID):
        resp = httpx.post(
            f"{self.base_url}/api/v1/libraries/{library_uid}/books/{book_uid}/reduce_count",
        )
        return ReduceBookCountResponse(**self._handle_response(resp).json())

    def increase_book_count(self, library_uid: UUID, book_uid: UUID):
        resp = httpx.post(
            f"{self.base_url}/api/v1/libraries/{library_uid}/books/{book_uid}/increase_count",
        )
        return ReduceBookCountResponse(**self._handle_response(resp).json())

    def get_library_info(self, library_uid: UUID):
        resp = httpx.get(f"{self.base_url}/api/v1/libraries/{library_uid}")
        return LibraryResponse(**self._handle_response(resp).json())

    def update_book_condition(
        self, library_uid: UUID, book_uid: UUID, condition: BookCondition
    ):
        resp = httpx.patch(
            f"{self.base_url}/api/v1/libraries/{library_uid}/books/{book_uid}/update_condition",
            params={"condition": condition},
        )
        self._handle_response(resp)

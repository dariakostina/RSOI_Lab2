from datetime import datetime
from uuid import UUID

import httpx
from fastapi import HTTPException
from httpx import HTTPStatusError, Response

from reservation_service.models import (
    ReservationRequest,
    ReservationResponse,
    ReturnBookResponse,
)


class ReservationServiceClient:
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

    def get_reservations(self, x_user_name: str):
        resp = httpx.get(
            f"{self.base_url}/api/v1/reservations", headers={"X-User-Name": x_user_name}
        )
        return [
            ReservationResponse(**item) for item in self._handle_response(resp).json()
        ]

    def create_reservation(
        self, x_user_name: str, reservation_body: ReservationRequest
    ):
        resp = httpx.post(
            f"{self.base_url}/api/v1/reservations",
            headers={"X-User-Name": x_user_name},
            json=reservation_body.model_dump(mode="json"),
        )
        return ReservationResponse(**self._handle_response(resp).json())

    def get_reservation(self, reservation_uid: UUID, x_user_name: str):
        resp = httpx.get(
            f"{self.base_url}/api/v1/reservations/{reservation_uid}",
            headers={"X-User-Name": x_user_name},
        )
        return ReservationResponse(**self._handle_response(resp).json())

    def return_book(self, reservation_uid: UUID, x_user_name: str, date: datetime):
        resp = httpx.post(
            f"{self.base_url}/api/v1/reservations/{reservation_uid}/return",
            headers={"X-User-Name": x_user_name},
            params={"date": date.isoformat()},
        )
        return ReturnBookResponse(**self._handle_response(resp).json())

    def undo_return_book(self, reservation_uid: UUID, x_user_name: str):
        resp = httpx.post(
            f"{self.base_url}/api/v1/reservations/{reservation_uid}/return/undo",
            headers={"X-User-Name": x_user_name},
        )
        return ReturnBookResponse(**self._handle_response(resp).json())

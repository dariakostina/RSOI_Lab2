import httpx
from fastapi import HTTPException
from httpx import HTTPStatusError, Response

from rating_service.models import RatingResponse


class RatingServiceClient:
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

    def get_rating(self, username: str):
        resp = httpx.get(
            f"{self.base_url}/api/v1/rating", params={"username": username}
        )
        return RatingResponse(**self._handle_response(resp).json())

    def increase_rating(self, username: str, amount: int):
        resp = httpx.post(
            f"{self.base_url}/api/v1/rating/inc",
            params={"username": username, "amount": amount},
        )
        return RatingResponse(**self._handle_response(resp).json())

    def decrease_rating(self, username: str, amount: int):
        resp = httpx.post(
            f"{self.base_url}/api/v1/rating/dec",
            params={"username": username, "amount": amount},
        )
        return RatingResponse(**self._handle_response(resp).json())

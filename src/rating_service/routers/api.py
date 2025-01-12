from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session, SQLModel

from rating_service.database import get_engine
from rating_service.models import (
    ErrorResponse,
    Rating,
    RatingResponse,
)
from rating_service.repositories import RatingRepository


def get_repository():
    engine = get_engine()
    with Session(engine) as session:
        yield RatingRepository(session)


RepoDep = Annotated[RatingRepository, Depends(get_repository)]


def init_db():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(_: APIRouter):
    init_db()
    yield


router = APIRouter(prefix="/api/v1", lifespan=lifespan)


@router.get(
    "/rating",
    response_model=RatingResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_rating(repo: RepoDep, username: str):
    r = repo.get_rating_by_username(username)
    if not r:
        r = Rating(username=username, stars=50)
        repo.create_rating(r)
    return RatingResponse(stars=r.stars)


@router.post(
    "/rating/inc",
    response_model=RatingResponse,
    responses={404: {"model": ErrorResponse}},
)
def increase_rating(repo: RepoDep, username: str, amount: int = 1):
    """
    Увеличить рейтинг (но не более 100).
    """
    r = repo.get_rating_by_username(username)
    if not r:
        r = Rating(username=username, stars=50)
        repo.create_rating(r)

    r.stars = min(r.stars + amount, 100)
    repo.update_rating(r)
    return RatingResponse(stars=r.stars)


@router.post(
    "/rating/dec",
    response_model=RatingResponse,
    responses={404: {"model": ErrorResponse}},
)
def decrease_rating(repo: RepoDep, username: str, amount: int = 10):
    """
    Уменьшить рейтинг (но не менее 0).
    """
    r = repo.get_rating_by_username(username)
    if not r:
        r = Rating(username=username, stars=50)
        repo.create_rating(r)

    r.stars = max(r.stars - amount, 0)
    repo.update_rating(r)
    return RatingResponse(stars=r.stars)

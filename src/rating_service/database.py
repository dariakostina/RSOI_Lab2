from functools import lru_cache

from sqlmodel import create_engine

from rating_service.settings import Settings


@lru_cache(maxsize=1)
def get_engine():
    return create_engine(Settings().database_url, echo=False)

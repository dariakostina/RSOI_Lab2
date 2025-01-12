from sqlmodel import Session, select

from rating_service.models import Rating


class RatingRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_rating_by_username(self, username: str):
        return self.session.exec(
            select(Rating).where(Rating.username == username)
        ).first()

    def create_rating(self, rating: Rating):
        self.session.add(rating)
        self.session.commit()
        self.session.refresh(rating)

    def update_rating(self, rating: Rating):
        self.session.add(rating)
        self.session.commit()

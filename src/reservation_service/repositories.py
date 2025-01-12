from uuid import UUID

from sqlmodel import Session, select

from reservation_service.models import Reservation


class ReservationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_reservations_by_username(self, username: str):
        stmt = select(Reservation).where(Reservation.username == username)
        return self.session.exec(stmt).all()

    def get_reservation_by_uid(self, reservation_uid: UUID):
        return self.session.exec(
            select(Reservation).where(Reservation.reservation_uid == reservation_uid)
        ).first()

    def create_reservation(self, reservation: Reservation):
        self.session.add(reservation)
        self.session.commit()
        self.session.refresh(reservation)

    def update_reservation(self, reservation: Reservation):
        self.session.add(reservation)
        self.session.commit()

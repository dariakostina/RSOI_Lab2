from uuid import UUID

from sqlmodel import Session, col, func, select

from library_service.models import (
    Book,
    Library,
    LibraryBook,
)


class LibraryRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_library_by_uid(self, library_uid: UUID):
        return self.session.exec(
            select(Library).where(Library.library_uid == library_uid)
        ).first()

    def get_book_by_uid(self, book_uid: UUID):
        return self.session.exec(select(Book).where(Book.book_uid == book_uid)).first()

    def get_library_book(self, library_id: int, book_id: int):
        return self.session.exec(
            select(LibraryBook).where(
                (LibraryBook.library_id == library_id)
                & (LibraryBook.book_id == book_id)
            )
        ).first()

    def update_library_book(self, library_book: LibraryBook):
        self.session.add(library_book)
        self.session.commit()

    def create_library_book(self, library_book: LibraryBook):
        self.session.add(library_book)
        self.session.commit()

    def get_libraries_by_city(self, city: str, offset: int, limit: int):
        stmt = select(Library).where(Library.city == city).offset(offset).limit(limit)
        return self.session.exec(stmt).all()

    def count_libraries_by_city(self, city: str):
        stmt = select(func.count(col(Library.id))).where(Library.city == city)
        return self.session.exec(stmt).one()

    def get_books_in_library(
        self, library_id: int, show_all: bool, offset: int, limit: int
    ):
        stmt = (
            select(LibraryBook, Book)
            .join(Book, col(LibraryBook.book_id) == col(Book.id))
            .where(LibraryBook.library_id == library_id)
        )
        if not show_all:
            stmt = stmt.where(LibraryBook.available_count > 0)
        return self.session.exec(stmt.offset(offset).limit(limit)).all()

    def count_books_in_library(self, library_id: int, show_all: bool):
        stmt = select(func.count(col(LibraryBook.book_id))).where(
            LibraryBook.library_id == library_id
        )
        if not show_all:
            stmt = stmt.where(LibraryBook.available_count > 0)
        return self.session.exec(stmt).one()

    def update_book(self, book: Book):
        self.session.add(book)
        self.session.commit()

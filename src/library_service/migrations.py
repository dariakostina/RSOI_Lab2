from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from library_service.database import get_engine
from library_service.models import Book, BookCondition, Library, LibraryBook


def seed_data():
    with Session(get_engine()) as session:
        # Если библиотек нет, создадим тестовую
        count_libs = session.exec(select(func.count(Library.id))).one()
        if count_libs == 0:
            lib1 = Library(
                library_uid=UUID("83575e12-7ce0-48ee-9931-51919ff3c9ee"),
                name="Библиотека имени 7 Непьющих",
                city="Москва",
                address="2-я Бауманская ул., д.5, стр.1",
            )
            session.add(lib1)
            session.commit()

            book1 = Book(
                book_uid=UUID("f7cdc58f-2caf-4b15-9727-f89dcc629b27"),
                name="Краткий курс C++ в 7 томах",
                author="Бьерн Страуструп",
                genre="Научная фантастика",
                condition=BookCondition.EXCELLENT,
            )
            session.add(book1)
            session.commit()

            # Связка
            lb = LibraryBook(book_id=book1.id, library_id=lib1.id, available_count=1)
            session.add(lb)
            session.commit()

import uuid

from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from library_service.main import app
from library_service.models import Book, BookCondition, Library, LibraryBook
from library_service.routers.api import get_repository

client = TestClient(app)


def test_health_check():
    # act
    response = client.get("/manage/health")
    # assert
    assert response.status_code == 200


def test_get_libraries(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    mock_repo.count_libraries_by_city.return_value = 1
    mock_repo.get_libraries_by_city.return_value = [
        Library(
            library_uid=uuid.uuid4(),
            name="Test Library",
            address="Test Address",
            city="Test City",
        )
    ]
    # act
    response = client.get("/api/v1/libraries", params={"city": "TestCity"})
    # assert
    assert response.status_code == 200


def test_get_library(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    uid = uuid.uuid4()
    mock_repo.get_library_by_uid.return_value = Library(
        library_uid=uid,
        name="Single Library",
        address="Single Address",
        city="Single City",
    )
    # act
    response = client.get(f"/api/v1/libraries/{uid}")
    # assert
    assert response.status_code == 200


def test_get_library_books(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    mock_repo.get_library_by_uid.return_value = mocker.Mock(id=1)
    mock_repo.count_books_in_library.return_value = 1
    mock_repo.get_books_in_library.return_value = [
        (
            LibraryBook(available_count=1),
            Book(
                book_uid="f7cdc58f-2caf-4b15-9727-f89dcc629b27",
                name="Test Book",
                author="Test Author",
                genre="Test Genre",
                condition=BookCondition.EXCELLENT,
            ),
        )
    ]
    library_uuid = uuid.uuid4()
    # act
    response = client.get(f"/api/v1/libraries/{library_uuid}/books")
    # assert
    assert response.status_code == 200


def test_get_library_book(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    mock_repo.get_library_by_uid.return_value = mocker.Mock(id=1)
    book_uuid = uuid.uuid4()
    library_uuid = uuid.uuid4()
    mock_repo.get_book_by_uid.return_value = Book(
        id=2,
        book_uid=book_uuid,
        name="Test Book",
        author="Test Author",
        genre="Test Genre",
        condition=BookCondition.EXCELLENT,
    )
    mock_repo.get_library_book.return_value = mocker.Mock(available_count=1)

    # act
    response = client.get(f"/api/v1/libraries/{library_uuid}/books/{book_uuid}")
    # assert
    assert response.status_code == 200


def test_reduce_book_count(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    mock_repo.get_library_by_uid.return_value = mocker.Mock(id=1)
    mock_repo.get_book_by_uid.return_value = mocker.Mock(id=2)
    mock_repo.get_library_book.return_value = mocker.Mock(available_count=1)
    library_uuid = uuid.uuid4()
    book_uuid = uuid.uuid4()
    # act
    response = client.post(
        f"/api/v1/libraries/{library_uuid}/books/{book_uuid}/reduce_count"
    )
    # assert
    assert response.status_code == 200


def test_increase_book_count(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    mock_repo.get_library_by_uid.return_value = mocker.Mock(id=1)
    mock_repo.get_book_by_uid.return_value = mocker.Mock(id=2)
    mock_repo.get_library_book.return_value = None
    library_uuid = uuid.uuid4()
    book_uuid = uuid.uuid4()
    # act
    response = client.post(
        f"/api/v1/libraries/{library_uuid}/books/{book_uuid}/increase_count"
    )
    # assert
    assert response.status_code == 200


def test_update_book_condition(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    mock_repo.get_library_by_uid.return_value = mocker.Mock(id=1)
    mock_repo.get_book_by_uid.return_value = mocker.Mock(id=2)
    mock_repo.get_library_book.return_value = None
    library_uuid = uuid.uuid4()
    book_uuid = uuid.uuid4()
    # act
    response = client.patch(
        f"/api/v1/libraries/{library_uuid}/books/{book_uuid}/update_condition",
        params={"condition": BookCondition.GOOD},
    )
    # assert
    assert response.status_code == 204

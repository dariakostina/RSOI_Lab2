from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from gateway_service.main import app
from gateway_service.models import (
    RatingResponse,
    TakeBookRequest,
)
from gateway_service.routers.api import (
    get_library_service,
    get_rating_service,
    get_reservation_service,
)
from library_service.models import BookCondition, BookResponse, LibraryResponse
from reservation_service.models import ReservationResponse, ReservationStatus

client = TestClient(app)


def test_health_check():
    # act
    response = client.get("/manage/health")
    # assert
    assert response.status_code == 200


def test_get_libraries(mocker: MockerFixture):
    # arrange
    mock_library = mocker.Mock()
    app.dependency_overrides[get_library_service] = lambda: mock_library
    mock_library.get_libraries.return_value = {"content": [], "page": 1, "size": 10}
    # act
    response = client.get("/api/v1/libraries", params={"city": "TestCity"})
    # assert
    assert response.status_code == 200


def test_get_library_books(mocker: MockerFixture):
    # arrange
    mock_library = mocker.Mock()
    app.dependency_overrides[get_library_service] = lambda: mock_library
    mock_library.get_library_books.return_value = {"content": [], "page": 1, "size": 10}
    library_uuid = uuid4()
    # act
    response = client.get(f"/api/v1/libraries/{library_uuid}/books")
    # assert
    assert response.status_code == 200


def test_get_reservations(mocker: MockerFixture):
    # arrange
    mock_reservation = mocker.Mock()
    app.dependency_overrides[get_reservation_service] = lambda: mock_reservation
    mock_reservation.get_reservations.return_value = []
    # act
    response = client.get("/api/v1/reservations", headers={"X-User-Name": "testuser"})
    # assert
    assert response.status_code == 200


def test_take_book(mocker: MockerFixture):
    # arrange
    mock_library = mocker.Mock()
    mock_reservation = mocker.Mock()
    mock_rating = mocker.Mock()
    app.dependency_overrides[get_library_service] = lambda: mock_library
    app.dependency_overrides[get_reservation_service] = lambda: mock_reservation
    app.dependency_overrides[get_rating_service] = lambda: mock_rating
    mock_library.get_library_book.return_value = BookResponse(
        bookUid=uuid4(),
        name="testbook",
        author="testauthor",
        genre="testgenre",
        condition=BookCondition.GOOD,
        availableCount=1,
    )
    mock_reservation.get_reservations.return_value = []
    mock_rating.get_rating.return_value = RatingResponse(stars=5)
    mock_library.reduce_book_count.return_value = None
    mock_reservation.create_reservation.return_value = ReservationResponse(
        reservationUid=uuid4(),
        username="testuser",
        bookUid=uuid4(),
        libraryUid=uuid4(),
        status=ReservationStatus.RENTED,
        startDate=datetime.now(),
        tillDate=datetime.now(),
    )
    mock_library.get_library_info.return_value = LibraryResponse(
        libraryUid=uuid4(), name="testlibrary", address="testaddress", city="testcity"
    )

    payload = TakeBookRequest(
        bookUid=uuid4(),
        libraryUid=uuid4(),
        tillDate=datetime.now(),
    )
    # act
    response = client.post(
        "/api/v1/reservations",
        headers={"X-User-Name": "testuser"},
        json=payload.model_dump(mode="json"),
    )
    # assert
    assert response.status_code == 200


def test_return_book(mocker: MockerFixture):
    # arrange
    mock_library = mocker.Mock()
    mock_reservation = mocker.Mock()
    mock_rating = mocker.Mock()
    app.dependency_overrides[get_library_service] = lambda: mock_library
    app.dependency_overrides[get_reservation_service] = lambda: mock_reservation
    app.dependency_overrides[get_rating_service] = lambda: mock_rating
    mock_reservation.get_reservation.return_value = mocker.Mock(
        libraryUid=uuid4(), bookUid=uuid4()
    )
    mock_reservation.return_book.return_value = mocker.Mock(
        status=ReservationStatus.RETURNED
    )
    # act
    response = client.post(
        f"/api/v1/reservations/{uuid4()}/return",
        headers={"X-User-Name": "testuser"},
        json={"condition": str(BookCondition.GOOD), "date": datetime.now().isoformat()},
    )
    # assert
    assert response.status_code == 204


def test_get_rating(mocker: MockerFixture):
    # arrange
    mock_rating = mocker.Mock()
    app.dependency_overrides[get_rating_service] = lambda: mock_rating
    mock_rating.get_rating.return_value = RatingResponse(stars=5)
    # act
    response = client.get("/api/v1/rating", headers={"X-User-Name": "testuser"})
    # assert
    assert response.status_code == 200

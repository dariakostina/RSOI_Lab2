from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from reservation_service.main import app
from reservation_service.models import (
    Reservation,
    ReservationRequest,
    ReservationStatus,
)
from reservation_service.routers.api import get_repository

client = TestClient(app)


def test_health_check():
    # act
    response = client.get("/manage/health")
    # assert
    assert response.status_code == 200


def test_get_reservations(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    mock_repo.get_reservations_by_username.return_value = [
        Reservation(
            reservation_uid=uuid4(),
            username="testuser",
            book_uid=uuid4(),
            library_uid=uuid4(),
            status=ReservationStatus.RENTED,
            start_date=datetime.now(),
            till_date=datetime.now(),
        )
    ]
    # act
    response = client.get("/api/v1/reservations", headers={"X-User-Name": "testuser"})
    # assert
    assert response.status_code == 200


def test_get_reservation(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    res_uid = uuid4()
    mock_repo.get_reservation_by_uid.return_value = Reservation(
        reservation_uid=res_uid,
        username="testuser",
        book_uid=uuid4(),
        library_uid=uuid4(),
        status=ReservationStatus.RENTED,
        start_date=datetime.now(),
        till_date=datetime.now(),
    )
    # act
    response = client.get(
        f"/api/v1/reservations/{res_uid}", headers={"X-User-Name": "testuser"}
    )
    # assert
    assert response.status_code == 200


def test_create_reservation(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    # act
    response = client.post(
        "/api/v1/reservations",
        headers={"X-User-Name": "testuser"},
        json=ReservationRequest(
            reservationUid=uuid4(),
            username="testuser",
            bookUid=uuid4(),
            libraryUid=uuid4(),
            status=ReservationStatus.RENTED,
            startDate=datetime.now(),
            tillDate=datetime.now(),
        ).model_dump(mode="json"),
    )
    # assert
    assert response.status_code == 200


def test_return_book(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    res_uid = uuid4()
    mock_repo.get_reservation_by_uid.return_value = Reservation(
        reservation_uid=res_uid,
        username="testuser",
        book_uid=uuid4(),
        library_uid=uuid4(),
        status=ReservationStatus.RENTED,
        start_date=datetime.now(),
        till_date=datetime.now(),
    )
    # act
    response = client.post(
        f"/api/v1/reservations/{res_uid}/return",
        headers={"X-User-Name": "testuser"},
        params={"date": datetime.now().isoformat()},
    )
    # assert
    assert response.status_code == 200


def test_undo_return_book(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    res_uid = uuid4()
    mock_repo.get_reservation_by_uid.return_value = Reservation(
        reservation_uid=res_uid,
        username="testuser",
        book_uid=uuid4(),
        library_uid=uuid4(),
        status=ReservationStatus.RETURNED,
        start_date=datetime.now(),
        till_date=datetime.now(),
    )
    # act
    response = client.post(
        f"/api/v1/reservations/{res_uid}/return/undo",
        headers={"X-User-Name": "testuser"},
    )
    # assert
    assert response.status_code == 200

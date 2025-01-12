from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from rating_service.main import app
from rating_service.routers.api import get_repository

client = TestClient(app)


def test_health_check():
    # act
    response = client.get("/manage/health")
    # assert
    assert response.status_code == 200


def test_get_rating(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    mock_repo.get_rating_by_username.return_value = None
    # act
    response = client.get("/api/v1/rating", params={"username": "testuser"})
    # assert
    assert response.status_code == 200


def test_increase_rating(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    mock_repo.get_rating_by_username.return_value = mocker.Mock(stars=50)
    # act
    response = client.post(
        "/api/v1/rating/inc", params={"username": "testuser", "amount": 10}
    )
    # assert
    assert response.status_code == 200


def test_decrease_rating(mocker: MockerFixture):
    # arrange
    mock_repo = mocker.Mock()
    app.dependency_overrides[get_repository] = lambda: mock_repo
    mock_repo.get_rating_by_username.return_value = mocker.Mock(stars=100)
    # act
    response = client.post(
        "/api/v1/rating/dec", params={"username": "testuser", "amount": 10}
    )
    # assert
    assert response.status_code == 200

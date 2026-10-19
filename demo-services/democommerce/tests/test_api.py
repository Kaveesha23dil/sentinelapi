
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_user(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_list_orders(client):
    response = client.get("/api/v1/orders")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_existing_order(client):
    response = client.get("/api/v1/orders/1")

    assert response.status_code == 200
    assert response.json()["total_amount"] == "99.98"


def test_order_not_found(client):
    response = client.get("/api/v1/orders/999")

    assert response.status_code == 404


def test_create_order(client):
    response = client.post(
        "/api/v1/orders",
        json={
            "user_id": 1,
            "items": [
                {"product_id": 101, "quantity": 2}
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["total_amount"] == "99.98"


def test_invalid_quantity(client):
    response = client.post(
        "/api/v1/orders",
        json={
            "user_id": 1,
            "items": [
                {"product_id": 101, "quantity": -5}
            ],
        },
    )

    assert response.status_code == 422


def test_unknown_product(client):
    response = client.post(
        "/api/v1/orders",
        json={
            "user_id": 1,
            "items": [
                {"product_id": 999, "quantity": 1}
            ],
        },
    )

    assert response.status_code == 400


def test_payment_success(client):
    response = client.post(
        "/api/v1/payments/simulate",
        json={"order_id": 1},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    order = client.get("/api/v1/orders/1")
    assert order.json()["status"] == "completed"


def test_payment_failure(client):
    response = client.post(
        "/api/v1/payments/simulate",
        json={
            "order_id": 1,
            "simulate_failure": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"

    order = client.get("/api/v1/orders/1")
    assert order.json()["status"] == "pending"


def test_payment_order_not_found(client):
    response = client.post(
        "/api/v1/payments/simulate",
        json={"order_id": 999},
    )

    assert response.status_code == 404


def test_openapi_documentation(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/orders" in response.json()["paths"]

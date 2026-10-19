
from contextlib import asynccontextmanager
from decimal import Decimal
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status

from .data import PRODUCT_PRICES, USERS, initial_orders
from .models import (
    HealthResponse,
    Order,
    OrderCreate,
    OrderStatus,
    PaymentRequest,
    PaymentResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.orders = initial_orders()
    app.state.order_lock = Lock()
    yield


app = FastAPI(
    title="DemoCommerce API",
    description="Demo backend for SentinelAPI security monitoring",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
)
def health_check():
    return HealthResponse(
        status="healthy",
        service="democommerce-api",
        version="1.0.0",
    )


@app.get("/api/v1/users/me", tags=["Users"])
def get_current_user():
    # Fixed demo identity, not an authenticated user.
    # Real identity will be enforced in later milestones.
    return USERS[1]


@app.get(
    "/api/v1/orders",
    response_model=list[Order],
    tags=["Orders"],
)
def list_orders():
    with app.state.order_lock:
        return list(app.state.orders.values())


@app.get(
    "/api/v1/orders/{order_id}",
    response_model=Order,
    tags=["Orders"],
)
def get_order(order_id: int):
    with app.state.order_lock:
        order = app.state.orders.get(order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order


@app.post(
    "/api/v1/orders",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
    tags=["Orders"],
)
def create_order(payload: OrderCreate):
    if payload.user_id not in USERS:
        raise HTTPException(404, "User not found")

    total = Decimal("0.00")

    for item in payload.items:
        price = PRODUCT_PRICES.get(item.product_id)

        if price is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown product: {item.product_id}",
            )

        total += price * item.quantity

    with app.state.order_lock:
        next_id = max(
            app.state.orders.keys(),
            default=0,
        ) + 1

        order = Order(
            id=next_id,
            user_id=payload.user_id,
            items=payload.items,
            total_amount=total,
        )

        app.state.orders[next_id] = order

    return order


@app.post(
    "/api/v1/payments/simulate",
    response_model=PaymentResponse,
    tags=["Payments"],
)
def simulate_payment(payload: PaymentRequest):
    with app.state.order_lock:
        order = app.state.orders.get(payload.order_id)

        if order is None:
            raise HTTPException(404, "Order not found")

        if payload.simulate_failure:
            return PaymentResponse(
                transaction_id=str(uuid4()),
                order_id=payload.order_id,
                status="failed",
                message="Simulated payment failure",
            )

        order.status = OrderStatus.completed

    return PaymentResponse(
        transaction_id=str(uuid4()),
        order_id=payload.order_id,
        status="success",
        message="Simulated payment completed",
    )

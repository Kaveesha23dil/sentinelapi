
from decimal import Decimal

from .models import Order, OrderItem, OrderStatus, User


USERS = {
    1: User(
        id=1,
        name="John Doe",
        email="john@example.com"
    )
}

PRODUCT_PRICES = {
    101: Decimal("49.99"),
    102: Decimal("29.50"),
    103: Decimal("15.00"),
}


def initial_orders() -> dict[int, Order]:
    return {
        1: Order(
            id=1,
            user_id=1,
            items=[OrderItem(product_id=101, quantity=2)],
            total_amount=Decimal("99.98"),
            status=OrderStatus.pending,
        )
    }

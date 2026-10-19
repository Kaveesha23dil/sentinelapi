
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class OrderStatus(str, Enum):
    pending = "pending"
    completed = "completed"


class User(BaseModel):
    id: int
    name: str
    email: str


class OrderItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    user_id: int = Field(gt=0)
    items: list[OrderItem] = Field(min_length=1)


class Order(BaseModel):
    id: int
    user_id: int
    items: list[OrderItem]
    total_amount: Decimal
    status: OrderStatus = OrderStatus.pending


class PaymentRequest(BaseModel):
    order_id: int
    simulate_failure: bool = False


class PaymentResponse(BaseModel):
    transaction_id: str
    order_id: int
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

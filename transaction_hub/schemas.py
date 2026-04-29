"""
Transaction Hub - Pydantic Schemas
Defines request/response models for API validation and documentation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class CartItemRequest(BaseModel):
    """Schema for adding/updating item in cart."""
    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity to add")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 1,
                "quantity": 2
            }
        }


class CartItemResponse(BaseModel):
    """Schema for cart item response."""
    item_id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_id": 1,
                "product_id": 1,
                "quantity": 2,
                "unit_price": 79.99,
                "subtotal": 159.98
            }
        }


class CartResponse(BaseModel):
    """Schema for cart response."""
    cart_id: int
    user_id: int
    items: List[CartItemResponse] = Field(default_factory=list)
    total_price: float
    created_at: str
    updated_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "cart_id": 1,
                "user_id": 1,
                "items": [
                    {
                        "item_id": 1,
                        "product_id": 1,
                        "quantity": 2,
                        "unit_price": 79.99,
                        "subtotal": 159.98
                    }
                ],
                "total_price": 159.98,
                "created_at": "2026-04-30T12:00:00",
                "updated_at": "2026-04-30T12:00:00"
            }
        }


class CheckoutRequest(BaseModel):
    """Schema for checkout request."""
    user_id: int = Field(..., gt=0, description="User ID")
    cart_id: int = Field(..., gt=0, description="Cart ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "cart_id": 1
            }
        }


class OrderItemResponse(BaseModel):
    """Schema for order item response."""
    order_item_id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float


class OrderResponse(BaseModel):
    """Schema for order response."""
    order_id: int
    user_id: int
    cart_id: int
    items: List[OrderItemResponse] = Field(default_factory=list)
    total_price: float
    status: str
    created_at: str
    updated_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": 1,
                "user_id": 1,
                "cart_id": 1,
                "items": [
                    {
                        "order_item_id": 1,
                        "product_id": 1,
                        "quantity": 2,
                        "unit_price": 79.99,
                        "subtotal": 159.98
                    }
                ],
                "total_price": 159.98,
                "status": "confirmed",
                "created_at": "2026-04-30T12:00:00",
                "updated_at": "2026-04-30T12:00:00"
            }
        }


class CheckoutResponse(BaseModel):
    """Schema for checkout completion response."""
    order_id: int
    user_id: int
    status: str
    total_price: float
    timestamp: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": 1,
                "user_id": 1,
                "status": "confirmed",
                "total_price": 159.98,
                "timestamp": "2026-04-30T12:00:00Z",
                "message": "Order confirmed and stock reserved"
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Cart not found",
                "status_code": 404
            }
        }

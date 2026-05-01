"""
Product Hub - Pydantic Schemas
Defines request/response models for API validation and documentation.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ProductCreateRequest(BaseModel):
    """Schema for product creation request."""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: str = Field(default="", max_length=5000, description="Product description")
    price: float = Field(..., gt=0, description="Product price (must be > 0)")
    stock: int = Field(default=0, ge=0, description="Initial stock quantity")
    image_url: str = Field(default="", max_length=2000, description="Product image URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Wireless Headphones",
                "description": "High-quality Bluetooth headphones with noise cancellation",
                "price": 79.99,
                "stock": 50,
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400"
            }
        }


class ProductUpdateRequest(BaseModel):
    """Schema for product update request (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, max_length=5000, description="Product description")
    price: Optional[float] = Field(None, gt=0, description="Product price")
    stock: Optional[int] = Field(None, ge=0, description="Stock quantity")
    image_url: Optional[str] = Field(None, max_length=2000, description="Product image URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "price": 89.99,
                "stock": 45,
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400"
            }
        }


class ProductResponse(BaseModel):
    """Schema for product response."""
    product_id: int
    name: str
    description: str
    price: float
    stock: int
    image_url: str
    created_at: str
    updated_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 1,
                "name": "Wireless Headphones",
                "description": "High-quality Bluetooth headphones with noise cancellation",
                "price": 79.99,
                "stock": 50,
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400",
                "created_at": "2026-04-30T12:00:00",
                "updated_at": "2026-04-30T12:00:00"
            }
        }


class ProductStockResponse(BaseModel):
    """Schema for stock availability response."""
    product_id: int
    name: str
    stock: int
    in_stock: bool = Field(..., description="Whether product is in stock")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 1,
                "name": "Wireless Headphones",
                "stock": 50,
                "in_stock": True
            }
        }


class BulkStockCheckRequest(BaseModel):
    """Schema for bulk stock verification request."""
    items: list[dict] = Field(..., description="List of {product_id, quantity} items")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"product_id": 1, "quantity": 2},
                    {"product_id": 2, "quantity": 1}
                ]
            }
        }


class BulkStockCheckResponse(BaseModel):
    """Schema for bulk stock verification response."""
    available: bool = Field(..., description="Whether all items are in stock")
    items: list[dict] = Field(..., description="Stock status for each item")
    
    class Config:
        json_schema_extra = {
            "example": {
                "available": True,
                "items": [
                    {"product_id": 1, "requested": 2, "available_stock": 50, "sufficient": True},
                    {"product_id": 2, "requested": 1, "available_stock": 20, "sufficient": True}
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Product not found",
                "status_code": 404
            }
        }

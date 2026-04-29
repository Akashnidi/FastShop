"""
Product Hub - FastAPI Application
Entry point for the product catalog microservice.
Handles product CRUD operations, inventory management, and stock verification.
Port: 8002
"""

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from database import db
from schemas import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    ProductStockResponse,
    BulkStockCheckRequest,
    BulkStockCheckResponse,
    ErrorResponse,
)
from models import Product

# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title="FastShop - Product Hub",
    description="Product catalog management, inventory tracking, and stock verification",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Lifecycle Events
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    await db.connect()
    print("✓ Product Hub started on port 8002")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await db.disconnect()
    print("✓ Product Hub shutdown")


# ============================================================================
# Routes
# ============================================================================


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "service": "Product Hub",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "FastShop - Product Hub",
        "version": "1.0.0",
        "docs": "http://localhost:8002/docs",
        "endpoints": {
            "list_products": "GET /products",
            "create_product": "POST /products",
            "get_product": "GET /products/{product_id}",
            "update_product": "PUT /products/{product_id}",
            "delete_product": "DELETE /products/{product_id}",
            "check_stock": "GET /products/{product_id}/stock",
            "bulk_check_stock": "POST /products/stock/bulk-check",
            "health": "GET /health",
        },
    }


@app.get("/products", response_model=list[ProductResponse], tags=["Products"])
async def list_products(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of products to return"),
    offset: int = Query(0, ge=0, description="Number of products to skip"),
):
    """
    List all products with pagination.
    
    Args:
        limit: Maximum number of products (1-1000, default 100)
        offset: Number of products to skip (default 0)
    
    Returns:
        List of ProductResponse objects
    """
    products = await db.get_all_products(limit=limit, offset=offset)
    return [ProductResponse(**product.to_dict()) for product in products]


@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, tags=["Products"])
async def create_product(request: ProductCreateRequest):
    """
    Create a new product.
    
    Args:
        request: ProductCreateRequest with name, price, stock, description
    
    Returns:
        ProductResponse with assigned product_id
    """
    # Validate input
    if request.price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be greater than 0",
        )
    
    if request.stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock cannot be negative",
        )
    
    product = await db.create_product(
        name=request.name,
        description=request.description,
        price=request.price,
        stock=request.stock,
    )
    
    return ProductResponse(**product.to_dict())


@app.get("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
async def get_product(product_id: int):
    """
    Get a single product by ID.
    
    Args:
        product_id: Product ID
    
    Returns:
        ProductResponse
    
    Raises:
        HTTPException: If product not found
    """
    product = await db.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    
    return ProductResponse(**product.to_dict())


@app.put("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
async def update_product(product_id: int, request: ProductUpdateRequest):
    """
    Update a product by ID.
    
    Args:
        product_id: Product ID
        request: ProductUpdateRequest with fields to update
    
    Returns:
        Updated ProductResponse
    
    Raises:
        HTTPException: If product not found or validation fails
    """
    # Verify product exists
    existing = await db.get_product_by_id(product_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    
    # Build update dict with only provided fields
    update_data = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.description is not None:
        update_data["description"] = request.description
    if request.price is not None:
        if request.price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be greater than 0",
            )
        update_data["price"] = request.price
    if request.stock is not None:
        if request.stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock cannot be negative",
            )
        update_data["stock"] = request.stock
    
    product = await db.update_product(product_id, **update_data)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    
    return ProductResponse(**product.to_dict())


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Products"])
async def delete_product(product_id: int):
    """
    Delete a product by ID.
    
    Args:
        product_id: Product ID
    
    Raises:
        HTTPException: If product not found
    """
    # Verify product exists
    existing = await db.get_product_by_id(product_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    
    deleted = await db.delete_product(product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )


@app.get("/products/{product_id}/stock", response_model=ProductStockResponse, tags=["Stock"])
async def check_product_stock(
    product_id: int,
    quantity: int = Query(1, ge=1, description="Quantity to check availability for"),
):
    """
    Check product stock availability.
    
    Args:
        product_id: Product ID
        quantity: Quantity to verify (default 1)
    
    Returns:
        ProductStockResponse with stock info
    
    Raises:
        HTTPException: If product not found
    """
    product = await db.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    
    return ProductStockResponse(
        product_id=product.product_id,
        name=product.name,
        stock=product.stock,
        in_stock=product.stock >= quantity,
    )


@app.post("/products/stock/bulk-check", response_model=BulkStockCheckResponse, tags=["Stock"])
async def bulk_check_stock(request: BulkStockCheckRequest):
    """
    Check stock availability for multiple products.
    Used by Transaction Hub before confirming orders.
    
    Args:
        request: BulkStockCheckRequest with list of {product_id, quantity} items
    
    Returns:
        BulkStockCheckResponse with overall and per-item availability
    """
    if not request.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Items list cannot be empty",
        )
    
    # Validate items
    for item in request.items:
        if "product_id" not in item or "quantity" not in item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Each item must have product_id and quantity",
            )
        if item["quantity"] < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be at least 1",
            )
    
    result = await db.bulk_check_stock(request.items)
    
    return BulkStockCheckResponse(
        available=result["available"],
        items=result["items"],
    )


@app.post("/products/{product_id}/stock/update", response_model=ProductResponse, tags=["Stock"])
async def update_product_stock(product_id: int, delta: int = Query(..., description="Quantity delta (positive or negative)")):
    """
    Update product stock by delta.
    Used internally by Transaction Hub when orders are confirmed/cancelled.
    
    Args:
        product_id: Product ID
        delta: Amount to add/subtract from stock
    
    Returns:
        Updated ProductResponse
    
    Raises:
        HTTPException: If product not found or invalid delta
    """
    # Verify product exists
    existing = await db.get_product_by_id(product_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    
    # Check that resulting stock won't be negative
    if existing.stock + delta < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Current: {existing.stock}, requested delta: {delta}",
        )
    
    product = await db.update_stock(product_id, delta)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    
    return ProductResponse(**product.to_dict())


# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Handle generic exceptions."""
    return {
        "detail": "Internal server error",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        workers=1,
    )

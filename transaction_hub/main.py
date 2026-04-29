"""
Transaction Hub - FastAPI Application
Entry point for the transaction/order microservice.
Handles cart management, checkout, and order processing.
Synchronously verifies stock with Product Hub before confirming orders.
Port: 8003
"""

import os
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from database import db, product_hub_client
from schemas import (
    CartItemRequest,
    CartResponse,
    CartItemResponse,
    CheckoutRequest,
    CheckoutResponse,
    OrderResponse,
    OrderItemResponse,
)

# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title="FastShop - Transaction Hub",
    description="Cart management, checkout, and order processing with stock verification",
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
    print("✓ Transaction Hub started on port 8003")
    print(f"✓ Product Hub URL: {product_hub_client.base_url}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await db.disconnect()
    print("✓ Transaction Hub shutdown")


# ============================================================================
# Routes
# ============================================================================


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "service": "Transaction Hub",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "FastShop - Transaction Hub",
        "version": "1.0.0",
        "docs": "http://localhost:8003/docs",
        "endpoints": {
            "get_cart": "GET /cart/{user_id}",
            "add_to_cart": "POST /cart/{user_id}/items",
            "remove_from_cart": "DELETE /cart/{user_id}/items/{product_id}",
            "clear_cart": "DELETE /cart/{user_id}",
            "checkout": "POST /checkout",
            "get_order": "GET /orders/{order_id}",
            "list_user_orders": "GET /orders/user/{user_id}",
            "health": "GET /health",
        },
    }


# ============================================================================
# CART ENDPOINTS
# ============================================================================


@app.get("/cart/{user_id}", response_model=CartResponse, tags=["Cart"])
async def get_cart(user_id: int):
    """
    Get user's shopping cart.
    Creates a new cart if doesn't exist.
    
    Args:
        user_id: User ID
    
    Returns:
        CartResponse with items and total price
    """
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id",
        )
    
    cart = await db.get_or_create_cart(user_id)
    items = await db.get_cart_items(cart.cart_id)
    
    return CartResponse(
        cart_id=cart.cart_id,
        user_id=cart.user_id,
        items=[CartItemResponse(**item.to_dict()) for item in items],
        total_price=cart.total_price,
        created_at=cart.created_at.isoformat(),
        updated_at=cart.updated_at.isoformat(),
    )


@app.post("/cart/{user_id}/items", response_model=CartResponse, tags=["Cart"])
async def add_to_cart(user_id: int, request: CartItemRequest):
    """
    Add item to user's cart.
    Fetches current product price from Product Hub.
    
    Args:
        user_id: User ID
        request: CartItemRequest with product_id and quantity
    
    Returns:
        Updated CartResponse
    
    Raises:
        HTTPException: If product not found or validation fails
    """
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id",
        )
    
    if request.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than 0",
        )
    
    # Get or create cart
    cart = await db.get_or_create_cart(user_id)
    
    # Fetch product from Product Hub to get current price
    product = await product_hub_client.get_product(request.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {request.product_id} not found",
        )
    
    unit_price = product.get("price", 0.0)
    
    # Add to cart
    await db.add_to_cart(
        cart_id=cart.cart_id,
        product_id=request.product_id,
        quantity=request.quantity,
        unit_price=unit_price,
    )
    
    # Return updated cart
    updated_cart = await db.get_cart_by_id(cart.cart_id)
    items = await db.get_cart_items(cart.cart_id)
    
    return CartResponse(
        cart_id=updated_cart.cart_id,
        user_id=updated_cart.user_id,
        items=[CartItemResponse(**item.to_dict()) for item in items],
        total_price=updated_cart.total_price,
        created_at=updated_cart.created_at.isoformat(),
        updated_at=updated_cart.updated_at.isoformat(),
    )


@app.delete("/cart/{user_id}/items/{product_id}", response_model=CartResponse, tags=["Cart"])
async def remove_from_cart(user_id: int, product_id: int):
    """
    Remove item from user's cart.
    
    Args:
        user_id: User ID
        product_id: Product ID to remove
    
    Returns:
        Updated CartResponse
    
    Raises:
        HTTPException: If cart or item not found
    """
    if user_id <= 0 or product_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id or product_id",
        )
    
    # Get cart
    cart = await db.get_or_create_cart(user_id)
    
    # Remove item
    removed = await db.remove_from_cart(cart.cart_id, product_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {product_id} not in cart",
        )
    
    # Return updated cart
    updated_cart = await db.get_cart_by_id(cart.cart_id)
    items = await db.get_cart_items(cart.cart_id)
    
    return CartResponse(
        cart_id=updated_cart.cart_id,
        user_id=updated_cart.user_id,
        items=[CartItemResponse(**item.to_dict()) for item in items],
        total_price=updated_cart.total_price,
        created_at=updated_cart.created_at.isoformat(),
        updated_at=updated_cart.updated_at.isoformat(),
    )


@app.delete("/cart/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Cart"])
async def clear_cart(user_id: int):
    """
    Clear all items from user's cart.
    
    Args:
        user_id: User ID
    """
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id",
        )
    
    cart = await db.get_or_create_cart(user_id)
    await db.clear_cart(cart.cart_id)


# ============================================================================
# CHECKOUT & ORDER ENDPOINTS
# ============================================================================


@app.post("/checkout", response_model=CheckoutResponse, tags=["Checkout"])
async def checkout(request: CheckoutRequest):
    """
    Process checkout.
    CRITICAL: Synchronously verifies stock with Product Hub before confirming order.
    
    Workflow:
    1. Verify cart exists and has items
    2. Fetch all cart items
    3. Call Product Hub to verify stock availability (SYNCHRONOUS)
    4. If stock available: create order, clear cart, return success
    5. If stock unavailable: return error without modifying cart
    
    Args:
        request: CheckoutRequest with user_id and cart_id
    
    Returns:
        CheckoutResponse with order details
    
    Raises:
        HTTPException: If cart not found, empty, out of stock, or verification fails
    """
    if request.user_id <= 0 or request.cart_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id or cart_id",
        )
    
    # Verify cart exists
    cart = await db.get_cart_by_id(request.cart_id)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart {request.cart_id} not found",
        )
    
    if cart.user_id != request.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized cart access",
        )
    
    # Get cart items
    items = await db.get_cart_items(request.cart_id)
    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )
    
    # ========================================================================
    # STOCK VERIFICATION - SYNCHRONOUS CALL TO PRODUCT HUB
    # ========================================================================
    # Build list of items for bulk stock check
    stock_check_items = [
        {"product_id": item.product_id, "quantity": item.quantity}
        for item in items
    ]
    
    # Call Product Hub to verify stock (BLOCKING/SYNCHRONOUS)
    available, stock_response = await product_hub_client.verify_stock(stock_check_items)
    
    if not available:
        # Extract detailed error info
        failing_items = [
            item for item in stock_response.get("items", [])
            if not item.get("sufficient", False)
        ]
        
        detail = "Insufficient stock: "
        for item in failing_items:
            detail += f"Product {item['product_id']} (need {item['requested']}, have {item['available_stock']}); "
        
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )
    
    # ========================================================================
    # STOCK VERIFIED - PROCEED WITH ORDER CREATION
    # ========================================================================
    
    # Create order (snapshot of cart)
    order = await db.create_order(
        user_id=request.user_id,
        cart_id=request.cart_id,
        total_price=cart.total_price,
    )
    
    # Clear the cart for future shopping
    await db.clear_cart(request.cart_id)
    
    return CheckoutResponse(
        order_id=order.order_id,
        user_id=order.user_id,
        status=order.status,
        total_price=order.total_price,
        timestamp=datetime.now(timezone.utc).isoformat(),
        message="Order confirmed and stock reserved",
    )


@app.get("/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
async def get_order(order_id: int):
    """
    Get order details.
    
    Args:
        order_id: Order ID
    
    Returns:
        OrderResponse with items and status
    
    Raises:
        HTTPException: If order not found
    """
    if order_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order_id",
        )
    
    order = await db.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    
    order_items = await db.get_order_items(order_id)
    
    return OrderResponse(
        order_id=order.order_id,
        user_id=order.user_id,
        cart_id=order.cart_id,
        items=[OrderItemResponse(**item.to_dict()) for item in order_items],
        total_price=order.total_price,
        status=order.status,
        created_at=order.created_at.isoformat(),
        updated_at=order.updated_at.isoformat(),
    )


@app.get("/orders/user/{user_id}", response_model=list[OrderResponse], tags=["Orders"])
async def get_user_orders(user_id: int, limit: int = 50, offset: int = 0):
    """
    Get user's orders.
    
    Args:
        user_id: User ID
        limit: Maximum orders to return
        offset: Number of orders to skip
    
    Returns:
        List of OrderResponse objects
    """
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id",
        )
    
    orders = await db.get_user_orders(user_id, limit=limit, offset=offset)
    
    result = []
    for order in orders:
        order_items = await db.get_order_items(order.order_id)
        result.append(
            OrderResponse(
                order_id=order.order_id,
                user_id=order.user_id,
                cart_id=order.cart_id,
                items=[OrderItemResponse(**item.to_dict()) for item in order_items],
                total_price=order.total_price,
                status=order.status,
                created_at=order.created_at.isoformat(),
                updated_at=order.updated_at.isoformat(),
            )
        )
    
    return result


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
        port=8003,
        workers=1,
    )

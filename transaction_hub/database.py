"""
Transaction Hub - Database Module
Manages SQLite database connections and migrations using aiosqlite.
Handles cart, cart items, and order operations.
"""

import aiosqlite
import os
from typing import Optional, List, Tuple
import httpx
from models import Cart, CartItem, Order, OrderItem


class Database:
    """
    Async SQLite database manager for Transaction Hub.
    Handles cart, cart items, and order operations.
    """
    
    def __init__(self, db_path: str = "transaction.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file (default: transaction.db)
        """
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> None:
        """
        Establish async connection to SQLite database.
        Creates database file if it doesn't exist.
        Runs migrations automatically.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else ".", exist_ok=True)
        
        # Connect to database
        self.conn = await aiosqlite.connect(self.db_path)
        
        # Enable foreign keys for data integrity
        await self.conn.execute("PRAGMA foreign_keys = ON;")
        
        # Run migrations
        await self._migrate()
        
        print(f"✓ Connected to database: {self.db_path}")
    
    async def disconnect(self) -> None:
        """Close database connection gracefully."""
        if self.conn:
            await self.conn.close()
            print(f"✓ Disconnected from database: {self.db_path}")
    
    async def _migrate(self) -> None:
        """
        Run database migrations (create tables, indexes).
        Idempotent - safe to run multiple times.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        # Create tables
        await self.conn.execute(Cart.CREATE_TABLE_SQL)
        await self.conn.execute(CartItem.CREATE_TABLE_SQL)
        await self.conn.execute(Order.CREATE_TABLE_SQL)
        await self.conn.execute(OrderItem.CREATE_TABLE_SQL)
        
        # Create indexes
        for index_sql in Cart.CREATE_INDEXES_SQL + CartItem.CREATE_INDEXES_SQL + Order.CREATE_INDEXES_SQL + OrderItem.CREATE_INDEXES_SQL:
            await self.conn.execute(index_sql)
        
        await self.conn.commit()
        print("✓ Database migrations completed")
    
    # ========================================================================
    # CART OPERATIONS
    # ========================================================================
    
    async def get_or_create_cart(self, user_id: int) -> Cart:
        """
        Get user's cart or create one if doesn't exist.
        
        Args:
            user_id: User ID
        
        Returns:
            Cart object
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        # Try to get existing cart
        sql = f"SELECT * FROM {Cart.TABLE_NAME} WHERE user_id = ? LIMIT 1"
        cursor = await self.conn.execute(sql, (user_id,))
        row = await cursor.fetchone()
        
        if row:
            return Cart.from_row(row)
        
        # Create new cart
        sql = f"INSERT INTO {Cart.TABLE_NAME} (user_id) VALUES (?)"
        cursor = await self.conn.execute(sql, (user_id,))
        await self.conn.commit()
        
        cart_id = cursor.lastrowid
        return Cart(cart_id=cart_id, user_id=user_id, total_price=0.0)
    
    async def get_cart_by_id(self, cart_id: int) -> Optional[Cart]:
        """Get cart by ID."""
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"SELECT * FROM {Cart.TABLE_NAME} WHERE cart_id = ? LIMIT 1"
        cursor = await self.conn.execute(sql, (cart_id,))
        row = await cursor.fetchone()
        
        return Cart.from_row(row) if row else None
    
    async def add_to_cart(self, cart_id: int, product_id: int, quantity: int, unit_price: float) -> CartItem:
        """
        Add or update item in cart.
        
        Args:
            cart_id: Cart ID
            product_id: Product ID
            quantity: Quantity to add
            unit_price: Price per unit
        
        Returns:
            CartItem object
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        # Calculate subtotal
        subtotal = quantity * unit_price
        
        # Check if item already in cart
        sql = f"SELECT item_id, quantity FROM {CartItem.TABLE_NAME} WHERE cart_id = ? AND product_id = ?"
        cursor = await self.conn.execute(sql, (cart_id, product_id))
        existing = await cursor.fetchone()
        
        if existing:
            # Update quantity
            new_quantity = existing[1] + quantity
            new_subtotal = new_quantity * unit_price
            sql = f"""
            UPDATE {CartItem.TABLE_NAME}
            SET quantity = ?, subtotal = ?
            WHERE item_id = ?
            """
            await self.conn.execute(sql, (new_quantity, new_subtotal, existing[0]))
        else:
            # Insert new item
            sql = f"""
            INSERT INTO {CartItem.TABLE_NAME} (cart_id, product_id, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?)
            """
            cursor = await self.conn.execute(sql, (cart_id, product_id, quantity, unit_price, subtotal))
        
        await self.conn.commit()
        
        # Recalculate cart total
        await self._recalculate_cart_total(cart_id)
        
        # Return the cart item
        sql = f"SELECT * FROM {CartItem.TABLE_NAME} WHERE cart_id = ? AND product_id = ?"
        cursor = await self.conn.execute(sql, (cart_id, product_id))
        row = await cursor.fetchone()
        return CartItem.from_row(row)
    
    async def remove_from_cart(self, cart_id: int, product_id: int) -> bool:
        """
        Remove item from cart.
        
        Args:
            cart_id: Cart ID
            product_id: Product ID
        
        Returns:
            True if removed, False if not found
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"DELETE FROM {CartItem.TABLE_NAME} WHERE cart_id = ? AND product_id = ?"
        cursor = await self.conn.execute(sql, (cart_id, product_id))
        await self.conn.commit()
        
        # Recalculate cart total
        await self._recalculate_cart_total(cart_id)
        
        return cursor.rowcount > 0
    
    async def get_cart_items(self, cart_id: int) -> List[CartItem]:
        """Get all items in cart."""
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"SELECT * FROM {CartItem.TABLE_NAME} WHERE cart_id = ? ORDER BY item_id"
        cursor = await self.conn.execute(sql, (cart_id,))
        rows = await cursor.fetchall()
        
        return [CartItem.from_row(row) for row in rows]
    
    async def clear_cart(self, cart_id: int) -> bool:
        """Clear all items from cart."""
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"DELETE FROM {CartItem.TABLE_NAME} WHERE cart_id = ?"
        cursor = await self.conn.execute(sql, (cart_id,))
        await self.conn.commit()
        
        # Reset cart total
        sql = f"UPDATE {Cart.TABLE_NAME} SET total_price = 0 WHERE cart_id = ?"
        await self.conn.execute(sql, (cart_id,))
        await self.conn.commit()
        
        return cursor.rowcount > 0
    
    async def _recalculate_cart_total(self, cart_id: int) -> float:
        """Recalculate and update cart total price."""
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"SELECT COALESCE(SUM(subtotal), 0) FROM {CartItem.TABLE_NAME} WHERE cart_id = ?"
        cursor = await self.conn.execute(sql, (cart_id,))
        row = await cursor.fetchone()
        total = float(row[0]) if row else 0.0
        
        sql = f"UPDATE {Cart.TABLE_NAME} SET total_price = ? WHERE cart_id = ?"
        await self.conn.execute(sql, (total, cart_id))
        await self.conn.commit()
        
        return total
    
    # ========================================================================
    # ORDER OPERATIONS
    # ========================================================================
    
    async def create_order(self, user_id: int, cart_id: int, total_price: float) -> Order:
        """
        Create a new order from a cart.
        
        Args:
            user_id: User ID
            cart_id: Cart ID to convert to order
            total_price: Order total
        
        Returns:
            Order object
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        # Create order
        sql = f"""
        INSERT INTO {Order.TABLE_NAME} (user_id, cart_id, total_price, status)
        VALUES (?, ?, ?, 'confirmed')
        """
        cursor = await self.conn.execute(sql, (user_id, cart_id, total_price))
        await self.conn.commit()
        
        order_id = cursor.lastrowid
        
        # Copy cart items to order items
        cart_items = await self.get_cart_items(cart_id)
        for item in cart_items:
            sql = f"""
            INSERT INTO {OrderItem.TABLE_NAME} (order_id, product_id, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?)
            """
            await self.conn.execute(sql, (order_id, item.product_id, item.quantity, item.unit_price, item.subtotal))
        
        await self.conn.commit()
        
        return Order(order_id=order_id, user_id=user_id, cart_id=cart_id, total_price=total_price, status="confirmed")
    
    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID."""
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"SELECT * FROM {Order.TABLE_NAME} WHERE order_id = ? LIMIT 1"
        cursor = await self.conn.execute(sql, (order_id,))
        row = await cursor.fetchone()
        
        return Order.from_row(row) if row else None
    
    async def get_order_items(self, order_id: int) -> List[OrderItem]:
        """Get all items in an order."""
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"SELECT * FROM {OrderItem.TABLE_NAME} WHERE order_id = ? ORDER BY order_item_id"
        cursor = await self.conn.execute(sql, (order_id,))
        rows = await cursor.fetchall()
        
        return [OrderItem.from_row(row) for row in rows]
    
    async def get_user_orders(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Order]:
        """Get user's orders with pagination."""
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"""
        SELECT * FROM {Order.TABLE_NAME}
        WHERE user_id = ?
        ORDER BY order_id DESC
        LIMIT ? OFFSET ?
        """
        cursor = await self.conn.execute(sql, (user_id, limit, offset))
        rows = await cursor.fetchall()
        
        return [Order.from_row(row) for row in rows]


# Global database instance
db = Database(os.getenv("DATABASE_PATH", "transaction.db"))


# ============================================================================
# PRODUCT HUB INTEGRATION
# ============================================================================

class ProductHubClient:
    """Client for communicating with Product Hub via httpx."""
    
    def __init__(self, base_url: str):
        """
        Initialize Product Hub client.
        
        Args:
            base_url: Product Hub service URL (e.g., http://product_hub:8002)
        """
        self.base_url = base_url.rstrip("/")
    
    async def get_product(self, product_id: int) -> Optional[dict]:
        """
        Fetch product details from Product Hub.
        
        Args:
            product_id: Product ID
        
        Returns:
            Product dict with name, price, stock, or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/products/{product_id}")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Error fetching product {product_id}: {e}")
        return None
    
    async def verify_stock(self, items: List[dict]) -> Tuple[bool, dict]:
        """
        Verify stock availability for cart items via Product Hub.
        SYNCHRONOUS call to ensure stock is checked before checkout.
        
        Args:
            items: List of {product_id, quantity} dicts
        
        Returns:
            Tuple of (available: bool, response_data: dict)
        """
        try:
            payload = {"items": items}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/products/stock/bulk-check",
                    json=payload
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("available", False), data
        except Exception as e:
            print(f"Error verifying stock: {e}")
        
        return False, {"available": False, "error": "Stock verification failed"}


# Global Product Hub client
product_hub_url = os.getenv("PRODUCT_HUB_URL", "http://localhost:8002")
product_hub_client = ProductHubClient(product_hub_url)

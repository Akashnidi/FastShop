"""
Product Hub - Database Module
Manages SQLite database connections and migrations using aiosqlite.
Ensures thread-safe async operations for concurrent requests.
"""

import aiosqlite
import os
from typing import Optional, List
from models import Product


class Database:
    """
    Async SQLite database manager for Product Hub.
    Handles connection pooling, migrations, and query execution.
    """
    
    def __init__(self, db_path: str = "product.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file (default: product.db)
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
        
        # Create products table
        await self.conn.execute(Product.CREATE_TABLE_SQL)
        
        # Create indexes
        for index_sql in Product.CREATE_INDEXES_SQL:
            await self.conn.execute(index_sql)
        
        await self.conn.commit()
        print("✓ Database migrations completed")
    
    async def create_product(
        self, name: str, price: float, stock: int = 0, description: str = ""
    ) -> Product:
        """
        Create a new product in the database.
        
        Args:
            name: Product name
            price: Product price
            stock: Initial stock quantity
            description: Product description
        
        Returns:
            Product object with assigned product_id
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"""
        INSERT INTO {Product.TABLE_NAME} (name, description, price, stock)
        VALUES (?, ?, ?, ?)
        """
        
        cursor = await self.conn.execute(sql, (name, description, price, stock))
        await self.conn.commit()
        
        product_id = cursor.lastrowid
        product = Product(
            product_id=product_id,
            name=name,
            description=description,
            price=price,
            stock=stock,
        )
        return product
    
    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Retrieve product by product ID.
        
        Args:
            product_id: Product ID to search for
        
        Returns:
            Product object if found, None otherwise
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"SELECT * FROM {Product.TABLE_NAME} WHERE product_id = ? LIMIT 1"
        cursor = await self.conn.execute(sql, (product_id,))
        row = await cursor.fetchone()
        
        if row:
            return Product.from_row(row)
        return None
    
    async def get_all_products(self, limit: int = 100, offset: int = 0) -> List[Product]:
        """
        Retrieve all products with pagination.
        
        Args:
            limit: Maximum number of products to return
            offset: Number of products to skip
        
        Returns:
            List of Product objects
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"SELECT * FROM {Product.TABLE_NAME} ORDER BY product_id DESC LIMIT ? OFFSET ?"
        cursor = await self.conn.execute(sql, (limit, offset))
        rows = await cursor.fetchall()
        
        return [Product.from_row(row) for row in rows]
    
    async def update_product(self, product_id: int, **kwargs) -> Optional[Product]:
        """
        Update product fields.
        
        Args:
            product_id: Product ID to update
            **kwargs: Fields to update (name, description, price, stock)
        
        Returns:
            Updated Product object if found, None otherwise
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        if not kwargs:
            return await self.get_product_by_id(product_id)
        
        # Only allow updating specific fields
        allowed_fields = {"name", "description", "price", "stock"}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_fields:
            return await self.get_product_by_id(product_id)
        
        # Build dynamic SQL
        set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
        values = list(update_fields.values()) + [product_id]
        
        sql = f"""
        UPDATE {Product.TABLE_NAME}
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE product_id = ?
        """
        
        await self.conn.execute(sql, values)
        await self.conn.commit()
        
        return await self.get_product_by_id(product_id)
    
    async def delete_product(self, product_id: int) -> bool:
        """
        Delete a product by ID.
        
        Args:
            product_id: Product ID to delete
        
        Returns:
            True if product was deleted, False if not found
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"DELETE FROM {Product.TABLE_NAME} WHERE product_id = ?"
        cursor = await self.conn.execute(sql, (product_id,))
        await self.conn.commit()
        
        return cursor.rowcount > 0
    
    async def update_stock(self, product_id: int, quantity_delta: int) -> Optional[Product]:
        """
        Update product stock by delta (increase or decrease).
        
        Args:
            product_id: Product ID to update
            quantity_delta: Amount to add/subtract from stock
        
        Returns:
            Updated Product object if found, None otherwise
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"""
        UPDATE {Product.TABLE_NAME}
        SET stock = MAX(0, stock + ?), updated_at = CURRENT_TIMESTAMP
        WHERE product_id = ?
        """
        
        await self.conn.execute(sql, (quantity_delta, product_id))
        await self.conn.commit()
        
        return await self.get_product_by_id(product_id)
    
    async def check_stock(self, product_id: int, quantity: int = 1) -> dict:
        """
        Check if product has sufficient stock.
        
        Args:
            product_id: Product ID to check
            quantity: Quantity required
        
        Returns:
            Dict with availability info: {available: bool, stock: int, sufficient: bool}
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        product = await self.get_product_by_id(product_id)
        if not product:
            return {"available": False, "stock": 0, "sufficient": False}
        
        return {
            "available": True,
            "stock": product.stock,
            "sufficient": product.stock >= quantity,
        }
    
    async def bulk_check_stock(self, items: List[dict]) -> dict:
        """
        Check stock for multiple products.
        
        Args:
            items: List of {product_id, quantity} dicts
        
        Returns:
            Dict with overall availability and per-item status
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        results = []
        all_available = True
        
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 1)
            
            product = await self.get_product_by_id(product_id)
            
            if not product:
                results.append({
                    "product_id": product_id,
                    "requested": quantity,
                    "available_stock": 0,
                    "sufficient": False,
                })
                all_available = False
            else:
                sufficient = product.stock >= quantity
                results.append({
                    "product_id": product_id,
                    "requested": quantity,
                    "available_stock": product.stock,
                    "sufficient": sufficient,
                })
                if not sufficient:
                    all_available = False
        
        return {
            "available": all_available,
            "items": results,
        }
    
    async def get_product_count(self) -> int:
        """Get total number of products in database."""
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"SELECT COUNT(*) FROM {Product.TABLE_NAME}"
        cursor = await self.conn.execute(sql)
        row = await cursor.fetchone()
        
        return row[0] if row else 0


# Global database instance
db = Database(os.getenv("DATABASE_PATH", "product.db"))

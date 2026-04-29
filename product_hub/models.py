"""
Product Hub - Database Models
Defines the Product table schema for SQLite.
Uses raw SQL queries (no ORM) for lightweight, direct database access.
"""

from datetime import datetime


class Product:
    """
    Product model representing a product in the product.db database.
    
    Attributes:
        product_id (int): Primary key, auto-incremented
        name (str): Product name (max 255 chars)
        description (str): Long product description
        price (float): Product price in USD
        stock (int): Current stock quantity
        created_at (datetime): Product creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
    TABLE_NAME = "products"
    
    # SQL schema for the products table
    CREATE_TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        price DECIMAL(10, 2) NOT NULL CHECK(price >= 0),
        stock INTEGER NOT NULL CHECK(stock >= 0) DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Indexes for performance
    CREATE_INDEXES_SQL = [
        f"CREATE INDEX IF NOT EXISTS idx_name ON {TABLE_NAME}(name);",
        f"CREATE INDEX IF NOT EXISTS idx_stock ON {TABLE_NAME}(stock);",
    ]
    
    def __init__(
        self,
        product_id: int = None,
        name: str = None,
        description: str = "",
        price: float = None,
        stock: int = 0,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        """Initialize a Product instance."""
        self.product_id = product_id
        self.name = name
        self.description = description
        self.price = price
        self.stock = stock
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert product to dictionary (for responses)."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price) if self.price else 0.0,
            "stock": self.stock,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "Product":
        """
        Create a Product instance from a database row.
        
        Row tuple structure: (product_id, name, description, price, stock, created_at, updated_at)
        """
        return cls(
            product_id=row[0],
            name=row[1],
            description=row[2],
            price=float(row[3]),
            stock=row[4],
            created_at=datetime.fromisoformat(row[5]) if isinstance(row[5], str) else row[5],
            updated_at=datetime.fromisoformat(row[6]) if isinstance(row[6], str) else row[6],
        )

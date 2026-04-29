"""
Transaction Hub - Database Models
Defines the Cart, CartItem, and Order table schemas for SQLite.
Uses raw SQL queries (no ORM) for lightweight, direct database access.
"""

from datetime import datetime


class Cart:
    """
    Cart model representing a shopping cart in the transaction.db database.
    
    Attributes:
        cart_id (int): Primary key, auto-incremented
        user_id (int): User who owns this cart
        total_price (float): Current total price of all items
        created_at (datetime): Cart creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
    TABLE_NAME = "carts"
    
    CREATE_TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_price DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK(total_price >= 0),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id)
    );
    """
    
    CREATE_INDEXES_SQL = [
        f"CREATE INDEX IF NOT EXISTS idx_user_id ON {TABLE_NAME}(user_id);",
    ]
    
    def __init__(
        self,
        cart_id: int = None,
        user_id: int = None,
        total_price: float = 0.0,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.cart_id = cart_id
        self.user_id = user_id
        self.total_price = total_price
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "cart_id": self.cart_id,
            "user_id": self.user_id,
            "total_price": float(self.total_price) if self.total_price else 0.0,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "Cart":
        return cls(
            cart_id=row[0],
            user_id=row[1],
            total_price=float(row[2]),
            created_at=datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3],
            updated_at=datetime.fromisoformat(row[4]) if isinstance(row[4], str) else row[4],
        )


class CartItem:
    """
    CartItem model representing an item in a shopping cart.
    
    Attributes:
        item_id (int): Primary key, auto-incremented
        cart_id (int): Foreign key to Cart
        product_id (int): Product being ordered
        quantity (int): Quantity of this product
        unit_price (float): Price per unit at time of add
        subtotal (float): quantity * unit_price
        created_at (datetime): Item added timestamp
    """
    
    TABLE_NAME = "cart_items"
    
    CREATE_TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cart_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        unit_price DECIMAL(10, 2) NOT NULL CHECK(unit_price > 0),
        subtotal DECIMAL(10, 2) NOT NULL CHECK(subtotal > 0),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cart_id) REFERENCES carts(cart_id) ON DELETE CASCADE,
        UNIQUE (cart_id, product_id)
    );
    """
    
    CREATE_INDEXES_SQL = [
        f"CREATE INDEX IF NOT EXISTS idx_cart_id ON {TABLE_NAME}(cart_id);",
        f"CREATE INDEX IF NOT EXISTS idx_product_id ON {TABLE_NAME}(product_id);",
    ]
    
    def __init__(
        self,
        item_id: int = None,
        cart_id: int = None,
        product_id: int = None,
        quantity: int = None,
        unit_price: float = None,
        subtotal: float = None,
        created_at: datetime = None,
    ):
        self.item_id = item_id
        self.cart_id = cart_id
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price
        self.subtotal = subtotal
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price else 0.0,
            "subtotal": float(self.subtotal) if self.subtotal else 0.0,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "CartItem":
        return cls(
            item_id=row[0],
            cart_id=row[1],
            product_id=row[2],
            quantity=row[3],
            unit_price=float(row[4]),
            subtotal=float(row[5]),
            created_at=datetime.fromisoformat(row[6]) if isinstance(row[6], str) else row[6],
        )


class Order:
    """
    Order model representing a confirmed purchase order.
    
    Attributes:
        order_id (int): Primary key, auto-incremented
        user_id (int): User who placed the order
        cart_id (int): Cart that was checked out
        total_price (float): Total order amount
        status (str): Order status (pending, confirmed, shipped, cancelled)
        created_at (datetime): Order creation timestamp
        updated_at (datetime): Last status update timestamp
    """
    
    TABLE_NAME = "orders"
    
    CREATE_TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        cart_id INTEGER NOT NULL,
        total_price DECIMAL(10, 2) NOT NULL CHECK(total_price > 0),
        status TEXT NOT NULL DEFAULT 'confirmed' CHECK(status IN ('pending', 'confirmed', 'shipped', 'cancelled')),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
    );
    """
    
    CREATE_INDEXES_SQL = [
        f"CREATE INDEX IF NOT EXISTS idx_user_id ON {TABLE_NAME}(user_id);",
        f"CREATE INDEX IF NOT EXISTS idx_status ON {TABLE_NAME}(status);",
    ]
    
    def __init__(
        self,
        order_id: int = None,
        user_id: int = None,
        cart_id: int = None,
        total_price: float = None,
        status: str = "confirmed",
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.order_id = order_id
        self.user_id = user_id
        self.cart_id = cart_id
        self.total_price = total_price
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "cart_id": self.cart_id,
            "total_price": float(self.total_price) if self.total_price else 0.0,
            "status": self.status,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "Order":
        return cls(
            order_id=row[0],
            user_id=row[1],
            cart_id=row[2],
            total_price=float(row[3]),
            status=row[4],
            created_at=datetime.fromisoformat(row[5]) if isinstance(row[5], str) else row[5],
            updated_at=datetime.fromisoformat(row[6]) if isinstance(row[6], str) else row[6],
        )


class OrderItem:
    """
    OrderItem model representing items in a confirmed order (snapshot of cart at checkout).
    
    Attributes:
        order_item_id (int): Primary key
        order_id (int): Foreign key to Order
        product_id (int): Product that was ordered
        quantity (int): Quantity ordered
        unit_price (float): Price per unit at time of order
        subtotal (float): quantity * unit_price
    """
    
    TABLE_NAME = "order_items"
    
    CREATE_TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        unit_price DECIMAL(10, 2) NOT NULL CHECK(unit_price > 0),
        subtotal DECIMAL(10, 2) NOT NULL CHECK(subtotal > 0),
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
    );
    """
    
    CREATE_INDEXES_SQL = [
        f"CREATE INDEX IF NOT EXISTS idx_order_id ON {TABLE_NAME}(order_id);",
    ]
    
    def __init__(
        self,
        order_item_id: int = None,
        order_id: int = None,
        product_id: int = None,
        quantity: int = None,
        unit_price: float = None,
        subtotal: float = None,
    ):
        self.order_item_id = order_item_id
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price
        self.subtotal = subtotal
    
    def to_dict(self) -> dict:
        return {
            "order_item_id": self.order_item_id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price else 0.0,
            "subtotal": float(self.subtotal) if self.subtotal else 0.0,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "OrderItem":
        return cls(
            order_item_id=row[0],
            order_id=row[1],
            product_id=row[2],
            quantity=row[3],
            unit_price=float(row[4]),
            subtotal=float(row[5]),
        )

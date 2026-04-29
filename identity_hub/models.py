"""
Identity Hub - Database Models
Defines the User table schema for SQLite.
Uses raw SQL queries (no ORM) for lightweight, direct database access.
"""

from datetime import datetime


class User:
    """
    User model representing a user in the identity.db database.
    
    Attributes:
        user_id (int): Primary key, auto-incremented
        username (str): Unique username (max 100 chars)
        email (str): Unique email address (max 100 chars)
        password_hash (str): bcrypt-hashed password (max 255 chars)
        created_at (datetime): Account creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
    TABLE_NAME = "users"
    
    # SQL schema for the users table
    CREATE_TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Indexes for performance
    CREATE_INDEXES_SQL = [
        f"CREATE INDEX IF NOT EXISTS idx_email ON {TABLE_NAME}(email);",
        f"CREATE INDEX IF NOT EXISTS idx_username ON {TABLE_NAME}(username);",
    ]
    
    def __init__(
        self,
        user_id: int = None,
        username: str = None,
        email: str = None,
        password_hash: str = None,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        """Initialize a User instance."""
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (for responses)."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "User":
        """
        Create a User instance from a database row.
        
        Row tuple structure: (user_id, username, email, password_hash, created_at, updated_at)
        """
        return cls(
            user_id=row[0],
            username=row[1],
            email=row[2],
            password_hash=row[3],
            created_at=datetime.fromisoformat(row[4]) if isinstance(row[4], str) else row[4],
            updated_at=datetime.fromisoformat(row[5]) if isinstance(row[5], str) else row[5],
        )

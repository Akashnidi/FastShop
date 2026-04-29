"""
Identity Hub - Database Module
Manages SQLite database connections and migrations using aiosqlite.
Ensures thread-safe async operations for concurrent requests.
"""

import aiosqlite
import os
from typing import Optional
from models import User


class Database:
    """
    Async SQLite database manager for Identity Hub.
    Handles connection pooling, migrations, and query execution.
    """
    
    def __init__(self, db_path: str = "identity.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file (default: identity.db)
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
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
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
        
        # Create users table
        await self.conn.execute(User.CREATE_TABLE_SQL)
        
        # Create indexes
        for index_sql in User.CREATE_INDEXES_SQL:
            await self.conn.execute(index_sql)
        
        await self.conn.commit()
        print("✓ Database migrations completed")
    
    async def create_user(self, username: str, email: str, password_hash: str) -> User:
        """
        Create a new user in the database.
        
        Args:
            username: Unique username
            email: Unique email address
            password_hash: Bcrypt-hashed password
        
        Returns:
            User object with assigned user_id
        
        Raises:
            aiosqlite.IntegrityError: If username or email already exists
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"""
        INSERT INTO {User.TABLE_NAME} (username, email, password_hash)
        VALUES (?, ?, ?)
        """
        
        try:
            cursor = await self.conn.execute(sql, (username, email, password_hash))
            await self.conn.commit()
            
            user_id = cursor.lastrowid
            user = User(user_id=user_id, username=username, email=email, password_hash=password_hash)
            return user
        except aiosqlite.IntegrityError as e:
            raise ValueError(f"User with this email or username already exists") from e
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user by email address.
        
        Args:
            email: Email address to search for
        
        Returns:
            User object if found, None otherwise
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"SELECT * FROM {User.TABLE_NAME} WHERE email = ? LIMIT 1"
        cursor = await self.conn.execute(sql, (email,))
        row = await cursor.fetchone()
        
        if row:
            return User.from_row(row)
        return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve user by user ID.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            User object if found, None otherwise
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"SELECT * FROM {User.TABLE_NAME} WHERE user_id = ? LIMIT 1"
        cursor = await self.conn.execute(sql, (user_id,))
        row = await cursor.fetchone()
        
        if row:
            return User.from_row(row)
        return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve user by username.
        
        Args:
            username: Username to search for
        
        Returns:
            User object if found, None otherwise
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"SELECT * FROM {User.TABLE_NAME} WHERE username = ? LIMIT 1"
        cursor = await self.conn.execute(sql, (username,))
        row = await cursor.fetchone()
        
        if row:
            return User.from_row(row)
        return None
    
    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """
        Update user fields.
        
        Args:
            user_id: User ID to update
            **kwargs: Fields to update (username, email, password_hash, etc.)
        
        Returns:
            Updated User object if found, None otherwise
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        if not kwargs:
            return await self.get_user_by_id(user_id)
        
        # Only allow updating specific fields
        allowed_fields = {"username", "email", "password_hash"}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_fields:
            return await self.get_user_by_id(user_id)
        
        # Build dynamic SQL
        set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
        values = list(update_fields.values()) + [user_id]
        
        sql = f"""
        UPDATE {User.TABLE_NAME}
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """
        
        await self.conn.execute(sql, values)
        await self.conn.commit()
        
        return await self.get_user_by_id(user_id)
    
    async def delete_user(self, user_id: int) -> bool:
        """
        Delete a user by ID.
        
        Args:
            user_id: User ID to delete
        
        Returns:
            True if user was deleted, False if not found
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        sql = f"DELETE FROM {User.TABLE_NAME} WHERE user_id = ?"
        cursor = await self.conn.execute(sql, (user_id,))
        await self.conn.commit()
        
        return cursor.rowcount > 0
    
    async def user_exists(self, email: str = None, username: str = None) -> bool:
        """
        Check if a user exists by email or username.
        
        Args:
            email: Email to check
            username: Username to check
        
        Returns:
            True if user exists, False otherwise
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        if email:
            cursor = await self.conn.execute(
                f"SELECT 1 FROM {User.TABLE_NAME} WHERE email = ? LIMIT 1",
                (email,)
            )
        elif username:
            cursor = await self.conn.execute(
                f"SELECT 1 FROM {User.TABLE_NAME} WHERE username = ? LIMIT 1",
                (username,)
            )
        else:
            return False
        
        return await cursor.fetchone() is not None


# Global database instance
db = Database(os.getenv("DATABASE_PATH", "identity.db"))

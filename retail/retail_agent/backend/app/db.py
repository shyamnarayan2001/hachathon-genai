# backend/app/db.py
import aiosqlite
from contextlib import asynccontextmanager
from typing import Dict, List, Any, Optional
import logging
from .models import Customer, Product, Order

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "database/retail.db"):
        self.db_path = db_path
    
    async def initialize(self):
        """Initialize the database and create tables"""
        async with self.get_connection() as conn:
            await conn.executescript("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    preferred_activity TEXT,
                    shoe_size TEXT,
                    address TEXT
                );
                
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    activity TEXT,
                    size TEXT,
                    price REAL,
                    stock INTEGER
                );
                
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY,
                    customer_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER,
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (id),
                    FOREIGN KEY (product_id) REFERENCES inventory (id)
                );
            """)
            
            # Add some sample data if tables are empty
            cursor = await conn.execute("SELECT COUNT(*) FROM customers")
            count = await cursor.fetchone()
            if count[0] == 0:
                await self._insert_sample_data(conn)
            
            await conn.commit()
            logger.info("Database initialized successfully")

    async def _insert_sample_data(self, conn):
        """Insert sample data into the database"""
        # Sample customers
        await conn.executemany(
            """INSERT INTO customers (name, preferred_activity, shoe_size, address) 
               VALUES (?, ?, ?, ?)""",
            [
                ("John Doe", "running", "10", "123 Main St"),
                ("Jane Smith", "walking", "8", "456 Oak Ave"),
                ("Mike Johnson", "hiking", "11", "789 Pine Rd")
            ]
        )

        # Sample inventory
        await conn.executemany(
            """INSERT INTO inventory (name, activity, size, price, stock) 
               VALUES (?, ?, ?, ?, ?)""",
            [
                ("Speed Runner Pro", "running", "10", 129.99, 5),
                ("Speed Runner Pro", "running", "9", 129.99, 3),
                ("Speed Runner Pro", "running", "11", 129.99, 2),
                ("Trail Blazer X", "hiking", "10", 159.99, 4),
                ("Trail Blazer X", "hiking", "9", 159.99, 3),
                ("Comfort Walker", "walking", "10", 89.99, 6),
                ("Comfort Walker", "walking", "11", 89.99, 4),
                ("Marathon Elite", "running", "10", 149.99, 3),
                ("Mountain Explorer", "hiking", "10", 179.99, 2),
                ("Daily Walker Plus", "walking", "10", 99.99, 5)
            ]
        )
    
    @asynccontextmanager
    async def get_connection(self):
        """Async context manager for database connections"""
        conn = await aiosqlite.connect(self.db_path)
        try:
            yield conn
        finally:
            await conn.close()
    
    async def get_customers(self) -> List[Customer]:
        """Get all customers"""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM customers")
            results = await cursor.fetchall()
            return [Customer(**dict(row)) for row in results]
    
    async def get_customer(self, name: str) -> Optional[Customer]:
        """Get customer by name"""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM customers WHERE name LIKE ?",
                (f"%{name}%",)
            )
            result = await cursor.fetchone()
            if result:
                return Customer(**dict(result))
            return None
    
    async def get_inventory(self, activity: Optional[str] = None, size: Optional[str] = None) -> List[Product]:
        """Get available inventory with optional filtering"""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            query = "SELECT * FROM inventory WHERE stock > 0"
            params = []
            
            if activity:
                query += " AND activity = ?"
                params.append(activity)
            if size:
                query += " AND size = ?"
                params.append(size)
            
            cursor = await conn.execute(query, params)
            results = await cursor.fetchall()
            return [Product(**dict(row)) for row in results]
    
    async def place_order(self, customer_id: int, product_id: int, quantity: int = 1) -> Optional[int]:
        """Place an order and return the order ID if successful"""
        try:
            async with self.get_connection() as conn:
                # Check stock availability
                cursor = await conn.execute(
                    "SELECT stock FROM inventory WHERE id = ?",
                    (product_id,)
                )
                stock = await cursor.fetchone()
                if not stock or stock[0] < quantity:
                    return None
                
                # Update inventory
                await conn.execute(
                    "UPDATE inventory SET stock = stock - ? WHERE id = ?",
                    (quantity, product_id)
                )
                
                # Create order
                cursor = await conn.execute(
                    """INSERT INTO orders (customer_id, product_id, quantity)
                       VALUES (?, ?, ?)""",
                    (customer_id, product_id, quantity)
                )
                await conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return None
    
    async def add_customer(self, customer: Customer) -> Optional[int]:
        """Add a new customer and return the customer ID if successful"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute("""
                    INSERT INTO customers (name, preferred_activity, shoe_size, address)
                    VALUES (?, ?, ?, ?)
                """, (customer.name, customer.preferred_activity, customer.shoe_size, customer.address))
                await conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding customer: {str(e)}")
            return None
            
    async def get_order(self, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM orders WHERE id = ?",
                (order_id,)
            )
            result = await cursor.fetchone()
            if result:
                return Order(**dict(result))
            return None

    async def get_customer_orders(self, customer_id: int) -> List[Order]:
        """Get all orders for a customer"""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """SELECT o.*, i.name as product_name, i.price 
                   FROM orders o 
                   JOIN inventory i ON o.product_id = i.id 
                   WHERE o.customer_id = ? 
                   ORDER BY o.order_date DESC""",
                (customer_id,)
            )
            results = await cursor.fetchall()
            return [Order(**dict(row)) for row in results]
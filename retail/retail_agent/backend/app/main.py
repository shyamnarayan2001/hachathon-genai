from fastapi import FastAPI, WebSocket, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
from .agents import RetailAgent
from .models import (
    ChatMessage, 
    ChatResponse, 
    Customer, 
    Product, 
    Order,
    CustomerCreate,
    OrderCreate,
    HealthResponse
)
from .config import Settings
from .db import Database
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()

# Initialize FastAPI and database
app = FastAPI(
    title="Retail Agent API",
    description="A retail chatbot API with inventory management and order processing",
    version="1.0.0"
)

# Initialize database
db = Database()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
# backend/app/main.py

@app.on_event("startup")
async def startup_event():
    """Initialize database and agents on startup"""
    try:
        await db.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application")
    
# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check the health of the API and its dependencies"""
    try:
        # Test database connection
        async with db.get_connection() as conn:
            await conn.execute("SELECT 1")
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version=app.version,
            database_status="connected"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": app.version,
                "database_status": "disconnected",
                "error": str(e)
            }
        )

# Existing chat endpoints
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    agent = RetailAgent(db=db)  # Pass database instance to agent
    
    try:
        while True:
            message = await websocket.receive_text()
            response = await agent.process_message(message)
            await websocket.send_text(response)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

# backend/app/main.py (just the chat endpoint part)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Process chat messages and return responses"""
    try:
        agent = RetailAgent(db=db)
        response = await agent.process_message(message.content)
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return ChatResponse(
            response="I apologize, but I'm having trouble processing your request at the moment. Please try again."
        )
        
# Customer endpoints
@app.post("/api/customers", response_model=Customer)
async def create_customer(customer: CustomerCreate):
    """Create a new customer"""
    try:
        success = await db.add_customer(customer)
        if success:
            created_customer = await db.get_customer(customer.name)
            if created_customer:
                return created_customer
        raise HTTPException(status_code=400, detail="Failed to create customer")
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{name}", response_model=Customer)
async def get_customer(name: str):
    """Get customer by name"""
    try:
        customer = await db.get_customer(name)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Inventory endpoints
@app.get("/api/inventory", response_model=List[Product])
async def get_inventory(activity: Optional[str] = None, size: Optional[str] = None):
    """Get available inventory with optional filtering"""
    try:
        inventory = await db.get_inventory(activity=activity, size=size)
        return inventory
    except Exception as e:
        logger.error(f"Error retrieving inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Order endpoints
@app.post("/api/orders", response_model=Order)
async def create_order(order: OrderCreate):
    """Create a new order"""
    try:
        order_id = await db.place_order(
            customer_id=order.customer_id,
            product_id=order.product_id,
            quantity=order.quantity
        )
        if not order_id:
            raise HTTPException(status_code=400, detail="Failed to create order")
        
        created_order = await db.get_order(order_id)
        if created_order:
            return created_order
        raise HTTPException(status_code=404, detail="Order not found after creation")
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/{customer_id}", response_model=List[Order])
async def get_customer_orders(customer_id: int):
    """Get all orders for a customer"""
    try:
        orders = await db.get_customer_orders(customer_id)
        return orders
    except Exception as e:
        logger.error(f"Error retrieving orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# backend/app/main.py
# ... (previous imports remain the same)

# Add this new endpoint
@app.get("/api/customers", response_model=List[Customer])
async def get_customers():
    """Get all customers"""
    try:
        customers = await db.get_customers()
        return customers
    except Exception as e:
        logger.error(f"Error retrieving customers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add this method to the Database class in db.py
async def get_customers(self) -> List[Customer]:
    """Get all customers"""
    async with self.get_connection() as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM customers")
        results = await cursor.fetchall()
        return [Customer(**dict(row)) for row in results]
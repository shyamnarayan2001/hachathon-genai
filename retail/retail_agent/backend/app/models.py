# backend/app/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")
    version: str = Field(..., description="API version")
    database_status: str = Field(..., description="Database connection status")

class ChatMessage(BaseModel):
    """Chat message request model"""
    content: str = Field(..., description="The message content from the user")

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="The response from the agent")

class CustomerBase(BaseModel):
    """Base customer model"""
    name: str
    preferred_activity: Optional[str] = None
    shoe_size: Optional[str] = None
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    """Customer creation model"""
    pass

class Customer(CustomerBase):
    """Customer response model"""
    id: int
    
    class Config:
        from_attributes = True

class Product(BaseModel):
    """Product model"""
    id: int
    name: str
    activity: str
    size: str
    price: float
    stock: int
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    """Order creation model"""
    customer_id: int
    product_id: int
    quantity: int = Field(gt=0)

class Order(BaseModel):
    """Order response model"""
    id: int
    customer_id: int
    product_id: int
    quantity: int
    order_date: datetime
    
    class Config:
        from_attributes = True

class ApiResponse(BaseModel):
    """Generic API response model"""
    status: str = Field(..., description="Success or error status")
    data: Optional[Any] = Field(None, description="Response data")
    message: str = Field(..., description="Response message")

class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error detail message")

class InventoryFilter(BaseModel):
    """Inventory filter model"""
    activity: Optional[str] = None
    size: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

class OrderStatus(BaseModel):
    """Order status response model"""
    order_id: int
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None
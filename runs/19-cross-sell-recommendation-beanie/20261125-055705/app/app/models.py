from typing import List, Optional
from datetime import datetime
from beanie import Document
from pydantic import Field

class Product(Document):
    id: str = Field(..., alias="_id")
    name: Optional[str]
    embedding: Optional[List[float]]
    embedding_model: Optional[str]
    dimensions: Optional[int]

    class Settings:
        name = "products"

class ProductPair(Document):
    id: Optional[str] = Field(None, alias="_id")
    product_ids: List[str]
    count: int = 0
    embedding: Optional[List[float]]
    embedding_model: Optional[str]
    dimensions: Optional[int]
    updated_at: Optional[datetime]

    class Settings:
        name = "product_pairs"

class Order(Document):
    id: Optional[str] = Field(None, alias="_id")
    items: List[str]
    ts: Optional[datetime]

    class Settings:
        name = "orders"

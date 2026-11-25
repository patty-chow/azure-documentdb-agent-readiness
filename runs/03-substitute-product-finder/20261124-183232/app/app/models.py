from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from beanie import Document
from pydantic import Field


class Product(Document):
    """Beanie document model for a product.

    Fields:
    - product_id: a short string SKU or identifier used by the sample UI and queries
    - name, description, category: basic product metadata
    - price: numeric price
    - attributes: arbitrary attribute dictionary (colors, size, etc.)
    - embedding: a list of floats representing the semantic embedding for the product
    - created_at: timestamp for when the document was created

    The embedding field is stored as an array of floats and is the field used by the vector index.
    """

    product_id: str = Field(..., index=True)
    name: str
    description: str
    category: Optional[str]
    price: float
    attributes: Dict[str, Any] = Field(default_factory=dict)
    embedding: List[float] = Field(default_factory=list)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    class Settings:
        # Beanie uses this to name the collection when not provided explicitly
        name = "products"

    class Config:
        schema_extra = {
            "example": {
                "product_id": "SKU-0001",
                "name": "Example Widget",
                "description": "An example product for the sample app.",
                "category": "Widgets",
                "price": 9.99,
                "attributes": {"color": "red", "size": "M"},
                "embedding": [0.0, 0.1, -0.2],
            }
        }

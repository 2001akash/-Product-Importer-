from pydantic import BaseModel, AnyHttpUrl
from typing import Optional

class ProductBase(BaseModel):
    sku: str
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    active: Optional[bool] = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class ProductOut(ProductBase):
    id: int

    class Config:
        orm_mode = True

class WebhookBase(BaseModel):
    url: AnyHttpUrl
    event_types: Optional[str] = "import_complete"
    enabled: Optional[bool] = True

class WebhookOut(WebhookBase):
    id: int
    class Config:
        orm_mode = True

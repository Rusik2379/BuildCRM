from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    unit: str = "шт"
    price: float = 0
    notes: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int

    model_config = {"from_attributes": True}

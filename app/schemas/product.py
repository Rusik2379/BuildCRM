from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    category: str | None = None
    unit: str = "шт"
    description: str | None = None
    is_wholesale: bool = False


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int

    model_config = {"from_attributes": True}

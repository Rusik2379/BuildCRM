from pydantic import BaseModel


class StockItemBase(BaseModel):
    product_id: int
    city_name: str | None = None
    supplier_name: str | None = None
    quantity: float = 0
    purchase_price: float = 0
    retail_price: float = 0
    small_wholesale_price: float = 0
    large_wholesale_price: float = 0
    notes: str | None = None


class StockItemCreate(StockItemBase):
    pass


class StockItemRead(StockItemBase):
    id: int
    product_name: str | None = None

    model_config = {"from_attributes": True}

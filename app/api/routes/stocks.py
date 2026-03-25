from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.stock import StockItemCreate
from app.services.stock_service import StockService

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("")
def list_stock(
    search: str | None = Query(default=None),
    city: str | None = Query(default=None),
    supplier: str | None = Query(default=None),
    category: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
):
    items = StockService.list_stock(db, search=search, city=city, supplier=supplier, category=category)
    return [
        {
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else None,
            "city_name": item.city.name if item.city else None,
            "supplier_name": item.supplier.name if item.supplier else None,
            "quantity": float(item.quantity or 0),
            "purchase_price": float(item.purchase_price or 0),
            "retail_price": float(item.retail_price or 0),
            "small_wholesale_price": float(item.small_wholesale_price or 0),
            "large_wholesale_price": float(item.large_wholesale_price or 0),
            "notes": item.notes,
        }
        for item in items
    ]


@router.post("")
def create_stock_item(payload: StockItemCreate, db: Session = Depends(get_db_session)):
    item = StockService.create_stock_item(db, **payload.model_dump())
    return {"id": item.id}

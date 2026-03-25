from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.product import Product
from app.models.stock import City, StockItem, Supplier


class StockService:
    @staticmethod
    def list_stock(
        db: Session,
        search: str | None = None,
        city: str | None = None,
        supplier: str | None = None,
        category: str | None = None,
    ) -> list[StockItem]:
        query = db.query(StockItem).options(
            joinedload(StockItem.product),
            joinedload(StockItem.city),
            joinedload(StockItem.supplier),
        )
        if search:
            term = f"%{search.strip()}%"
            query = query.join(StockItem.product).outerjoin(StockItem.city).outerjoin(StockItem.supplier).filter(
                or_(
                    Product.name.ilike(term),
                    Product.category.ilike(term),
                    Supplier.name.ilike(term),
                    City.name.ilike(term),
                    StockItem.notes.ilike(term),
                )
            )
        if city and city != "all":
            query = query.join(StockItem.city).filter(City.name == city)
        if supplier and supplier != "all":
            query = query.join(StockItem.supplier).filter(Supplier.name == supplier)
        if category and category != "all":
            query = query.join(StockItem.product).filter(Product.category == category)
        return query.order_by(StockItem.updated_at.desc()).all()

    @staticmethod
    def create_stock_item(
        db: Session,
        product_id: int,
        city_name: str | None,
        supplier_name: str | None,
        quantity: float,
        purchase_price: float,
        retail_price: float,
        small_wholesale_price: float,
        large_wholesale_price: float,
        notes: str | None = None,
    ) -> StockItem:
        city = None
        supplier = None
        if city_name and city_name.strip():
            city = db.query(City).filter(City.name == city_name.strip()).first()
            if not city:
                city = City(name=city_name.strip())
                db.add(city)
                db.flush()
        if supplier_name and supplier_name.strip():
            supplier = db.query(Supplier).filter(Supplier.name == supplier_name.strip()).first()
            if not supplier:
                supplier = Supplier(name=supplier_name.strip(), city_id=city.id if city else None)
                db.add(supplier)
                db.flush()
            elif city and supplier.city_id is None:
                supplier.city_id = city.id
        item = StockItem(
            product_id=product_id,
            city_id=city.id if city else None,
            supplier_id=supplier.id if supplier else None,
            quantity=quantity,
            purchase_price=purchase_price,
            retail_price=retail_price,
            small_wholesale_price=small_wholesale_price,
            large_wholesale_price=large_wholesale_price,
            notes=notes,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_cities(db: Session) -> list[str]:
        return [row[0] for row in db.query(City.name).order_by(City.name).all()]

    @staticmethod
    def get_suppliers(db: Session) -> list[str]:
        return [row[0] for row in db.query(Supplier.name).order_by(Supplier.name).all()]

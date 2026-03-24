from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.product import Product


class ProductService:
    @staticmethod
    def list_products(db: Session, search: str | None = None) -> list[Product]:
        query = db.query(Product)
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(term),
                    Product.unit.ilike(term),
                    Product.notes.ilike(term),
                )
            )
        return query.order_by(Product.name.asc()).all()

    @staticmethod
    def create_product(db: Session, **data) -> Product:
        product = Product(**data)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_or_create_by_name(db: Session, query: str) -> Product:
        value = query.strip()
        existing = db.query(Product).filter(Product.name.ilike(value)).first()
        if existing:
            return existing
        product = Product(name=value, unit="шт", price=0)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

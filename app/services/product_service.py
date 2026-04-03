from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.product import Product


class ProductService:
    @staticmethod
    def list_products(db: Session, search: str | None = None, category: str | None = None, wholesale: str | None = None) -> list[Product]:
        query = db.query(Product)
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(term),
                    Product.category.ilike(term),
                    Product.unit.ilike(term),
                    Product.description.ilike(term),
                )
            )
        if category and category != "all":
            query = query.filter(Product.category == category)
        if wholesale == "yes":
            query = query.filter(Product.is_wholesale.is_(True))
        elif wholesale == "no":
            query = query.filter(Product.is_wholesale.is_(False))
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
        product = Product(name=value, unit="шт")
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_categories(db: Session) -> list[str]:
        return [row[0] for row in db.query(Product.category).filter(Product.category.isnot(None), Product.category != "").distinct().order_by(Product.category).all()]

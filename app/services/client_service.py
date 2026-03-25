from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.client import Client


class ClientService:
    @staticmethod
    def list_clients(db: Session, search: str | None = None, source: str | None = None, category: str | None = None) -> list[Client]:
        query = db.query(Client)
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Client.name.ilike(term),
                    Client.phone.ilike(term),
                    Client.second_phone.ilike(term),
                    Client.address.ilike(term),
                    Client.notes.ilike(term),
                    Client.source.ilike(term),
                    Client.category.ilike(term),
                )
            )
        if source and source != "all":
            query = query.filter(Client.source == source)
        if category and category != "all":
            query = query.filter(Client.category == category)
        return query.order_by(Client.name.asc()).all()

    @staticmethod
    def create_client(db: Session, **data) -> Client:
        client = Client(**data)
        db.add(client)
        db.commit()
        db.refresh(client)
        return client

    @staticmethod
    def get_or_create_by_query(db: Session, query: str) -> Client:
        value = query.strip()
        existing = (
            db.query(Client)
            .filter(or_(Client.phone == value, Client.second_phone == value, func.lower(Client.name) == value.lower()))
            .first()
        )
        if existing:
            return existing
        name = value
        phone = value if any(ch.isdigit() for ch in value) else f"Не указан ({value})"
        client = Client(name=name, phone=phone)
        db.add(client)
        db.commit()
        db.refresh(client)
        return client

    @staticmethod
    def get_sources(db: Session) -> list[str]:
        return [row[0] for row in db.query(Client.source).filter(Client.source.isnot(None), Client.source != "").distinct().order_by(Client.source).all()]

    @staticmethod
    def get_categories(db: Session) -> list[str]:
        return [row[0] for row in db.query(Client.category).filter(Client.category.isnot(None), Client.category != "").distinct().order_by(Client.category).all()]

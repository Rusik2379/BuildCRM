from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.client import Client


class ClientService:
    @staticmethod
    def list_clients(db: Session, search: str | None = None) -> list[Client]:
        query = db.query(Client)
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Client.name.ilike(term),
                    Client.phone.ilike(term),
                    Client.address.ilike(term),
                    Client.notes.ilike(term),
                )
            )
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
            .filter(or_(Client.phone == value, Client.name.ilike(value)))
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

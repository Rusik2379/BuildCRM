from sqlalchemy.orm import Session, joinedload

from app.models.client_request import ClientRequest, RequestKind, RequestStatus


class RequestService:
    @staticmethod
    def list_requests(db: Session, status: str | None = None, kind: str | None = None) -> list[ClientRequest]:
        query = db.query(ClientRequest).options(
            joinedload(ClientRequest.client),
            joinedload(ClientRequest.product),
        )
        if status and status != "all":
            query = query.filter(ClientRequest.status == RequestStatus(status))
        if kind and kind != "all":
            query = query.filter(ClientRequest.kind == RequestKind(kind))
        return query.order_by(ClientRequest.created_at.desc()).all()

    @staticmethod
    def create_request(db: Session, **data) -> ClientRequest:
        request = ClientRequest(**data)
        db.add(request)
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def list_by_client(db: Session, client_id: int, kind: str | None = None) -> list[ClientRequest]:
        query = (
            db.query(ClientRequest)
            .options(joinedload(ClientRequest.product))
            .filter(ClientRequest.client_id == client_id)
        )
        if kind and kind != "all":
            query = query.filter(ClientRequest.kind == RequestKind(kind))
        return query.order_by(ClientRequest.created_at.desc()).all()

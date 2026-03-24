from sqlalchemy.orm import Session, joinedload

from app.models.client_request import ClientRequest, RequestStatus


class RequestService:
    @staticmethod
    def list_requests(db: Session, status: str | None = None) -> list[ClientRequest]:
        query = db.query(ClientRequest).options(
            joinedload(ClientRequest.client),
            joinedload(ClientRequest.product),
        )
        if status and status != "all":
            query = query.filter(ClientRequest.status == RequestStatus(status))
        return query.order_by(ClientRequest.created_at.desc()).all()

    @staticmethod
    def create_request(db: Session, **data) -> ClientRequest:
        request = ClientRequest(**data)
        db.add(request)
        db.commit()
        db.refresh(request)
        return request

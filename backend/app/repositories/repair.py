from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.models import RepairRequest, AIDiagnosis, RequestImage, RequestStatus


class RepairRequestRepository:
    """Repository for RepairRequest database operations."""

    @staticmethod
    def get_by_id(db: Session, request_id: str) -> Optional[RepairRequest]:
        """Get a repair request by ID."""
        return db.query(RepairRequest).filter(RepairRequest.id == request_id).first()

    @staticmethod
    def get_by_customer(db: Session, customer_id: str) -> List[RepairRequest]:
        """Get all repair requests for a customer."""
        return (
            db.query(RepairRequest)
            .filter(RepairRequest.customer_id == customer_id)
            .order_by(RepairRequest.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_mechanic(db: Session, mechanic_id: str) -> List[RepairRequest]:
        """Get all repair requests assigned to a mechanic."""
        return (
            db.query(RepairRequest)
            .filter(RepairRequest.mechanic_id == mechanic_id)
            .order_by(RepairRequest.created_at.desc())
            .all()
        )

    @staticmethod
    def get_pending_requests(db: Session) -> List[RepairRequest]:
        """Get all pending repair requests."""
        return (
            db.query(RepairRequest)
            .filter(RepairRequest.status == RequestStatus.pending)
            .order_by(RepairRequest.created_at.desc())
            .all()
        )

    @staticmethod
    def create(db: Session, request: RepairRequest) -> RepairRequest:
        """Create a new repair request."""
        db.add(request)
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def update(db: Session, request: RepairRequest) -> RepairRequest:
        """Update an existing repair request."""
        db.commit()
        db.refresh(request)
        return request


class AIDiagnosisRepository:
    """Repository for AIDiagnosis database operations."""

    @staticmethod
    def get_by_request_id(db: Session, request_id: str) -> Optional[AIDiagnosis]:
        """Get AI diagnosis by request ID."""
        return db.query(AIDiagnosis).filter(AIDiagnosis.request_id == request_id).first()

    @staticmethod
    def create(db: Session, diagnosis: AIDiagnosis) -> AIDiagnosis:
        """Create a new AI diagnosis."""
        db.add(diagnosis)
        db.commit()
        db.refresh(diagnosis)
        return diagnosis

    @staticmethod
    def update(db: Session, diagnosis: AIDiagnosis) -> AIDiagnosis:
        """Update an existing AI diagnosis."""
        db.commit()
        db.refresh(diagnosis)
        return diagnosis


class RequestImageRepository:
    """Repository for RequestImage database operations."""

    @staticmethod
    def get_by_request_id(db: Session, request_id: str) -> List[RequestImage]:
        """Get all images for a request."""
        return db.query(RequestImage).filter(RequestImage.request_id == request_id).all()

    @staticmethod
    def create(db: Session, image: RequestImage) -> RequestImage:
        """Create a new request image."""
        db.add(image)
        db.commit()
        db.refresh(image)
        return image

    @staticmethod
    def delete(db: Session, image: RequestImage) -> None:
        """Delete a request image."""
        db.delete(image)
        db.commit()

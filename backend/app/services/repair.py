from typing import List, Optional
from geoalchemy2 import Geometry
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
from sqlalchemy import cast, func

from app.db.models import RepairRequest, AIDiagnosis, RequestImage, RequestStatus
from app.repositories.repair import (
    RepairRequestRepository,
    AIDiagnosisRepository,
    RequestImageRepository,
)
from app.repositories.mechanic import MechanicRepository
from app.repositories.vehicle import VehicleRepository
from app.schemas.repair import (
    RepairRequestCreate,
    RepairRequestUpdate,
    RepairRequestResponse,
    RepairRequestWithDetails,
    AIDiagnosisResponse,
    RequestImageResponse,
)
from app.services.notification import NotificationService


class RepairRequestService:
    """Service for repair request business logic."""

    @staticmethod
    def create_request(
        db: Session, customer_id: str, request_data: RepairRequestCreate
    ) -> RepairRequestResponse:
        """Create a new repair request."""
        if (request_data.latitude is None) != (request_data.longitude is None):
            raise ValueError("Latitude and longitude must be provided together")
        if request_data.vehicle_id:
            vehicle = VehicleRepository.get_by_id(db, request_data.vehicle_id)
            if not vehicle or str(vehicle.customer_id) != str(customer_id):
                raise ValueError("Selected vehicle was not found for this customer")

        mechanic_id = request_data.mechanic_id
        if mechanic_id:
            mechanic = MechanicRepository.get_by_id(db, mechanic_id)
            if not mechanic:
                raise ValueError("Mechanic profile not found")
            if not mechanic.is_online:
                raise ValueError("Selected mechanic is currently offline")

        # Create location point from lat/lon
        location = None
        if request_data.latitude is not None and request_data.longitude is not None:
            location = WKTElement(
                f"POINT({request_data.longitude} {request_data.latitude})",
                srid=4326,
            )

        request = RepairRequest(
            customer_id=customer_id,
            vehicle_id=request_data.vehicle_id,
            mechanic_id=mechanic_id,
            description=request_data.description,
            customer_location=location,
            status=RequestStatus.pending,
        )

        created_request = RepairRequestRepository.create(db, request)
        NotificationService.notify_new_repair_request(db, created_request)
        return RepairRequestService._to_response(db, created_request)

    @staticmethod
    def get_customer_requests(db: Session, customer_id: str) -> List[RepairRequestResponse]:
        """Get all repair requests for a customer."""
        requests = RepairRequestRepository.get_by_customer(db, customer_id)
        return [RepairRequestService._to_response(db, r) for r in requests]

    @staticmethod
    def get_mechanic_requests(db: Session, mechanic_id: str) -> List[RepairRequestResponse]:
        """Get all repair requests assigned to a mechanic."""
        requests = RepairRequestRepository.get_by_mechanic(db, mechanic_id)
        return [RepairRequestService._to_response(db, r) for r in requests]

    @staticmethod
    def get_request(db: Session, request_id: str) -> RepairRequestWithDetails:
        """Get a repair request with full details."""
        request = RepairRequestRepository.get_by_id(db, request_id)
        if not request:
            raise ValueError("Repair request not found")

        return RepairRequestService._to_detailed_response(db, request)

    @staticmethod
    def update_request_status(
        db: Session, request_id: str, mechanic_id: str, status_data: RepairRequestUpdate
    ) -> RepairRequestResponse:
        """Update the status of a repair request (mechanic only)."""
        request = RepairRequestRepository.get_by_id(db, request_id)
        if not request:
            raise ValueError("Repair request not found")

        # Validate status transitions
        if request.status == RequestStatus.completed:
            raise ValueError("Cannot update a completed request")
        if request.status == RequestStatus.cancelled:
            raise ValueError("Cannot update a cancelled request")

        if request.mechanic_id and str(request.mechanic_id) != str(mechanic_id):
            raise ValueError("Request already assigned to another mechanic")

        old_status = request.status

        if status_data.status == RequestStatus.accepted:
            if request.status != RequestStatus.pending:
                raise ValueError("Cannot accept a request that is not pending")
            request.mechanic_id = mechanic_id
        elif status_data.status == RequestStatus.cancelled:
            if request.status != RequestStatus.pending:
                raise ValueError("Cannot reject a request that is not pending")
            request.mechanic_id = mechanic_id
        elif status_data.status == RequestStatus.completed:
            if request.status != RequestStatus.accepted:
                raise ValueError("Only accepted requests can be completed")
        else:
            raise ValueError("Mechanics cannot move a request back to pending")

        request.status = status_data.status
        updated_request = RepairRequestRepository.update(db, request)

        # Dispatch notifications based on status change
        if updated_request.status == RequestStatus.accepted:
            shop_name = (
                updated_request.mechanic.shop_name
                if updated_request.mechanic
                else "Assigned Mechanic"
            )
            NotificationService.notify_request_accepted(db, updated_request, shop_name)
        elif updated_request.status == RequestStatus.completed:
            NotificationService.notify_repair_completed(db, updated_request)
        elif updated_request.status == RequestStatus.cancelled:
            NotificationService.notify_request_rejected(db, updated_request)
        else:
            old_val = old_status.value if hasattr(old_status, "value") else str(old_status)
            new_val = (
                updated_request.status.value
                if hasattr(updated_request.status, "value")
                else str(updated_request.status)
            )
            NotificationService.notify_status_changed(db, updated_request, old_val, new_val)

        return RepairRequestService._to_response(db, updated_request)

    @staticmethod
    def cancel_request(db: Session, request_id: str, customer_id: str) -> RepairRequestResponse:
        """Cancel a repair request (customer only)."""
        request = RepairRequestRepository.get_by_id(db, request_id)
        if not request:
            raise ValueError("Repair request not found")
        if str(request.customer_id) != str(customer_id):
            raise ValueError("Access denied")
        if request.status == RequestStatus.completed:
            raise ValueError("Cannot cancel a completed request")

        request.status = RequestStatus.cancelled
        updated_request = RepairRequestRepository.update(db, request)
        NotificationService.notify_request_rejected(db, updated_request)
        return RepairRequestService._to_response(db, updated_request)

    @staticmethod
    def get_pending_requests(db: Session) -> List[RepairRequestResponse]:
        """Get all pending repair requests (for mechanics to browse)."""
        requests = RepairRequestRepository.get_pending_requests(db)
        return [RepairRequestService._to_response(db, r) for r in requests]

    @staticmethod
    def _to_response(db: Session, request: RepairRequest) -> RepairRequestResponse:
        """Convert RepairRequest model to response schema."""
        # Extract lat/lon from location if available
        latitude = None
        longitude = None
        if request.customer_location:
            try:
                point = cast(RepairRequest.customer_location, Geometry(srid=4326))
                result = db.query(
                    func.ST_Y(point).label("lat"),
                    func.ST_X(point).label("lon"),
                ).filter(RepairRequest.id == request.id).first()
                if result and result.lat is not None and result.lon is not None:
                    latitude = float(result.lat)
                    longitude = float(result.lon)
            except Exception:
                pass

        return RepairRequestResponse(
            id=str(request.id),
            customer_id=str(request.customer_id),
            vehicle_id=str(request.vehicle_id) if request.vehicle_id else None,
            mechanic_id=str(request.mechanic_id) if request.mechanic_id else None,
            status=request.status,
            description=request.description,
            latitude=latitude,
            longitude=longitude,
            created_at=request.created_at.isoformat() if request.created_at else None,
            updated_at=request.updated_at.isoformat() if request.updated_at else None,
        )

    @staticmethod
    def _to_detailed_response(db: Session, request: RepairRequest) -> RepairRequestWithDetails:
        """Convert RepairRequest model to detailed response schema."""
        base_response = RepairRequestService._to_response(db, request)

        # Get vehicle info if available
        vehicle_info = None
        if request.vehicle:
            vehicle_info = {
                "id": str(request.vehicle.id),
                "make": request.vehicle.make,
                "model": request.vehicle.model,
                "year": request.vehicle.year,
            }

        # Get mechanic info if available
        mechanic_info = None
        if request.mechanic:
            mechanic_info = {
                "id": str(request.mechanic.id),
                "shop_name": request.mechanic.shop_name,
                "address": request.mechanic.address,
                "average_rating": request.mechanic.average_rating,
            }

        # Get AI diagnosis if available
        ai_diagnosis = None
        if request.ai_diagnosis:
            ai_diagnosis = AIDiagnosisResponse(
                id=str(request.ai_diagnosis.id),
                request_id=str(request.ai_diagnosis.request_id),
                possible_faults=request.ai_diagnosis.possible_faults,
                urgency=request.ai_diagnosis.urgency,
                ai_summary=request.ai_diagnosis.ai_summary,
            )

        # Get images if available
        images = [
            RequestImageResponse(
                id=str(img.id), request_id=str(img.request_id), image_url=img.image_url
            )
            for img in request.images
        ]

        return RepairRequestWithDetails(
            **base_response.model_dump(),
            vehicle_info=vehicle_info,
            mechanic_info=mechanic_info,
            ai_diagnosis=ai_diagnosis,
            images=images,
        )

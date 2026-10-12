from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.dependencies.auth import get_current_user, get_current_customer, get_current_mechanic
from app.schemas.repair import (
    RepairRequestCreate,
    RepairRequestUpdate,
    RepairRequestResponse,
    RepairRequestWithDetails,
)
from app.services.repair import RepairRequestService

router = APIRouter(prefix="/repairs", tags=["Repair Requests"])


@router.post("", response_model=RepairRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_repair_request(
    request_data: RepairRequestCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_customer)],
):
    """
    Create a new repair request.

    - **vehicle_id**: Optional vehicle ID
    - **description**: Description of the problem (10-2000 characters)
    - **latitude**: Customer's current latitude
    - **longitude**: Customer's current longitude
    """
    try:
        return RepairRequestService.create_request(db, str(current_user.id), request_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[RepairRequestResponse])
async def get_my_repair_requests(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get all repair requests for the current user.

    - Customers: Get their own requests
    - Mechanics: Get requests assigned to them
    """
    if current_user.role.value == "customer":
        return RepairRequestService.get_customer_requests(db, str(current_user.id))
    elif current_user.role.value == "mechanic":
        from app.repositories.mechanic import MechanicRepository
        profile = MechanicRepository.get_by_user_id(db, str(current_user.id))
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mechanic profile not found",
            )
        return RepairRequestService.get_mechanic_requests(db, str(profile.id))
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )


@router.get("/pending", response_model=List[RepairRequestResponse])
async def get_pending_requests(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_mechanic)],
):
    """
    Get all pending repair requests (for mechanics to browse and accept).
    """
    return RepairRequestService.get_pending_requests(db)


@router.get("/{request_id}", response_model=RepairRequestWithDetails)
async def get_repair_request(
    request_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get a specific repair request with full details.
    """
    try:
        request = RepairRequestService.get_request(db, request_id)

        # Check access permissions
        if current_user.role.value == "customer":
            if request.customer_id != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )
        elif current_user.role.value == "mechanic":
            from app.repositories.mechanic import MechanicRepository
            profile = MechanicRepository.get_by_user_id(db, str(current_user.id))
            if not profile or request.mechanic_id != str(profile.id):
                # Mechanics can see pending requests too
                if request.status.value != "pending":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied",
                    )

        return request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/{request_id}", response_model=RepairRequestResponse)
async def update_repair_request_status(
    request_id: str,
    status_data: RepairRequestUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_mechanic)],
):
    """
    Update the status of a repair request (mechanic only).

    - **status**: New status (pending, accepted, completed, cancelled)
    """
    from app.repositories.mechanic import MechanicRepository
    profile = MechanicRepository.get_by_user_id(db, str(current_user.id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mechanic profile not found",
        )

    try:
        return RepairRequestService.update_request_status(
            db, request_id, str(profile.id), status_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "Cannot" in str(e) else status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{request_id}", response_model=RepairRequestResponse)
async def cancel_repair_request(
    request_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_customer)],
):
    """
    Cancel a repair request (customer only).
    """
    try:
        return RepairRequestService.cancel_request(db, request_id, str(current_user.id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "Cannot" in str(e) else status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

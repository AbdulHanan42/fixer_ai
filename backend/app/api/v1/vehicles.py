from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.dependencies.auth import get_current_customer
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from app.services.vehicle import VehicleService

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_data: VehicleCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_customer)],
):
    """
    Create a new vehicle for the current customer.

    - **make**: Vehicle make (e.g., Toyota, Honda)
    - **model**: Vehicle model (e.g., Camry, Civic)
    - **year**: Vehicle year (1900-2100)
    """
    try:
        return VehicleService.create_vehicle(db, str(current_user.id), vehicle_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[VehicleResponse])
async def get_vehicles(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_customer)],
):
    """
    Get all vehicles for the current customer.
    """
    return VehicleService.get_customer_vehicles(db, str(current_user.id))


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_customer)],
):
    """
    Get a specific vehicle by ID.
    """
    try:
        return VehicleService.get_vehicle(db, vehicle_id, str(current_user.id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: str,
    vehicle_data: VehicleUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_customer)],
):
    """
    Update a vehicle.
    """
    try:
        return VehicleService.update_vehicle(db, vehicle_id, str(current_user.id), vehicle_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_customer)],
):
    """
    Delete a vehicle.
    """
    try:
        VehicleService.delete_vehicle(db, vehicle_id, str(current_user.id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

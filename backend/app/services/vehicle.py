from typing import List
from sqlalchemy.orm import Session

from app.db.models import Vehicle
from app.repositories.vehicle import VehicleRepository
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse


class VehicleService:
    """Service for vehicle business logic."""

    @staticmethod
    def create_vehicle(db: Session, customer_id: str, vehicle_data: VehicleCreate) -> VehicleResponse:
        """Create a new vehicle for a customer."""
        vehicle = Vehicle(
            customer_id=customer_id,
            make=vehicle_data.make,
            model=vehicle_data.model,
            year=vehicle_data.year,
        )
        created_vehicle = VehicleRepository.create(db, vehicle)
        return VehicleService._to_response(created_vehicle)

    @staticmethod
    def get_customer_vehicles(db: Session, customer_id: str) -> List[VehicleResponse]:
        """Get all vehicles for a customer."""
        vehicles = VehicleRepository.get_by_customer(db, customer_id)
        return [VehicleService._to_response(v) for v in vehicles]

    @staticmethod
    def get_vehicle(db: Session, vehicle_id: str, customer_id: str) -> VehicleResponse:
        """Get a specific vehicle for a customer."""
        vehicle = VehicleRepository.get_by_id(db, vehicle_id)
        if not vehicle:
            raise ValueError("Vehicle not found")
        if vehicle.customer_id != customer_id:
            raise ValueError("Access denied")
        return VehicleService._to_response(vehicle)

    @staticmethod
    def update_vehicle(
        db: Session, vehicle_id: str, customer_id: str, vehicle_data: VehicleUpdate
    ) -> VehicleResponse:
        """Update a vehicle."""
        vehicle = VehicleRepository.get_by_id(db, vehicle_id)
        if not vehicle:
            raise ValueError("Vehicle not found")
        if vehicle.customer_id != customer_id:
            raise ValueError("Access denied")

        # Update fields if provided
        if vehicle_data.make is not None:
            vehicle.make = vehicle_data.make
        if vehicle_data.model is not None:
            vehicle.model = vehicle_data.model
        if vehicle_data.year is not None:
            vehicle.year = vehicle_data.year

        updated_vehicle = VehicleRepository.update(db, vehicle)
        return VehicleService._to_response(updated_vehicle)

    @staticmethod
    def delete_vehicle(db: Session, vehicle_id: str, customer_id: str) -> None:
        """Delete a vehicle."""
        vehicle = VehicleRepository.get_by_id(db, vehicle_id)
        if not vehicle:
            raise ValueError("Vehicle not found")
        if vehicle.customer_id != customer_id:
            raise ValueError("Access denied")
        VehicleRepository.delete(db, vehicle)

    @staticmethod
    def _to_response(vehicle: Vehicle) -> VehicleResponse:
        """Convert Vehicle model to VehicleResponse schema."""
        return VehicleResponse(
            id=str(vehicle.id),
            customer_id=str(vehicle.customer_id),
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
        )

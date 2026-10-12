from typing import Optional, List
from sqlalchemy.orm import Session

from app.db.models import Vehicle


class VehicleRepository:
    """Repository for Vehicle database operations."""

    @staticmethod
    def get_by_id(db: Session, vehicle_id: str) -> Optional[Vehicle]:
        """Get a vehicle by ID."""
        return db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    @staticmethod
    def get_by_customer(db: Session, customer_id: str) -> List[Vehicle]:
        """Get all vehicles for a customer."""
        return db.query(Vehicle).filter(Vehicle.customer_id == customer_id).all()

    @staticmethod
    def create(db: Session, vehicle: Vehicle) -> Vehicle:
        """Create a new vehicle."""
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        return vehicle

    @staticmethod
    def update(db: Session, vehicle: Vehicle) -> Vehicle:
        """Update an existing vehicle."""
        db.commit()
        db.refresh(vehicle)
        return vehicle

    @staticmethod
    def delete(db: Session, vehicle: Vehicle) -> None:
        """Delete a vehicle."""
        db.delete(vehicle)
        db.commit()

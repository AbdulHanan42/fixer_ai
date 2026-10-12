from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.db.models import MechanicProfile, Service, MechanicService


class MechanicRepository:
    """Repository for MechanicProfile database operations."""

    @staticmethod
    def get_by_id(db: Session, profile_id: str) -> Optional[MechanicProfile]:
        """Get a mechanic profile by ID."""
        return db.query(MechanicProfile).filter(MechanicProfile.id == profile_id).first()

    @staticmethod
    def get_by_user_id(db: Session, user_id: str) -> Optional[MechanicProfile]:
        """Get a mechanic profile by user ID."""
        return db.query(MechanicProfile).filter(MechanicProfile.user_id == user_id).first()

    @staticmethod
    def create(db: Session, profile: MechanicProfile) -> MechanicProfile:
        """Create a new mechanic profile."""
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def update(db: Session, profile: MechanicProfile) -> MechanicProfile:
        """Update an existing mechanic profile."""
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def search_nearby(
        db: Session, latitude: float, longitude: float, radius_km: float = 50
    ) -> List[MechanicProfile]:
        """
        Search for mechanics within a radius using PostGIS.

        Args:
            db: Database session
            latitude: Customer's latitude
            longitude: Customer's longitude
            radius_km: Search radius in kilometers (default: 50km)

        Returns:
            List of mechanic profiles within the radius
        """
        # Create a point from the customer's location
        customer_point = ST_MakePoint(longitude, latitude)

        # Query mechanics within radius using ST_DWithin
        radius_meters = radius_km * 1000
        query = (
            db.query(MechanicProfile)
            .filter(
                text("ST_DWithin(location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :radius)")
            )
            .params(lon=longitude, lat=latitude, radius=radius_meters)
            .order_by(
                text("ST_DistanceSphere(location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))")
            )
            .params(lon=longitude, lat=latitude)
        )

        return query.all()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[MechanicProfile]:
        """Get all mechanic profiles with pagination."""
        return db.query(MechanicProfile).offset(skip).limit(limit).all()

    @staticmethod
    def get_verified(db: Session) -> List[MechanicProfile]:
        """Get all verified mechanics."""
        return db.query(MechanicProfile).filter(MechanicProfile.is_verified == True).all()


class ServiceRepository:
    """Repository for Service catalog operations."""

    @staticmethod
    def get_by_id(db: Session, service_id: str) -> Optional[Service]:
        """Get a service by ID."""
        return db.query(Service).filter(Service.id == service_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Service]:
        """Get a service by name."""
        return db.query(Service).filter(Service.name == name).first()

    @staticmethod
    def get_all(db: Session, category: Optional[str] = None) -> List[Service]:
        """Get all services, optionally filtered by category."""
        query = db.query(Service)
        if category:
            query = query.filter(Service.category == category)
        return query.all()

    @staticmethod
    def create(db: Session, service: Service) -> Service:
        """Create a new service."""
        db.add(service)
        db.commit()
        db.refresh(service)
        return service

    @staticmethod
    def update(db: Session, service: Service) -> Service:
        """Update an existing service."""
        db.commit()
        db.refresh(service)
        return service

    @staticmethod
    def delete(db: Session, service: Service) -> None:
        """Delete a service."""
        db.delete(service)
        db.commit()


class MechanicServiceRepository:
    """Repository for MechanicService relationship operations."""

    @staticmethod
    def get_by_id(db: Session, ms_id: str) -> Optional[MechanicService]:
        """Get a mechanic service by ID."""
        return db.query(MechanicService).filter(MechanicService.id == ms_id).first()

    @staticmethod
    def get_by_mechanic(db: Session, mechanic_id: str) -> List[MechanicService]:
        """Get all services for a mechanic."""
        return (
            db.query(MechanicService)
            .filter(MechanicService.mechanic_id == mechanic_id)
            .all()
        )

    @staticmethod
    def get_by_mechanic_with_details(db: Session, mechanic_id: str) -> List[MechanicService]:
        """Get all services for a mechanic with service details."""
        return (
            db.query(MechanicService)
            .join(Service, MechanicService.service_id == Service.id)
            .filter(MechanicService.mechanic_id == mechanic_id)
            .all()
        )

    @staticmethod
    def create(db: Session, mechanic_service: MechanicService) -> MechanicService:
        """Create a new mechanic service."""
        db.add(mechanic_service)
        db.commit()
        db.refresh(mechanic_service)
        return mechanic_service

    @staticmethod
    def update(db: Session, mechanic_service: MechanicService) -> MechanicService:
        """Update an existing mechanic service."""
        db.commit()
        db.refresh(mechanic_service)
        return mechanic_service

    @staticmethod
    def delete(db: Session, mechanic_service: MechanicService) -> None:
        """Delete a mechanic service."""
        db.delete(mechanic_service)
        db.commit()

    @staticmethod
    def check_exists(db: Session, mechanic_id: str, service_id: str) -> bool:
        """Check if a mechanic already offers a service."""
        return (
            db.query(MechanicService)
            .filter(
                MechanicService.mechanic_id == mechanic_id,
                MechanicService.service_id == service_id,
            )
            .first()
            is not None
        )

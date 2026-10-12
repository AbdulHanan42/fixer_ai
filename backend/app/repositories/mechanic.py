import re
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text

from app.db.models import MechanicProfile, Service, MechanicService


def _issue_search_words(issue: str | None) -> list[str]:
    stop_words = {"about", "after", "been", "from", "have", "into", "that", "there", "this", "when", "with", "your", "car", "the", "and", "for"}
    words = re.findall(r"[a-z0-9]+", (issue or "").lower())
    return list(dict.fromkeys(word for word in words if len(word) >= 3 and word not in stop_words))[:12]


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
        db: Session, latitude: float, longitude: float, radius_km: float = 50,
        issue: str | None = None,
    ) -> List[tuple[MechanicProfile, bool]]:
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
        # location is a PostGIS geography column, so cast the customer point
        # to geography before distance operations (and keep distances in meters).
        radius_meters = radius_km * 1000
        point = "CAST(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS geography)"
        distance = text(f"ST_Distance(location, {point})")
        query = (
            db.query(MechanicProfile)
            .filter(text(f"ST_DWithin(location, {point}, :radius)"))
            .params(lon=longitude, lat=latitude, radius=radius_meters)
        )

        words = _issue_search_words(issue)
        if words:
            service_match = or_(
                *[
                    column.ilike(f"%{word}%")
                    for word in words
                    for column in (Service.name, Service.category)
                ]
            )
            has_matching_service = (
                db.query(MechanicService.id)
                .join(Service, MechanicService.service_id == Service.id)
                .filter(MechanicService.mechanic_id == MechanicProfile.id)
                .filter(service_match)
                .exists()
            )
            available = (MechanicProfile.is_online.is_(True) & MechanicProfile.is_verified.is_(True))
            rows = query.add_columns(has_matching_service.label("issue_match")).order_by(
                available.desc(), has_matching_service.desc(), MechanicProfile.is_online.desc(),
                MechanicProfile.is_verified.desc(), distance
            ).all()
            return [(profile, bool(issue_match)) for profile, issue_match in rows]

        return [
            (profile, False)
            for profile in query.order_by(
                (MechanicProfile.is_online.is_(True) & MechanicProfile.is_verified.is_(True)).desc(),
                MechanicProfile.is_online.desc(), MechanicProfile.is_verified.desc(), distance
            ).all()
        ]

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[MechanicProfile]:
        """Get all mechanic profiles with pagination."""
        return db.query(MechanicProfile).offset(skip).limit(limit).all()

    @staticmethod
    def search_directory(
        db: Session, city: str | None = None, skip: int = 0, limit: int = 50,
        issue: str | None = None,
    ) -> List[tuple[MechanicProfile, bool]]:
        """Return verified shop profiles filtered by city and prioritized by issue."""
        query = db.query(MechanicProfile)
        if city and city.strip():
            query = query.filter(MechanicProfile.city.ilike(f"%{city.strip()}%"))
        words = _issue_search_words(issue)
        if words:
            service_match = or_(
                *[
                    column.ilike(f"%{word}%")
                    for word in words
                    for column in (Service.name, Service.category)
                ]
            )
            has_matching_service = (
                db.query(MechanicService.id)
                .join(Service, MechanicService.service_id == Service.id)
                .filter(MechanicService.mechanic_id == MechanicProfile.id)
                .filter(service_match)
                .exists()
            )
            available = (MechanicProfile.is_online.is_(True) & MechanicProfile.is_verified.is_(True))
            rows = query.add_columns(has_matching_service.label("issue_match")).order_by(
                available.desc(), has_matching_service.desc(),
                MechanicProfile.is_verified.desc(),
                MechanicProfile.is_online.desc(),
                MechanicProfile.average_rating.desc(),
                MechanicProfile.shop_name.asc(),
            ).offset(skip).limit(limit).all()
            return [(profile, bool(issue_match)) for profile, issue_match in rows]

        rows = query.order_by(
            (MechanicProfile.is_online.is_(True) & MechanicProfile.is_verified.is_(True)).desc(),
            MechanicProfile.is_verified.desc(), MechanicProfile.is_online.desc(),
            MechanicProfile.average_rating.desc(), MechanicProfile.shop_name.asc()
        ).offset(skip).limit(limit).all()
        return [(profile, False) for profile in rows]

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

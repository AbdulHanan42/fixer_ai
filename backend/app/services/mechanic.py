from typing import List, Optional
from geoalchemy2 import Geometry
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
from sqlalchemy import cast, func

from app.db.models import MechanicProfile, Service, MechanicService
from app.repositories.mechanic import (
    MechanicRepository,
    ServiceRepository,
    MechanicServiceRepository,
)
from app.schemas.mechanic import (
    MechanicProfileCreate,
    MechanicProfileUpdate,
    MechanicProfileResponse,
    MechanicProfileWithServices,
)
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    MechanicServiceCreate,
    MechanicServiceUpdate,
    MechanicServiceResponse,
)


class MechanicProfileService:
    """Service for mechanic profile business logic."""

    @staticmethod
    def create_profile(
        db: Session, user_id: str, profile_data: MechanicProfileCreate
    ) -> MechanicProfileResponse:
        """Create a new mechanic profile."""
        # Check if profile already exists
        existing = MechanicRepository.get_by_user_id(db, user_id)
        if existing:
            raise ValueError("Mechanic profile already exists")

        # Create location point from lat/lon
        location = WKTElement(
            f"POINT({profile_data.longitude} {profile_data.latitude})",
            srid=4326,
        )

        profile = MechanicProfile(
            user_id=user_id,
            shop_name=profile_data.shop_name,
            address=profile_data.address,
            city=profile_data.city.strip(),
            location=location,
            is_verified=False,
            average_rating=0.0,
        )

        created_profile = MechanicRepository.create(db, profile)
        return MechanicProfileService._to_response(db, created_profile)

    @staticmethod
    def get_profile(db: Session, user_id: str) -> MechanicProfileResponse:
        """Get mechanic profile by user ID."""
        profile = MechanicRepository.get_by_user_id(db, user_id)
        if not profile:
            raise ValueError("Mechanic profile not found")
        return MechanicProfileService._to_response(db, profile)

    @staticmethod
    def update_profile(
        db: Session, user_id: str, profile_data: MechanicProfileUpdate
    ) -> MechanicProfileResponse:
        """Update mechanic profile."""
        if (profile_data.latitude is None) != (profile_data.longitude is None):
            raise ValueError("Latitude and longitude must be provided together")
        profile = MechanicRepository.get_by_user_id(db, user_id)
        if not profile:
            raise ValueError("Mechanic profile not found")

        # Update fields if provided
        if profile_data.shop_name is not None:
            profile.shop_name = profile_data.shop_name
        if profile_data.address is not None:
            profile.address = profile_data.address
        if profile_data.city is not None:
            profile.city = profile_data.city.strip()
        if profile_data.is_online is not None:
            profile.is_online = profile_data.is_online
        if profile_data.latitude is not None and profile_data.longitude is not None:
            profile.location = WKTElement(
                f"POINT({profile_data.longitude} {profile_data.latitude})",
                srid=4326,
            )

        updated_profile = MechanicRepository.update(db, profile)
        return MechanicProfileService._to_response(db, updated_profile)

    @staticmethod
    def search_nearby(
        db: Session, latitude: float, longitude: float, radius_km: float = 50,
        issue: str | None = None,
    ) -> List[MechanicProfileResponse]:
        """Search for nearby mechanics."""
        matches = MechanicRepository.search_nearby(db, latitude, longitude, radius_km, issue)
        return [
            MechanicProfileService._to_response(db, profile).model_copy(update={"issue_match": issue_match})
            for profile, issue_match in matches
        ]

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[MechanicProfileResponse]:
        """Get all mechanic profiles."""
        profiles = MechanicRepository.get_all(db, skip, limit)
        return [MechanicProfileService._to_response(db, p) for p in profiles]

    @staticmethod
    def search_directory(
        db: Session, city: str | None = None, skip: int = 0, limit: int = 50,
        issue: str | None = None,
    ) -> List[MechanicProfileResponse]:
        matches = MechanicRepository.search_directory(db, city, skip, limit, issue)
        return [
            MechanicProfileService._to_response(db, profile).model_copy(update={"issue_match": issue_match})
            for profile, issue_match in matches
        ]

    @staticmethod
    def _to_response(db: Session, profile: MechanicProfile) -> MechanicProfileResponse:
        """Convert MechanicProfile model to response schema."""
        # Geography columns need a geometry cast before ST_X/ST_Y can read them.
        latitude = None
        longitude = None
        if profile.location:
            try:
                point = cast(MechanicProfile.location, Geometry(srid=4326))
                result = db.query(
                    func.ST_Y(point).label("lat"),
                    func.ST_X(point).label("lon"),
                ).filter(MechanicProfile.id == profile.id).first()
                if result and result.lat is not None and result.lon is not None:
                    latitude = float(result.lat)
                    longitude = float(result.lon)
            except Exception:
                # If location parsing fails, return None for coordinates
                pass

        return MechanicProfileResponse(
            id=str(profile.id),
            user_id=str(profile.user_id),
            shop_name=profile.shop_name,
            workshop_image_url=profile.workshop_image_url,
            address=profile.address,
            city=profile.city,
            latitude=latitude,
            longitude=longitude,
            is_verified=profile.is_verified,
            is_online=profile.is_online,
            average_rating=profile.average_rating,
        )


class ServiceCatalogService:
    """Service for service catalog business logic (admin only)."""

    @staticmethod
    def create_service(db: Session, service_data: ServiceCreate) -> ServiceResponse:
        """Create a new service."""
        # Check if service name already exists
        existing = ServiceRepository.get_by_name(db, service_data.name)
        if existing:
            raise ValueError("Service name already exists")

        service = Service(name=service_data.name, category=service_data.category)
        created_service = ServiceRepository.create(db, service)
        return ServiceCatalogService._to_response(created_service)

    @staticmethod
    def get_all_services(db: Session, category: Optional[str] = None) -> List[ServiceResponse]:
        """Get all services, optionally filtered by category."""
        services = ServiceRepository.get_all(db, category)
        return [ServiceCatalogService._to_response(s) for s in services]

    @staticmethod
    def get_service(db: Session, service_id: str) -> ServiceResponse:
        """Get a service by ID."""
        service = ServiceRepository.get_by_id(db, service_id)
        if not service:
            raise ValueError("Service not found")
        return ServiceCatalogService._to_response(service)

    @staticmethod
    def update_service(
        db: Session, service_id: str, service_data: ServiceUpdate
    ) -> ServiceResponse:
        """Update a service."""
        service = ServiceRepository.get_by_id(db, service_id)
        if not service:
            raise ValueError("Service not found")

        if service_data.name is not None:
            service.name = service_data.name
        if service_data.category is not None:
            service.category = service_data.category

        updated_service = ServiceRepository.update(db, service)
        return ServiceCatalogService._to_response(updated_service)

    @staticmethod
    def delete_service(db: Session, service_id: str) -> None:
        """Delete a service."""
        service = ServiceRepository.get_by_id(db, service_id)
        if not service:
            raise ValueError("Service not found")
        ServiceRepository.delete(db, service)

    @staticmethod
    def _to_response(service: Service) -> ServiceResponse:
        """Convert Service model to response schema."""
        return ServiceResponse(
            id=str(service.id), name=service.name, category=service.category
        )


class MechanicServiceService:
    """Service for mechanic-service relationship business logic."""

    @staticmethod
    def add_service(
        db: Session, mechanic_id: str, service_data: MechanicServiceCreate
    ) -> MechanicServiceResponse:
        """Add a service to a mechanic's profile."""
        # Check if service exists
        service = ServiceRepository.get_by_id(db, service_data.service_id)
        if not service:
            raise ValueError("Service not found")

        # Check if mechanic already has this service
        if MechanicServiceRepository.check_exists(
            db, mechanic_id, service_data.service_id
        ):
            raise ValueError("Mechanic already offers this service")

        mechanic_service = MechanicService(
            mechanic_id=mechanic_id,
            service_id=service_data.service_id,
            base_price=service_data.base_price,
        )

        created_ms = MechanicServiceRepository.create(db, mechanic_service)
        return MechanicServiceService._to_response(created_ms, service)

    @staticmethod
    def get_mechanic_services(db: Session, mechanic_id: str) -> List[MechanicServiceResponse]:
        """Get all services for a mechanic."""
        mechanic_services = MechanicServiceRepository.get_by_mechanic_with_details(
            db, mechanic_id
        )
        return [
            MechanicServiceService._to_response(ms, ms.service)
            for ms in mechanic_services
        ]

    @staticmethod
    def update_service_price(
        db: Session, ms_id: str, mechanic_id: str, price_data: MechanicServiceUpdate
    ) -> MechanicServiceResponse:
        """Update a mechanic's service price."""
        mechanic_service = MechanicServiceRepository.get_by_id(db, ms_id)
        if not mechanic_service:
            raise ValueError("Mechanic service not found")
        if mechanic_service.mechanic_id != mechanic_id:
            raise ValueError("Access denied")

        mechanic_service.base_price = price_data.base_price
        updated_ms = MechanicServiceRepository.update(db, mechanic_service)
        return MechanicServiceService._to_response(updated_ms, updated_ms.service)

    @staticmethod
    def remove_service(db: Session, ms_id: str, mechanic_id: str) -> None:
        """Remove a service from a mechanic's profile."""
        mechanic_service = MechanicServiceRepository.get_by_id(db, ms_id)
        if not mechanic_service:
            raise ValueError("Mechanic service not found")
        if mechanic_service.mechanic_id != mechanic_id:
            raise ValueError("Access denied")
        MechanicServiceRepository.delete(db, mechanic_service)

    @staticmethod
    def _to_response(
        mechanic_service: MechanicService, service: Optional[Service] = None
    ) -> MechanicServiceResponse:
        """Convert MechanicService model to response schema."""
        return MechanicServiceResponse(
            id=str(mechanic_service.id),
            mechanic_id=str(mechanic_service.mechanic_id),
            service_id=str(mechanic_service.service_id),
            base_price=mechanic_service.base_price,
            service_name=service.name if service else None,
            service_category=service.category if service else None,
        )

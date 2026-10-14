from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from pathlib import Path
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.dependencies.auth import get_current_user, get_current_mechanic, get_current_admin
from app.schemas.mechanic import (
    MechanicProfileCreate,
    MechanicProfileUpdate,
    MechanicProfileResponse,
    MechanicPublicProfileResponse,
)
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    MechanicServiceCreate,
    MechanicServiceUpdate,
    MechanicServiceResponse,
    CustomMechanicServiceCreate,
)
from app.services.mechanic import (
    MechanicProfileService,
    ServiceCatalogService,
    MechanicServiceService,
)
from app.repositories.mechanic import MechanicRepository

router = APIRouter(prefix="/mechanics", tags=["Mechanics"])
WORKSHOP_UPLOAD_DIR = Path(__file__).resolve().parents[3] / "storage" / "workshops"
WORKSHOP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
WORKSHOP_IMAGE_TYPES = {
    "image/jpeg": ("jpg", lambda data: data.startswith(b"\xff\xd8\xff")),
    "image/png": ("png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": ("webp", lambda data: data[:4] == b"RIFF" and data[8:12] == b"WEBP"),
}
MAX_WORKSHOP_IMAGE_SIZE = 8 * 1024 * 1024


# Mechanic Profile Endpoints (for mechanics)
@router.post("/profile", response_model=MechanicProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_mechanic_profile(
    profile_data: MechanicProfileCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_mechanic)],
):
    """
    Create a mechanic profile.

    - **shop_name**: Name of the mechanic shop
    - **address**: Physical address of the shop
    - **latitude**: Shop location latitude
    - **longitude**: Shop location longitude
    """
    try:
        return MechanicProfileService.create_profile(db, str(current_user.id), profile_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/profile", response_model=MechanicProfileResponse)
async def get_mechanic_profile(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_mechanic)],
):
    """Get the current mechanic's profile."""
    try:
        return MechanicProfileService.get_profile(db, str(current_user.id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/profile", response_model=MechanicProfileResponse)
async def update_mechanic_profile(
    profile_data: MechanicProfileUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_mechanic)],
):
    """Update the current mechanic's profile."""
    try:
        return MechanicProfileService.update_profile(db, str(current_user.id), profile_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/profile/workshop-image", response_model=MechanicProfileResponse)
async def upload_workshop_image(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_mechanic)],
    image: UploadFile = File(...),
):
    """Save a mechanic's workshop photo for their public profile."""
    profile = MechanicRepository.get_by_user_id(db, str(current_user.id))
    if not profile:
        raise HTTPException(status_code=404, detail="Create your shop profile before uploading a photo.")

    image_type = WORKSHOP_IMAGE_TYPES.get(image.content_type or "")
    if not image_type:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image.")

    data = await image.read(MAX_WORKSHOP_IMAGE_SIZE + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(data) > MAX_WORKSHOP_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Workshop photos must be 8 MB or smaller.")
    extension, valid_signature = image_type
    if not valid_signature(data):
        raise HTTPException(status_code=400, detail="The image content does not match its file type.")

    filename = f"{uuid4().hex}.{extension}"
    image_path = WORKSHOP_UPLOAD_DIR / filename
    image_path.write_bytes(data)
    previous_url = profile.workshop_image_url
    profile.workshop_image_url = f"/uploads/workshops/{filename}"
    try:
        updated_profile = MechanicRepository.update(db, profile)
    except Exception:
        image_path.unlink(missing_ok=True)
        db.rollback()
        raise

    if previous_url and previous_url.startswith("/uploads/workshops/"):
        previous_path = WORKSHOP_UPLOAD_DIR / Path(previous_url).name
        if previous_path != image_path:
            previous_path.unlink(missing_ok=True)
    return MechanicProfileService._to_response(db, updated_profile)


# Nearby Mechanic Search (for customers)
@router.get("/search", response_model=List[MechanicProfileResponse])
async def search_nearby_mechanics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    latitude: float = Query(..., ge=-90, le=90, description="Customer's latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Customer's longitude"),
    radius_km: float = Query(50, ge=1, le=200, description="Search radius in kilometers"),
    issue: Optional[str] = Query(None, max_length=2000, description="Repair issue used to prioritize matching mechanic services"),
):
    """
    Search for nearby mechanics using PostGIS.

    - **latitude**: Customer's current latitude
    - **longitude**: Customer's current longitude
    - **radius_km**: Search radius in kilometers (default: 50km, max: 200km)
    """
    return MechanicProfileService.search_nearby(db, latitude, longitude, radius_km, issue)


@router.get("/directory", response_model=List[MechanicProfileResponse])
async def search_mechanic_directory(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    city: Optional[str] = Query(None, min_length=2, max_length=100),
    issue: Optional[str] = Query(None, max_length=2000),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Browse verified mechanic shops by city, without requiring device GPS."""
    return MechanicProfileService.search_directory(db, city, skip, limit, issue)


@router.get("/directory/{mechanic_id}/profile", response_model=MechanicPublicProfileResponse)
async def get_public_mechanic_profile(
    mechanic_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Return customer-safe shop details and the services this mechanic offers."""
    profile = MechanicRepository.get_by_id(db, str(mechanic_id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mechanic profile not found.",
        )

    return MechanicPublicProfileResponse(
        id=str(profile.id),
        shop_name=profile.shop_name,
        workshop_image_url=profile.workshop_image_url,
        address=profile.address,
        city=profile.city,
        is_verified=profile.is_verified,
        is_online=profile.is_online,
        average_rating=profile.average_rating,
        services=MechanicServiceService.get_mechanic_services(db, str(profile.id)),
    )


@router.get("", response_model=List[MechanicProfileResponse])
async def get_all_mechanics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of records to return"),
):
    """Get all mechanic profiles with pagination."""
    return MechanicProfileService.get_all(db, skip, limit)


# Mechanic Services Endpoints (for mechanics)
@router.post("/services/custom", response_model=MechanicServiceResponse, status_code=status.HTTP_201_CREATED)
async def add_custom_mechanic_service(
    service_data: CustomMechanicServiceCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_mechanic)],
):
    """Create a service visible only on this mechanic's profile."""
    profile = MechanicRepository.get_by_user_id(db, str(current_user.id))
    if not profile:
        raise HTTPException(status_code=404, detail="Mechanic profile not found")
    try:
        return MechanicServiceService.add_custom_service(db, str(profile.id), service_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/services", response_model=MechanicServiceResponse, status_code=status.HTTP_201_CREATED)
async def add_mechanic_service(
    service_data: MechanicServiceCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_mechanic)],
):
    """
    Add a service to the mechanic's profile.

    - **service_id**: ID of the service from the catalog
    - **base_price**: Base price for this service
    """
    # Get mechanic profile
    from app.repositories.mechanic import MechanicRepository
    profile = MechanicRepository.get_by_user_id(db, str(current_user.id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mechanic profile not found",
        )

    try:
        return MechanicServiceService.add_service(db, str(profile.id), service_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/services", response_model=List[MechanicServiceResponse])
async def get_mechanic_services(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_mechanic)],
):
    """Get all services offered by the current mechanic."""
    from app.repositories.mechanic import MechanicRepository
    profile = MechanicRepository.get_by_user_id(db, str(current_user.id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mechanic profile not found",
        )

    return MechanicServiceService.get_mechanic_services(db, str(profile.id))


@router.put("/services/{service_id}", response_model=MechanicServiceResponse)
async def update_mechanic_service_price(
    service_id: str,
    price_data: MechanicServiceUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_mechanic)],
):
    """Update the price of a service offered by the mechanic."""
    from app.repositories.mechanic import MechanicRepository
    profile = MechanicRepository.get_by_user_id(db, str(current_user.id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mechanic profile not found",
        )

    try:
        return MechanicServiceService.update_service_price(
            db, service_id, str(profile.id), price_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_mechanic_service(
    service_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_mechanic)],
):
    """Remove a service from the mechanic's profile."""
    from app.repositories.mechanic import MechanicRepository
    profile = MechanicRepository.get_by_user_id(db, str(current_user.id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mechanic profile not found",
        )

    try:
        MechanicServiceService.remove_service(db, service_id, str(profile.id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


# Service Catalog Endpoints (for admins)
@router.post("/catalog", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    Create a new service in the catalog (admin only).

    - **name**: Service name
    - **category**: Service category
    """
    try:
        return ServiceCatalogService.create_service(db, service_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/catalog", response_model=List[ServiceResponse])
async def get_service_catalog(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """Get all services in the catalog, optionally filtered by category."""
    return ServiceCatalogService.get_all_services(db, category)


@router.get("/catalog/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a specific service from the catalog."""
    try:
        return ServiceCatalogService.get_service(db, service_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/catalog/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    service_data: ServiceUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """Update a service in the catalog (admin only)."""
    try:
        return ServiceCatalogService.update_service(db, service_id, service_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/catalog/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """Delete a service from the catalog (admin only)."""
    try:
        ServiceCatalogService.delete_service(db, service_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

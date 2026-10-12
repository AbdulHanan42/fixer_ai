import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session, joinedload
from geoalchemy2 import Geometry

from app.db.models import MechanicProfile, User
from app.db.session import get_db
from app.dependencies.auth import get_current_admin_user
from app.schemas.admin import PendingMechanicResponse, VerifyMechanicResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get(
    "/mechanics/pending",
    response_model=list[PendingMechanicResponse],
)
async def list_pending_mechanics(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    """
    Get a list of all mechanics pending administrative verification.
    Strictly restricted to users with the 'admin' role.
    """
    stmt = (
        select(MechanicProfile)
        .options(joinedload(MechanicProfile.user))
        .where(MechanicProfile.is_verified.is_(False))
        .order_by(MechanicProfile.shop_name.asc())
    )
    pending_profiles = db.execute(stmt).scalars().all()

    response_items = []
    for profile in pending_profiles:
        # Extract lat/lon from location geography if available
        latitude: float | None = None
        longitude: float | None = None

        if profile.location is not None:
            try:
                coords = db.execute(
                    select(
                        func.ST_Y(cast(MechanicProfile.location, Geometry(srid=4326))).label("lat"),
                        func.ST_X(cast(MechanicProfile.location, Geometry(srid=4326))).label("lon"),
                    ).where(MechanicProfile.id == profile.id)
                ).first()
                if coords:
                    latitude = float(coords.lat) if coords.lat is not None else None
                    longitude = float(coords.lon) if coords.lon is not None else None
            except Exception as e:
                logger.debug("Could not parse coordinates for profile %s: %s", profile.id, e)

        user = profile.user
        response_items.append(
            PendingMechanicResponse(
                id=str(profile.id),
                user_id=str(profile.user_id),
                shop_name=profile.shop_name,
                address=profile.address,
                city=profile.city,
                is_verified=profile.is_verified,
                average_rating=profile.average_rating,
                mechanic_name=user.full_name if user else None,
                mechanic_email=user.email if user else None,
                mechanic_phone=user.phone_number if user else None,
                latitude=latitude,
                longitude=longitude,
            )
        )

    return response_items


@router.patch(
    "/mechanics/{mechanic_id}/verify",
    response_model=VerifyMechanicResponse,
)
async def verify_mechanic(
    mechanic_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    """
    Verify a mechanic profile so they appear in nearby customer searches.
    Strictly restricted to users with the 'admin' role.
    """
    stmt = select(MechanicProfile).where(MechanicProfile.id == mechanic_id)
    profile = db.execute(stmt).scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mechanic profile with ID '{mechanic_id}' not found.",
        )

    profile.is_verified = True
    db.commit()
    db.refresh(profile)

    return VerifyMechanicResponse(
        mechanic_id=str(profile.id),
        shop_name=profile.shop_name,
        is_verified=True,
        message=f"Mechanic '{profile.shop_name}' has been successfully verified.",
    )

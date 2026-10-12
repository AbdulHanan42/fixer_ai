from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import MechanicProfile, RepairRequest, RequestStatus, Review, User
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/request/{request_id}/status")
async def get_request_review_status(
    request_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Return whether the current customer has reviewed a completed request."""
    repair_request = db.execute(
        select(RepairRequest).where(RepairRequest.id == request_id)
    ).scalar_one_or_none()
    if not repair_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair request not found.")
    if str(repair_request.customer_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    existing = db.execute(select(Review.id).where(Review.request_id == repair_request.id)).scalar_one_or_none()
    return {"reviewed": existing is not None}


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_review(
    review_data: ReviewCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Submit a review and 1-5 star rating for a completed repair request.

    - **request_id**: ID of the completed repair request
    - **rating**: Rating between 1 and 5 stars
    - **comment**: Text feedback regarding the service
    """
    # 1. Fetch repair request
    stmt_req = select(RepairRequest).where(RepairRequest.id == review_data.request_id)
    repair_request = db.execute(stmt_req).scalar_one_or_none()

    if not repair_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repair request not found.",
        )

    # 2. Ownership verification: must be the customer of this repair request
    if str(repair_request.customer_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only review your own repair requests.",
        )

    # 3. Status verification: must be completed
    if repair_request.status != RequestStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only completed repair requests can be reviewed.",
        )

    # 4. Must have an assigned mechanic
    if not repair_request.mechanic_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot review a repair request without an assigned mechanic.",
        )

    # 5. Check if review already exists for this request
    stmt_existing = select(Review).where(Review.request_id == repair_request.id)
    existing_review = db.execute(stmt_existing).scalar_one_or_none()
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A review has already been submitted for this repair request.",
        )

    # 6. Save review
    new_review = Review(
        request_id=repair_request.id,
        customer_id=current_user.id,
        mechanic_id=repair_request.mechanic_id,
        rating=review_data.rating,
        comment=review_data.comment.strip(),
    )
    db.add(new_review)
    db.flush()

    # 7. Crucial: Calculate new average rating for mechanic and update MechanicProfile
    stmt_avg = select(func.avg(Review.rating)).where(
        Review.mechanic_id == repair_request.mechanic_id
    )
    avg_rating = db.execute(stmt_avg).scalar()
    new_avg_float = round(float(avg_rating), 2) if avg_rating is not None else float(review_data.rating)

    stmt_mech = select(MechanicProfile).where(
        MechanicProfile.id == repair_request.mechanic_id
    )
    mechanic_profile = db.execute(stmt_mech).scalar_one_or_none()
    if mechanic_profile:
        mechanic_profile.average_rating = new_avg_float

    db.commit()
    db.refresh(new_review)

    return ReviewResponse(
        id=str(new_review.id),
        request_id=str(new_review.request_id),
        customer_id=str(new_review.customer_id),
        mechanic_id=str(new_review.mechanic_id),
        rating=new_review.rating,
        comment=new_review.comment,
        mechanic_average_rating=new_avg_float,
    )


@router.get("/mechanic/{mechanic_id}", response_model=ReviewListResponse)
async def get_mechanic_reviews(
    mechanic_id: str,
    db: Annotated[Session, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
):
    """
    Get all reviews and aggregate rating for a mechanic profile.
    """
    stmt_mech = select(MechanicProfile).where(MechanicProfile.id == mechanic_id)
    mechanic_profile = db.execute(stmt_mech).scalar_one_or_none()
    if not mechanic_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mechanic profile not found.",
        )

    stmt_reviews = (
        select(Review)
        .where(Review.mechanic_id == mechanic_id)
        .offset(skip)
        .limit(limit)
    )
    reviews = db.execute(stmt_reviews).scalars().all()

    stmt_count = select(func.count(Review.id)).where(Review.mechanic_id == mechanic_id)
    total = db.execute(stmt_count).scalar() or 0

    return ReviewListResponse(
        reviews=[
            ReviewResponse(
                id=str(r.id),
                request_id=str(r.request_id),
                customer_id=str(r.customer_id),
                mechanic_id=str(r.mechanic_id),
                rating=r.rating,
                comment=r.comment,
                mechanic_average_rating=mechanic_profile.average_rating,
            )
            for r in reviews
        ],
        total=total,
        average_rating=mechanic_profile.average_rating,
    )

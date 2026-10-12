import uuid
import pytest
from fastapi.testclient import TestClient
from geoalchemy2.elements import WKTElement

from app.main import app
from app.db.session import SessionLocal
from app.db.models import (
    User,
    UserRole,
    MechanicProfile,
    RepairRequest,
    RequestStatus,
    Message,
    Notification,
)
from app.core.security import get_password_hash, create_access_token


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def db():
    """Database session fixture that cleans up test records."""
    session = SessionLocal()
    created_user_ids = []

    yield session, created_user_ids

    # Cleanup created users (cascade deletes all child records)
    if created_user_ids:
        try:
            session.query(Notification).filter(Notification.user_id.in_(created_user_ids)).delete(synchronize_session=False)
            session.query(Message).filter(Message.sender_id.in_(created_user_ids)).delete(synchronize_session=False)
            session.query(RepairRequest).filter(RepairRequest.customer_id.in_(created_user_ids)).delete(synchronize_session=False)
            session.query(MechanicProfile).filter(MechanicProfile.user_id.in_(created_user_ids)).delete(synchronize_session=False)
            session.query(User).filter(User.id.in_(created_user_ids)).delete(synchronize_session=False)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
    else:
        session.close()


@pytest.fixture
def test_setup(db):
    """
    Creates:
    - customer user + token
    - mechanic user + profile + token
    - unauthorized user + token
    - accepted repair request linking customer and mechanic
    """
    session, created_user_ids = db
    unique_suffix = uuid.uuid4().hex[:8]

    # 1. Customer
    customer = User(
        email=f"cust_{unique_suffix}@example.com",
        phone_number=f"+1000{unique_suffix[:6]}",
        full_name="Test Customer",
        password_hash=get_password_hash("password123"),
        role=UserRole.customer,
    )
    session.add(customer)
    session.flush()
    created_user_ids.append(customer.id)

    # 2. Mechanic
    mechanic_user = User(
        email=f"mech_{unique_suffix}@example.com",
        phone_number=f"+1999{unique_suffix[:6]}",
        full_name="Test Mechanic",
        password_hash=get_password_hash("password123"),
        role=UserRole.mechanic,
    )
    session.add(mechanic_user)
    session.flush()
    created_user_ids.append(mechanic_user.id)

    mechanic_profile = MechanicProfile(
        user_id=mechanic_user.id,
        shop_name="Fixer Auto Care",
        address="123 Motor Street",
        location=WKTElement("POINT(74.3587 31.5204)", srid=4326),
        is_verified=True,
        average_rating=4.8,
    )
    session.add(mechanic_profile)
    session.flush()

    # 3. Unauthorized Customer (Third party)
    unauthorized_user = User(
        email=f"unauth_{unique_suffix}@example.com",
        phone_number=f"+1888{unique_suffix[:6]}",
        full_name="Third Party User",
        password_hash=get_password_hash("password123"),
        role=UserRole.customer,
    )
    session.add(unauthorized_user)
    session.flush()
    created_user_ids.append(unauthorized_user.id)

    # 4. Repair Request (assigned to mechanic)
    repair_req = RepairRequest(
        customer_id=customer.id,
        mechanic_id=mechanic_profile.id,
        description="Engine check required. Strange noise from radiator.",
        customer_location=WKTElement("POINT(74.3587 31.5204)", srid=4326),
        status=RequestStatus.accepted,
    )
    session.add(repair_req)
    session.commit()
    session.refresh(repair_req)

    # 5. Pending Repair Request (no mechanic assigned)
    pending_req = RepairRequest(
        customer_id=customer.id,
        mechanic_id=None,
        description="Pending request with no mechanic yet.",
        customer_location=WKTElement("POINT(74.3587 31.5204)", srid=4326),
        status=RequestStatus.pending,
    )
    session.add(pending_req)
    session.commit()
    session.refresh(pending_req)

    # Tokens
    cust_token = create_access_token({"sub": str(customer.id), "role": "customer"})
    mech_token = create_access_token({"sub": str(mechanic_user.id), "role": "mechanic"})
    unauth_token = create_access_token({"sub": str(unauthorized_user.id), "role": "customer"})

    return {
        "customer": customer,
        "customer_token": cust_token,
        "mechanic_user": mechanic_user,
        "mechanic_profile": mechanic_profile,
        "mechanic_token": mech_token,
        "unauthorized_user": unauthorized_user,
        "unauthorized_token": unauth_token,
        "repair_request": repair_req,
        "pending_request": pending_req,
    }

import uuid
import pytest
from geoalchemy2.elements import WKTElement

from app.core.security import create_access_token, get_password_hash
from app.db.models import (
    MechanicProfile,
    RepairRequest,
    RequestStatus,
    Review,
    User,
    UserRole,
)


@pytest.fixture
def review_admin_setup(db):
    """Fixture with customer, admin, verified mechanic, and pending mechanic."""
    session, created_user_ids = db
    unique_suffix = uuid.uuid4().hex[:8]

    # Admin user
    admin_user = User(
        email=f"admin_{unique_suffix}@fixer.ai",
        phone_number=f"+92310{unique_suffix[:6]}",
        full_name="Admin Chief",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.admin,
    )
    session.add(admin_user)
    session.flush()
    created_user_ids.append(admin_user.id)

    # Customer user
    cust_user = User(
        email=f"customer_{unique_suffix}@fixer.ai",
        phone_number=f"+92311{unique_suffix[:6]}",
        full_name="Customer Reviews",
        password_hash=get_password_hash("CustPass123!"),
        role=UserRole.customer,
    )
    session.add(cust_user)
    session.flush()
    created_user_ids.append(cust_user.id)

    # Second Customer user (unauthorized third party)
    cust2_user = User(
        email=f"intruder_{unique_suffix}@fixer.ai",
        phone_number=f"+92312{unique_suffix[:6]}",
        full_name="Intruder Customer",
        password_hash=get_password_hash("IntruderPass123!"),
        role=UserRole.customer,
    )
    session.add(cust2_user)
    session.flush()
    created_user_ids.append(cust2_user.id)

    # Mechanic user + profile (initially unverified)
    mech_user = User(
        email=f"mech_{unique_suffix}@fixer.ai",
        phone_number=f"+92313{unique_suffix[:6]}",
        full_name="Akram Mechanic",
        password_hash=get_password_hash("MechPass123!"),
        role=UserRole.mechanic,
    )
    session.add(mech_user)
    session.flush()
    created_user_ids.append(mech_user.id)

    mech_profile = MechanicProfile(
        user_id=mech_user.id,
        shop_name="Akram Auto Garage",
        address="Near Iqbal Stadium, Faisalabad",
        location=WKTElement("POINT(73.0791 31.4187)", srid=4326),
        is_verified=False,
        average_rating=0.0,
    )
    session.add(mech_profile)
    session.flush()

    # Completed Repair Request (ready to review)
    completed_req = RepairRequest(
        customer_id=cust_user.id,
        mechanic_id=mech_profile.id,
        description="Gearbox oil leaking and slight slipping in 2nd gear.",
        customer_location=WKTElement("POINT(73.0791 31.4187)", srid=4326),
        status=RequestStatus.completed,
    )
    session.add(completed_req)

    # In-progress / Accepted Repair Request (not completed)
    accepted_req = RepairRequest(
        customer_id=cust_user.id,
        mechanic_id=mech_profile.id,
        description="Brake pads replacement in progress.",
        customer_location=WKTElement("POINT(73.0791 31.4187)", srid=4326),
        status=RequestStatus.accepted,
    )
    session.add(accepted_req)

    session.commit()

    admin_token = create_access_token({"sub": str(admin_user.id), "role": "admin"})
    cust_token = create_access_token({"sub": str(cust_user.id), "role": "customer"})
    cust2_token = create_access_token({"sub": str(cust2_user.id), "role": "customer"})
    mech_token = create_access_token({"sub": str(mech_user.id), "role": "mechanic"})

    return {
        "admin_user": admin_user,
        "admin_token": admin_token,
        "customer": cust_user,
        "customer_token": cust_token,
        "customer2": cust2_user,
        "customer2_token": cust2_token,
        "mechanic_user": mech_user,
        "mechanic_profile": mech_profile,
        "mechanic_token": mech_token,
        "completed_request": completed_req,
        "accepted_request": accepted_req,
    }


def test_create_review_success_and_average_calculation(client, review_admin_setup, db):
    """Test successful review submission and mechanic average rating recalculation."""
    session, _ = db
    setup = review_admin_setup
    req_id = str(setup["completed_request"].id)
    cust_token = setup["customer_token"]
    mech_id = str(setup["mechanic_profile"].id)

    # Submit 5-star review
    resp = client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "request_id": req_id,
            "rating": 5,
            "comment": "Excellent repair! The gearbox works smoothly now.",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 5
    assert data["comment"] == "Excellent repair! The gearbox works smoothly now."
    assert data["mechanic_id"] == mech_id
    assert data["customer_id"] == str(setup["customer"].id)
    assert data["mechanic_average_rating"] == 5.0

    # Verify MechanicProfile average rating in DB is updated to 5.0
    session.expire_all()
    prof = session.query(MechanicProfile).filter(MechanicProfile.id == mech_id).first()
    assert prof.average_rating == 5.0

    # Also test get reviews for mechanic
    list_resp = client.get(f"/api/v1/reviews/mechanic/{mech_id}")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] == 1
    assert list_data["average_rating"] == 5.0


def test_review_validation_and_ownership(client, review_admin_setup):
    """Test ownership check, status check, and duplicate review prevention."""
    setup = review_admin_setup
    completed_id = str(setup["completed_request"].id)
    accepted_id = str(setup["accepted_request"].id)
    cust_token = setup["customer_token"]
    intruder_token = setup["customer2_token"]

    # 1. Intruder customer tries to review someone else's request -> 403 Forbidden
    resp_unauth = client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {intruder_token}"},
        json={"request_id": completed_id, "rating": 4, "comment": "Not my request"},
    )
    assert resp_unauth.status_code == 403
    assert "access denied" in resp_unauth.json()["detail"].lower()

    # 2. Customer tries to review an accepted (not yet completed) request -> 400 Bad Request
    resp_not_completed = client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"request_id": accepted_id, "rating": 5, "comment": "Job not done yet"},
    )
    assert resp_not_completed.status_code == 400
    assert "completed" in resp_not_completed.json()["detail"].lower()

    # 3. Non-existent request ID -> 404
    resp_404 = client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "request_id": "00000000-0000-0000-0000-000000000000",
            "rating": 5,
            "comment": "Does not exist",
        },
    )
    assert resp_404.status_code == 404

    # 4. Invalid rating range (< 1 or > 5) -> 422
    resp_invalid_rating = client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"request_id": completed_id, "rating": 6, "comment": "Too high"},
    )
    assert resp_invalid_rating.status_code == 422

    # 5. Empty comment -> 422
    resp_empty_comment = client.post(
        "/api/v1/reviews/",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"request_id": completed_id, "rating": 5, "comment": ""},
    )
    assert resp_empty_comment.status_code == 422


def test_admin_pending_mechanics_and_verification(client, review_admin_setup, db):
    """Test admin listing pending mechanics and verifying a mechanic."""
    session, _ = db
    setup = review_admin_setup
    admin_token = setup["admin_token"]
    cust_token = setup["customer_token"]
    mech_id = str(setup["mechanic_profile"].id)

    # 1. Non-admin user cannot view pending mechanics -> 403 Forbidden
    resp_forbidden = client.get(
        "/api/v1/admin/mechanics/pending",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert resp_forbidden.status_code == 403
    assert "admin" in resp_forbidden.json()["detail"].lower()

    # 2. Admin retrieves pending mechanics list
    resp_pending = client.get(
        "/api/v1/admin/mechanics/pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_pending.status_code == 200
    pending_list = resp_pending.json()
    assert isinstance(pending_list, list)
    pending_ids = [m["id"] for m in pending_list]
    assert mech_id in pending_ids

    # 3. Non-admin cannot verify a mechanic -> 403 Forbidden
    resp_verify_forbidden = client.patch(
        f"/api/v1/admin/mechanics/{mech_id}/verify",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert resp_verify_forbidden.status_code == 403

    # 4. Admin verifies the mechanic -> 200 OK
    resp_verify = client.patch(
        f"/api/v1/admin/mechanics/{mech_id}/verify",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_verify.status_code == 200
    verify_data = resp_verify.json()
    assert verify_data["mechanic_id"] == mech_id
    assert verify_data["is_verified"] is True
    assert "verified" in verify_data["message"].lower()

    # 5. Verify database state updated
    session.expire_all()
    updated_profile = session.query(MechanicProfile).filter(MechanicProfile.id == mech_id).first()
    assert updated_profile.is_verified is True

    # 6. Mechanic is no longer in pending list
    resp_pending_after = client.get(
        "/api/v1/admin/mechanics/pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_pending_after.status_code == 200
    remaining_pending = [m["id"] for m in resp_pending_after.json()]
    assert mech_id not in remaining_pending

    # 7. Non-existent mechanic ID verification -> 404
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp_404 = client.patch(
        f"/api/v1/admin/mechanics/{fake_id}/verify",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_404.status_code == 404

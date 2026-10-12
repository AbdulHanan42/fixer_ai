import sys
from pathlib import Path

# Add backend directory to sys.path to enable importing app modules
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.models import (
    MechanicProfile,
    MechanicService,
    Service,
    User,
    UserRole,
)
from app.db.session import SessionLocal


def seed_services(db: Session) -> dict[str, Service]:
    """Seed base service catalog into the database."""
    services_data = [
        {"name": "Auto Electrician", "category": "Electrical"},
        {"name": "General Mechanic", "category": "Engine & Mechanical"},
        {"name": "Tyre Puncture & Alignment", "category": "Tyres & Suspension"},
        {"name": "Brake Service & Repair", "category": "Brakes"},
        {"name": "AC & Climate Control", "category": "Climate Control"},
        {"name": "Oil Change & Routine Service", "category": "Maintenance"},
    ]

    services_by_name = {}
    for item in services_data:
        stmt = select(Service).where(Service.name == item["name"])
        existing = db.execute(stmt).scalar_one_or_none()
        if not existing:
            service = Service(name=item["name"], category=item["category"])
            db.add(service)
            db.flush()
            services_by_name[item["name"]] = service
            print(f"  [+] Created Service: {item['name']} ({item['category']})")
        else:
            services_by_name[item["name"]] = existing
            print(f"  [.] Existing Service: {item['name']}")

    db.commit()
    return services_by_name


def seed_users(db: Session) -> dict[str, User]:
    """Seed customer and admin test users."""
    users_data = [
        {
            "key": "customer",
            "email": "customer@fixer.ai",
            "phone_number": "+923001234567",
            "full_name": "Hassan Ali (Customer)",
            "password": "Password123!",
            "role": UserRole.customer,
        },
        {
            "key": "admin",
            "email": "admin@fixer.ai",
            "phone_number": "+923009999999",
            "full_name": "Admin Supervisor",
            "password": "AdminPassword123!",
            "role": UserRole.admin,
        },
    ]

    seeded_users = {}
    for u in users_data:
        stmt = select(User).where(User.email == u["email"])
        existing = db.execute(stmt).scalar_one_or_none()
        if not existing:
            new_user = User(
                email=u["email"],
                phone_number=u["phone_number"],
                full_name=u["full_name"],
                password_hash=get_password_hash(u["password"]),
                role=u["role"],
            )
            db.add(new_user)
            db.flush()
            seeded_users[u["key"]] = new_user
            print(f"  [+] Created User: {u['full_name']} <{u['email']}> ({u['role'].value})")
        else:
            seeded_users[u["key"]] = existing
            print(f"  [.] Existing User: {u['full_name']} <{u['email']}>")

    db.commit()
    return seeded_users


def seed_mechanics(db: Session, services_by_name: dict[str, Service]) -> None:
    """Seed mechanic users, shop profiles with PostGIS coordinates, and services."""
    mechanics_data = [
        {
            "email": "tariq.mechanic@fixer.ai",
            "phone_number": "+923002221111",
            "full_name": "Tariq Mehmood",
            "shop_name": "Lahore Auto Care & Diagnostics",
            "address": "Plot 45, Maulana Shaukat Ali Road, Faisal Town, Lahore",
            "lon": 74.3015,
            "lat": 31.4721,
            "is_verified": True,
            "average_rating": 4.7,
            "services": [
                ("Auto Electrician", 2500.0),
                ("General Mechanic", 3000.0),
                ("AC & Climate Control", 3500.0),
            ],
        },
        {
            "email": "asif.motors@fixer.ai",
            "phone_number": "+923003332222",
            "full_name": "Muhammad Asif",
            "shop_name": "Gulberg Precision Motors",
            "address": "Main Boulevard Gulberg III, Lahore",
            "lon": 74.3436,
            "lat": 31.5102,
            "is_verified": True,
            "average_rating": 4.9,
            "services": [
                ("Oil Change & Routine Service", 1500.0),
                ("Brake Service & Repair", 2000.0),
                ("Tyre Puncture & Alignment", 800.0),
            ],
        },
        {
            "email": "zahid.chichawatni@fixer.ai",
            "phone_number": "+923004443333",
            "full_name": "Zahid Iqbal",
            "shop_name": "Chichawatni Highway Auto Clinic",
            "address": "Old GT Road, Near General Bus Stand, Chichawatni",
            "lon": 72.7000,
            "lat": 30.5333,
            "is_verified": False,  # Pending admin verification
            "average_rating": 0.0,
            "services": [
                ("General Mechanic", 1800.0),
                ("Auto Electrician", 2000.0),
                ("Tyre Puncture & Alignment", 500.0),
            ],
        },
        {
            "email": "bilal.sahiwal@fixer.ai",
            "phone_number": "+923005554444",
            "full_name": "Bilal Siddiqui",
            "shop_name": "Sahiwal Master Workshop",
            "address": "Farid Town, High Street, Sahiwal",
            "lon": 73.1068,
            "lat": 30.6682,
            "is_verified": False,  # Pending admin verification
            "average_rating": 0.0,
            "services": [
                ("Brake Service & Repair", 1800.0),
                ("Oil Change & Routine Service", 1200.0),
            ],
        },
        {
            "email": "noman.johar@fixer.ai",
            "phone_number": "+923006665555",
            "full_name": "Noman Raza",
            "shop_name": "Johar Town Express Service",
            "address": "G1 Market, Johar Town, Lahore",
            "lon": 74.2792,
            "lat": 31.4697,
            "is_verified": True,
            "average_rating": 4.5,
            "services": [
                ("Auto Electrician", 2200.0),
                ("AC & Climate Control", 3000.0),
                ("Oil Change & Routine Service", 1400.0),
            ],
        },
    ]

    for item in mechanics_data:
        # 1. Create or get Mechanic User
        stmt_user = select(User).where(User.email == item["email"])
        mech_user = db.execute(stmt_user).scalar_one_or_none()
        if not mech_user:
            mech_user = User(
                email=item["email"],
                phone_number=item["phone_number"],
                full_name=item["full_name"],
                password_hash=get_password_hash("MechanicPass123!"),
                role=UserRole.mechanic,
            )
            db.add(mech_user)
            db.flush()
            print(f"  [+] Created Mechanic User: {item['full_name']} <{item['email']}>")
        else:
            print(f"  [.] Existing Mechanic User: {item['full_name']}")

        # 2. Create or get MechanicProfile
        stmt_prof = select(MechanicProfile).where(MechanicProfile.user_id == mech_user.id)
        profile = db.execute(stmt_prof).scalar_one_or_none()
        point_wkt = f"POINT({item['lon']} {item['lat']})"

        if not profile:
            profile = MechanicProfile(
                user_id=mech_user.id,
                shop_name=item["shop_name"],
                address=item["address"],
                location=WKTElement(point_wkt, srid=4326),
                is_verified=item["is_verified"],
                average_rating=item["average_rating"],
            )
            db.add(profile)
            db.flush()
            status_tag = "VERIFIED" if item["is_verified"] else "PENDING"
            print(f"      [+] Created Profile: '{item['shop_name']}' [{status_tag}] at {point_wkt}")
        else:
            print(f"      [.] Existing Profile: '{item['shop_name']}'")

        # 3. Assign Services & Base Prices
        for svc_name, base_price in item["services"]:
            service_obj = services_by_name.get(svc_name)
            if not service_obj:
                continue

            stmt_ms = select(MechanicService).where(
                MechanicService.mechanic_id == profile.id,
                MechanicService.service_id == service_obj.id,
            )
            existing_ms = db.execute(stmt_ms).scalar_one_or_none()
            if not existing_ms:
                ms = MechanicService(
                    mechanic_id=profile.id,
                    service_id=service_obj.id,
                    base_price=base_price,
                )
                db.add(ms)
                print(f"          [+] Attached Service: {svc_name} -> Rs. {base_price}")

    db.commit()


def main():
    """Execute the full database seeding process."""
    print("=" * 60)
    print("Fixer AI - Database Seeding Script")
    print("=" * 60)

    db: Session = SessionLocal()
    try:
        print("\nStep 1: Seeding Service Catalog...")
        services_by_name = seed_services(db)

        print("\nStep 2: Seeding Test Users (Customer & Admin)...")
        seed_users(db)

        print("\nStep 3: Seeding Mechanic Profiles with PostGIS Spatial Coordinates...")
        seed_mechanics(db, services_by_name)

        print("\n" + "=" * 60)
        print("Database seeding completed successfully!")
        print("=" * 60)
    except Exception as e:
        db.rollback()
        print(f"\n[!] Error during database seeding: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

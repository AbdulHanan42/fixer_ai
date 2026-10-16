"""Promote an existing customer account to admin.

Run from the backend directory with:
    python -m scripts.promote_admin customer@example.com
"""
import argparse

from app.db.models import UserRole
from app.db.session import SessionLocal
from app.repositories.user import UserRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Grant admin access to an existing account.")
    parser.add_argument("email", help="Email address of the account to promote")
    email = parser.parse_args().email.strip().lower()

    db = SessionLocal()
    try:
        user = UserRepository.get_by_email(db, email)
        if user is None:
            raise SystemExit(f"No account found for {email}. Register the account first.")
        if user.role == UserRole.mechanic:
            raise SystemExit("Mechanic accounts cannot be promoted; use a separate operator account.")
        if user.role == UserRole.admin:
            print(f"{email} already has admin access.")
            return

        user.role = UserRole.admin
        db.commit()
        print(f"Granted admin access to {email}. Sign in again to open /admin/dashboard.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

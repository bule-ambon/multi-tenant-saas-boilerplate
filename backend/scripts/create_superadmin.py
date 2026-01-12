#!/usr/bin/env python3
"""
Create or update the super admin user from environment settings.
"""
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.database import get_db
from app.core.security import password_manager, password_validator
from app.models.user import User


def main() -> int:
    email = settings.SUPER_ADMIN_EMAIL
    password = settings.SUPER_ADMIN_PASSWORD

    is_valid, error_msg = password_validator.validate(password)
    if not is_valid:
        print(f"Invalid SUPER_ADMIN_PASSWORD: {error_msg}")
        return 1

    with get_db() as db:
        existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        hashed_password = password_manager.hash_password(password)

        if existing:
            existing.hashed_password = hashed_password
            existing.is_superuser = True
            existing.is_active = True
            existing.is_verified = True
            existing.full_name = existing.full_name or "Super Admin"
            print(f"Updated super admin user: {email}")
        else:
            user = User(
                email=email,
                hashed_password=hashed_password,
                full_name="Super Admin",
                is_superuser=True,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            print(f"Created super admin user: {email}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

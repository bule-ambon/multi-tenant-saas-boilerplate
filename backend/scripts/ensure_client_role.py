#!/usr/bin/env python3
"""
Ensure the global client role exists.
"""
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import get_db
from app.models.role import Role


def main() -> int:
    with get_db() as db:
        existing = db.execute(select(Role).where(Role.slug == "client")).scalar_one_or_none()
        if existing:
            print("Client role already exists.")
            return 0

        role = Role(
            name="Client",
            slug="client",
            description="Read-only client role",
            is_system_role=True,
            is_default=False,
            tenant_id=None,
        )
        db.add(role)
        print("Created client role.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

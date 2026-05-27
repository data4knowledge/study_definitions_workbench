"""Add or update a workbench user (the email-code login allow-list).

With Auth0 removed, the User table is the source of truth for who may
log in and which roles they hold. Run this to add/update an entry.

Usage (from the repo root, with the right PYTHON_ENVIRONMENT set):

    python -m scripts.seed_user --email dih@data4knowledge.dk \
        --name "Dave IH" --roles Admin,Transmit

Roles are a comma-separated list. Known roles: Admin, Transmit.
Re-running for an existing email updates the name and roles.
"""

import argparse

from app.database.database import SessionLocal
from app.database.database_manager import DatabaseManager
from app.database.database_tables import User as UserDB


def upsert_user(email: str, name: str, roles: str) -> None:
    email = email.strip().lower()
    session = SessionLocal()
    try:
        existing = session.query(UserDB).filter(UserDB.email == email).first()
        if existing:
            existing.display_name = name
            existing.roles = roles
            existing.is_active = True
            if not existing.identifier:
                existing.identifier = email
            session.commit()
            print(f"Updated user '{email}' (roles: '{roles or '<none>'}')")
        else:
            session.add(
                UserDB(
                    identifier=email,
                    email=email,
                    display_name=name,
                    roles=roles,
                    is_active=True,
                )
            )
            session.commit()
            print(f"Created user '{email}' (roles: '{roles or '<none>'}')")
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Add or update a workbench user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True, help="Display name (alphanumeric/spaces)")
    parser.add_argument(
        "--roles",
        default="",
        help="Comma-separated roles, e.g. 'Admin,Transmit'. Empty for none.",
    )
    args = parser.parse_args()

    # Make sure the database and schema (incl. the roles column) exist.
    dbm = DatabaseManager()
    dbm.check()
    dbm.migrate()

    upsert_user(args.email, args.name, args.roles)


if __name__ == "__main__":
    main()

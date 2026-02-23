#!/usr/bin/env python3
"""
Ensure the demo API key exists in the database.

This script creates the standard demo API key if it doesn't already exist.
It should be run during deployment to ensure the demo key is always available.
"""

import os
from pathlib import Path
import sys

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.models.api_key import DEMO_API_KEY_CONFIG
from src.domain.repositories.api_key_repository import APIKeyRepository


def ensure_demo_key():
    """Create the demo API key if it doesn't exist."""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False

    try:
        # Create synchronous engine for this script
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(bind=engine)

        with SessionLocal() as session:
            repo = APIKeyRepository(session)

            # Check if demo key exists
            existing_key = repo.get_by_key(DEMO_API_KEY_CONFIG["key"])
            if existing_key:
                print(f"✓ Demo API key already exists: {DEMO_API_KEY_CONFIG['key']}")
                print(f"  Name: {existing_key.name}")
                print(
                    f"  Limits: {existing_key.max_patients_per_request} patients, {existing_key.max_requests_per_day} requests/day"
                )
                return True

            # Create the demo key
            demo_key = repo.create_demo_key_if_not_exists()
            print(f"✓ Created demo API key: {DEMO_API_KEY_CONFIG['key']}")
            print(f"  Name: {demo_key.name}")
            print(
                f"  Limits: {demo_key.max_patients_per_request} patients, {demo_key.max_requests_per_day} requests/day"
            )
            return True

    except Exception as e:
        print(f"ERROR: Failed to ensure demo key: {e}")
        return False


if __name__ == "__main__":
    success = ensure_demo_key()
    sys.exit(0 if success else 1)

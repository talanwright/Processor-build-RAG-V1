#!/usr/bin/env python3
"""
Add access_password column to loans table
Run this once to fix the database schema
"""

import os
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set")
    print("Set it in Railway or locally before running this script")
    exit(1)

# Fix Railway's postgres:// URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='loans' AND column_name='access_password'
        """))

        if result.fetchone():
            print("✅ Column 'access_password' already exists!")
        else:
            # Add the column
            print("Adding 'access_password' column to loans table...")
            conn.execute(text("""
                ALTER TABLE loans
                ADD COLUMN access_password TEXT
            """))
            conn.commit()
            print("✅ SUCCESS! Column 'access_password' added to loans table")

        print("\nDatabase is now ready!")
        print("You can test your Make.com scenario again.")

except Exception as e:
    print(f"❌ ERROR: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure DATABASE_URL is set correctly")
    print("2. Make sure you have permissions to alter the table")

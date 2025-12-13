#!/usr/bin/env python3
"""
Quick script to create the access_tokens table in Railway database
Run this once to fix the 500 error
"""

from database import init_database

if __name__ == "__main__":
    print("Creating database tables...")
    try:
        init_database()
        print("✅ SUCCESS! Database tables created.")
        print("The access_tokens table now exists in Railway.")
        print("\nYou can now test your Make.com scenario again!")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\nIf you see an error, make sure your DATABASE_URL environment variable is set.")

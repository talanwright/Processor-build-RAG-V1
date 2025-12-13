#!/usr/bin/env python3
"""
Vector Database Initialization Script
Loads knowledge base documents into ChromaDB vector database
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vector_database import VectorDatabase

def main():
    """Initialize vector database and load knowledge base"""

    print("=" * 60)
    print("VECTOR DATABASE INITIALIZATION")
    print("=" * 60)
    print()

    # Set up paths
    script_dir = Path(__file__).parent
    knowledge_base_path = script_dir / "knowledge_base"
    db_path = script_dir / "vector_db"

    print(f"Knowledge base path: {knowledge_base_path}")
    print(f"Vector database path: {db_path}")
    print()

    # Check if knowledge base exists
    if not knowledge_base_path.exists():
        print("ERROR: knowledge_base directory not found!")
        return 1

    # Count knowledge base files
    kb_files = list(knowledge_base_path.rglob("*.txt"))
    print(f"Found {len(kb_files)} knowledge base documents:")

    # List all files by category
    for category in ['loan_requirements', 'compliance', 'red_flags']:
        category_path = knowledge_base_path / category
        if category_path.exists():
            files = list(category_path.glob("*.txt"))
            print(f"\n  {category.upper()}:")
            for file in files:
                print(f"    - {file.name}")

    print("\n" + "-" * 60)
    print("Initializing vector database...")
    print("-" * 60)
    print()

    try:
        # Initialize vector database
        vector_db = VectorDatabase(db_path=str(db_path))
        print("✓ Vector database client initialized")

        # Load knowledge base
        print("\nLoading knowledge base into vector database...")
        vector_db.add_knowledge_base(str(knowledge_base_path))

        print("\n" + "=" * 60)
        print("DATABASE INITIALIZATION COMPLETE!")
        print("=" * 60)
        print()

        # Verify collections
        print("Verifying collections:")

        collections = {
            'loan_requirements': vector_db.loan_requirements_collection,
            'compliance': vector_db.compliance_collection,
            'red_flags': vector_db.red_flags_collection
        }

        for name, collection in collections.items():
            try:
                count = collection.count()
                print(f"  ✓ {name}: {count} documents")
            except Exception as e:
                print(f"  ✗ {name}: Error - {str(e)}")

        print()
        print("Vector database is ready to use!")
        print(f"Database location: {db_path}")
        print()

        return 0

    except Exception as e:
        print("\n" + "=" * 60)
        print("ERROR DURING INITIALIZATION")
        print("=" * 60)
        print(f"\nError: {str(e)}")
        print("\nPlease ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        print()
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Script to populate local database with existing loan data
"""

import os
from database import SessionLocal, Loan, Document
from datetime import datetime

def populate_database():
    """Populate database with existing loan files"""
    db = SessionLocal()

    try:
        # Path to uploads directory
        uploads_dir = "./uploads"

        if not os.path.exists(uploads_dir):
            print(f"❌ Uploads directory not found: {uploads_dir}")
            return

        # Get all loan directories
        loan_dirs = [d for d in os.listdir(uploads_dir) if os.path.isdir(os.path.join(uploads_dir, d))]

        print(f"Found {len(loan_dirs)} loan directories")

        for loan_id in loan_dirs:
            loan_path = os.path.join(uploads_dir, loan_id)

            # Check if loan already exists
            existing_loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()

            if existing_loan:
                print(f"⏭️  Loan {loan_id} already exists, skipping...")
                continue

            # Count documents
            files = [f for f in os.listdir(loan_path) if os.path.isfile(os.path.join(loan_path, f))]

            print(f"📁 Creating loan: {loan_id} with {len(files)} documents")

            # Create loan record
            loan = Loan(
                loan_id=loan_id,
                borrower_email=loan_id,  # Using loan_id as email for now
                borrower_name=None,
                loan_type="conventional",
                status="ready_for_underwriting",
                completeness_score=100.0,
                risk_score=0.1,
                document_count=len(files),
                missing_documents="[]",
                reminder_count=0,
                created_date=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            db.add(loan)

            # Add documents
            for filename in files:
                file_path = os.path.join(loan_path, filename)
                file_size = os.path.getsize(file_path)

                document = Document(
                    loan_id=loan_id,
                    filename=filename,
                    file_path=file_path,
                    file_size=file_size,
                    upload_date=datetime.utcnow()
                )
                db.add(document)
                print(f"  ✅ Added document: {filename}")

            db.commit()
            print(f"✅ Loan {loan_id} created successfully!\n")

        # Summary
        total_loans = db.query(Loan).count()
        total_docs = db.query(Document).count()

        print(f"\n{'='*50}")
        print(f"✅ Database populated successfully!")
        print(f"📊 Total loans: {total_loans}")
        print(f"📄 Total documents: {total_docs}")
        print(f"{'='*50}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Populating local database with loan data...\n")
    populate_database()

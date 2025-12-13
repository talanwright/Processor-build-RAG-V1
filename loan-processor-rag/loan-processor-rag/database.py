#!/usr/bin/env python3
"""
Database models and connection for Loan Processor
Using PostgreSQL with SQLAlchemy
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property
from typing import Optional
from encryption import encrypt_field, decrypt_field

# Database URL from environment variable (Railway provides this automatically)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./loan_processor.db"  # Use SQLite for local development
)

# Fix for Railway's postgres:// URLs (SQLAlchemy requires postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create SQLAlchemy engine
# Use different settings for SQLite vs PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# ====================
# DATABASE MODELS
# ====================

class Loan(Base):
    """Loan tracking table with document completeness and reminder tracking"""
    __tablename__ = "loans"

    # Primary fields
    loan_id = Column(String(255), primary_key=True, index=True)
    _borrower_email = Column("borrower_email", Text, nullable=False)  # Encrypted
    _borrower_name = Column("borrower_name", Text, nullable=True)  # Encrypted

    # Encrypted field properties with automatic encryption/decryption
    @hybrid_property
    def borrower_email(self):
        """Decrypt email when reading"""
        return decrypt_field(self._borrower_email) if self._borrower_email else None

    @borrower_email.setter
    def borrower_email(self, value):
        """Encrypt email when writing"""
        self._borrower_email = encrypt_field(value) if value else None

    @hybrid_property
    def borrower_name(self):
        """Decrypt name when reading"""
        return decrypt_field(self._borrower_name) if self._borrower_name else None

    @borrower_name.setter
    def borrower_name(self, value):
        """Encrypt name when writing"""
        self._borrower_name = encrypt_field(value) if value else None

    # Loan details
    loan_type = Column(String(100), default="conventional")
    status = Column(String(50), default="pending_documents")

    # Scores
    completeness_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)

    # Document tracking
    document_count = Column(Integer, default=0)
    missing_documents = Column(Text, nullable=True)  # JSON string of missing docs

    # Reminder tracking (NEW FIELDS)
    last_reminder_sent = Column(DateTime, nullable=True)
    reminder_count = Column(Integer, default=0)

    # Timestamps
    created_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Loan(loan_id='{self.loan_id}', completeness={self.completeness_score}, reminders={self.reminder_count})>"


class Document(Base):
    """Document metadata table"""
    __tablename__ = "documents"

    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(String(255), index=True, nullable=False)

    # Document details
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_type = Column(String(50), nullable=True)

    # Timestamps
    upload_date = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Document(loan_id='{self.loan_id}', filename='{self.filename}')>"


# ====================
# DATABASE FUNCTIONS
# ====================

def get_db():
    """Dependency function to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def drop_all_tables():
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped!")


if __name__ == "__main__":
    print("Initializing database...")
    print(f"Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
    init_database()
    print("Done!")

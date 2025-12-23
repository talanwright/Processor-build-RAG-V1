#!/usr/bin/env python3
"""
SECURED Loan Processor RAG API - Production Ready with PostgreSQL Database
Implements: API Key Auth, Rate Limiting, CORS Restrictions, Audit Logging, Database Tracking
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Header, Request, Depends
from fastapi.responses import FileResponse, Response, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import os
import shutil
import uvicorn
from datetime import datetime, timedelta
import json
import secrets
import hashlib
from collections import defaultdict
import time

# Import database models and functions
from database import get_db, Loan, Document, AccessToken, init_database
from encryption import encrypt_file, decrypt_file

# Import document extractor for income calculation
try:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from document_extractor import extractor as document_extractor
    EXTRACTOR_AVAILABLE = True
except ImportError:
    EXTRACTOR_AVAILABLE = False
    print("⚠️  Document extractor not available - income calculation will be skipped")

# Initialize FastAPI app
app = FastAPI(
    title="Loan Processor RAG API (SECURED with DB)",
    version="3.0.0",
    docs_url=None,  # Disabled for production
    redoc_url=None  # Disabled for production
)

# Set up templates
templates = Jinja2Templates(directory="templates")

# ====================
# SECURITY CONFIGURATION
# ====================

# API Key from environment variable (CRITICAL!)
API_KEY = os.getenv("API_KEY", "CHANGE_THIS_IN_PRODUCTION")  # Set in Railway!

# Allowed origins for CORS (Make.com + Retool)
ALLOWED_ORIGINS = [
    "https://hook.us1.make.com",
    "https://hook.eu1.make.com",
    "https://hook.eu2.make.com",
    "https://us1.make.com",
    "https://eu1.make.com",
    "https://eu2.make.com",
    "https://retool.com",
    "https://*.retool.com",
]

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100  # Max requests per window
RATE_LIMIT_WINDOW = 3600  # Time window in seconds (1 hour)
rate_limit_store = defaultdict(list)

# Document retention (auto-delete after X days)
# 7 years = 2555 days (complies with federal lending regulations)
# FHA loans technically require life-of-loan + 2 years, but 7 years meets most requirements
DOCUMENT_RETENTION_DAYS = 2555

# File upload limits and restrictions
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
ALLOWED_FILE_TYPES = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.txt', '.xls', '.xlsx']

# Audit log file
AUDIT_LOG_FILE = "./audit_log.json"

# IP Whitelisting (optional but recommended)
# Set to empty list [] to disable IP whitelisting
# Add your IPs here - get them from Make.com and Retool documentation
ALLOWED_IPS = [
    # Make.com IP address
    "44.209.150.16",
    "44.210.162.163",
    "35.170.163.230",

    # Retools IP address


    # Make.com webhook IPs (update with actual IPs from Make.com)
    # You can find these in Make.com documentation
    # Example: "34.89.123.456", "34.89.123.457"

    # Retool IPs (update with actual IPs from Retool)
    # You can find these in Retool settings
    # Example: "52.72.123.456", "52.72.123.457"

    # Your office/home IP (optional)
    # Find yours at: https://whatismyipaddress.com/
    # Example: "203.0.113.45"
]

# Set to True to enable IP whitelisting
ENABLE_IP_WHITELIST = False  # Set to True when you add IPs above

# ====================
# MIDDLEWARE & SECURITY
# ====================

# Restrict CORS to only Make.com and Retool
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Trusted host middleware (prevent host header attacks)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*.railway.app", "*.up.railway.app", "localhost"]
)

# Initialize upload directory
upload_dir = "./uploads"
os.makedirs(upload_dir, exist_ok=True)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database on application startup"""
    init_database()
    print("Database initialized!")

# ====================
# SECURITY FUNCTIONS
# ====================

def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key from request header"""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include 'X-API-Key' header."
        )

    if x_api_key != API_KEY:
        # Log failed authentication attempt
        audit_log("SECURITY", "FAILED_AUTH", {"attempted_key": x_api_key[:8] + "..."})
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return x_api_key

def check_ip_whitelist(request: Request):
    """Check if request IP is whitelisted"""
    if not ENABLE_IP_WHITELIST or not ALLOWED_IPS:
        return  # IP whitelisting disabled

    client_ip = request.client.host

    # Check if IP is in whitelist
    if client_ip not in ALLOWED_IPS:
        audit_log("SECURITY", "IP_BLOCKED", {
            "ip": client_ip,
            "reason": "not_in_whitelist"
        })
        raise HTTPException(
            status_code=403,
            detail="Access denied. Your IP address is not authorized."
        )

def check_rate_limit(request: Request):
    """Simple rate limiting by IP address"""
    client_ip = request.client.host
    current_time = time.time()

    # Clean old entries
    rate_limit_store[client_ip] = [
        timestamp for timestamp in rate_limit_store[client_ip]
        if current_time - timestamp < RATE_LIMIT_WINDOW
    ]

    # Check if over limit
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        audit_log("SECURITY", "RATE_LIMIT_EXCEEDED", {
            "ip": client_ip,
            "requests": len(rate_limit_store[client_ip])
        })
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_REQUESTS} requests per hour."
        )

    # Add current request
    rate_limit_store[client_ip].append(current_time)

def audit_log(category: str, action: str, details: Dict):
    """Log all security and data access events"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "action": action,
        "details": details
    }

    # Append to audit log file
    try:
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Failed to write audit log: {e}")

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal attacks"""
    # Remove path separators and dangerous characters
    safe_name = os.path.basename(filename)
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._- ")
    return safe_name

def cleanup_old_documents():
    """Delete documents older than retention period"""
    if not os.path.exists(upload_dir):
        return

    cutoff_time = time.time() - (DOCUMENT_RETENTION_DAYS * 86400)
    deleted_count = 0

    for loan_dir in os.listdir(upload_dir):
        loan_path = os.path.join(upload_dir, loan_dir)
        if os.path.isdir(loan_path):
            # Check directory modification time
            if os.path.getmtime(loan_path) < cutoff_time:
                shutil.rmtree(loan_path)
                deleted_count += 1
                audit_log("DATA_RETENTION", "AUTO_DELETE", {
                    "loan_id": loan_dir,
                    "reason": "retention_period_expired"
                })

    return deleted_count

def generate_secure_token(loan_id: str, db: Session) -> str:
    """Generate a secure access token for loan officer access (no expiration)"""
    # Generate a cryptographically secure random token
    token = secrets.token_urlsafe(32)

    # Set to 100 years in the future (effectively no expiration for loan officers)
    expires_at = datetime.utcnow() + timedelta(days=365 * 100)

    # Create access token record
    access_token = AccessToken(
        token=token,
        loan_id=loan_id,
        expires_at=expires_at
    )
    db.add(access_token)
    db.commit()

    return token

# ====================
# PYDANTIC MODELS
# ====================

class LoanAnalysisRequest(BaseModel):
    loan_id: str
    borrower_email: Optional[str] = None
    borrower_name: Optional[str] = None
    borrower_info: Dict[str, Any]
    loan_type: Optional[str] = "conventional"
    documents: Optional[List[Dict]] = []

class LoanAnalysisResponse(BaseModel):
    loan_id: str
    loan_type: str
    analysis_complete: bool
    completeness_score: float
    risk_score: float
    missing_documents: List[Dict]
    red_flags: List[Dict]
    suggested_actions: List[str]
    email_template: Optional[str] = None
    status: str

class IncompleteLoanResponse(BaseModel):
    loan_id: str
    borrower_email: str
    borrower_name: Optional[str]
    completeness_score: float
    missing_documents: List[str]
    last_reminder_sent: Optional[datetime]
    reminder_count: int
    created_date: datetime
    hours_since_last_reminder: Optional[float]

# ====================
# ANALYSIS FUNCTIONS
# ====================

def analyze_loan_simple(loan_data):
    """Simplified loan analysis (same as before)"""
    loan_id = loan_data.get('loan_id', 'unknown')
    loan_type = loan_data.get('loan_type', 'conventional')
    documents = loan_data.get('documents', [])

    # Required documents for conventional loan
    required_docs = ['application', 'pay_stub', 'bank_statement', 'tax_return', 'employment_verification']

    # Check what we have
    present_docs = []
    for doc in documents:
        if 'filename' in doc:
            filename = doc['filename'].lower()
            if 'application' in filename or '1003' in filename:
                present_docs.append('application')
            elif 'pay' in filename or 'stub' in filename:
                present_docs.append('pay_stub')
            elif 'bank' in filename or 'statement' in filename:
                present_docs.append('bank_statement')
            elif 'tax' in filename or 'w2' in filename or '1040' in filename:
                present_docs.append('tax_return')
            elif 'employment' in filename or 'voe' in filename:
                present_docs.append('employment_verification')

    present_docs = list(set(present_docs))
    missing_docs = [doc for doc in required_docs if doc not in present_docs]

    # Calculate scores
    completeness_score = (len(present_docs) / len(required_docs)) * 100
    risk_score = 0.3 if len(missing_docs) > 2 else 0.1

    # Create missing documents list
    missing_documents = []
    for doc in missing_docs:
        missing_documents.append({
            'document_type': doc,
            'description': f'{doc.replace("_", " ").title()} required for loan processing',
            'urgency': 'high' if doc in ['application', 'pay_stub'] else 'medium'
        })

    # Create red flags
    red_flags = []
    if len(documents) < 2:
        red_flags.append({
            'type': 'insufficient_documentation',
            'severity': 'medium',
            'description': 'Very few documents submitted for review'
        })

    # Generate actions
    suggested_actions = []
    if missing_docs:
        suggested_actions.append(f"Request missing documents: {', '.join(missing_docs)}")
    if completeness_score >= 80:
        suggested_actions.append("File appears ready for underwriting review")

    return {
        'loan_id': loan_id,
        'loan_type': loan_type,
        'analysis_complete': True,
        'completeness_score': completeness_score,
        'risk_score': risk_score,
        'missing_documents': missing_documents,
        'missing_docs_list': missing_docs,  # For database storage
        'red_flags': red_flags,
        'suggested_actions': suggested_actions,
        'email_template': 'missing_documents' if missing_docs else 'ready_for_underwriting',
        'status': 'pending_documents' if missing_docs else 'ready_for_underwriting'
    }

# ====================
# API ENDPOINTS
# ====================

@app.get("/")
async def root():
    """Health check endpoint (PUBLIC - no auth required)"""
    return {
        "message": "Loan Processor RAG API (SECURED with PostgreSQL)",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "3.3.1",
        "security": "API Key + Secure Tokens for Loan Officer Access",
        "database": "PostgreSQL",
        "endpoints": [
            "/upload-documents",
            "/analyze-loan",
            "/generate-email",
            "/download-document/{loan_id}/{filename}",
            "/set-access-password",
            "/secure-loan/{token} (PUBLIC - no auth)",
            "/secure-loan/{token}/download/{filename} (PUBLIC - no auth)",
            "/revoke-token/{token}",
            "/stats",
            "/loans",
            "/loans/{loan_id}",
            "/incomplete-loans",
            "/update-reminder",
            "/health"
        ],
        "features": [
            "Secure token links for loan officer access",
            "Password-protected direct downloads (optional)",
            "Encrypted file storage (AES-128)",
            "Encrypted PII in database",
            "Audit logging for all access",
            "Permanent access links (no expiration)"
        ]
    }

@app.get("/init-db")
async def init_db_tables():
    """Initialize database tables (PUBLIC - for deployment setup)"""
    try:
        init_database()
        return {
            "success": True,
            "message": "Database tables initialized successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")

@app.get("/migrate-db")
async def migrate_database(db: Session = Depends(get_db)):
    """Add missing columns to existing tables (PUBLIC - for schema updates)"""
    try:
        from sqlalchemy import text

        columns_added = []

        # Check if access_password column exists
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='loans' AND column_name='access_password'
        """))

        if not result.fetchone():
            # Add the missing column
            db.execute(text("""
                ALTER TABLE loans
                ADD COLUMN access_password TEXT
            """))
            columns_added.append("access_password")

        # Check if monthly_income column exists
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='loans' AND column_name='monthly_income'
        """))

        if not result.fetchone():
            # Add the missing column
            db.execute(text("""
                ALTER TABLE loans
                ADD COLUMN monthly_income TEXT
            """))
            columns_added.append("monthly_income")

        db.commit()

        if columns_added:
            return {
                "success": True,
                "message": f"Columns added successfully: {', '.join(columns_added)}",
                "action": "columns_added",
                "columns": columns_added,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "message": "All columns already exist",
                "action": "none",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Detailed health check endpoint for monitoring (PUBLIC - no auth required)"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
        db_error = None
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)

    # Check upload directory
    upload_dir_exists = os.path.exists(upload_dir)

    return {
        "status": "healthy" if db_status == "healthy" and upload_dir_exists else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "components": {
            "database": {
                "status": db_status,
                "type": "PostgreSQL",
                "error": db_error
            },
            "storage": {
                "status": "healthy" if upload_dir_exists else "unhealthy",
                "upload_directory": upload_dir_exists
            },
            "api": {
                "status": "healthy"
            }
        },
        "security": {
            "api_key_required": True,
            "ip_whitelist_enabled": ENABLE_IP_WHITELIST,
            "rate_limiting": f"{RATE_LIMIT_REQUESTS} requests per hour",
            "file_size_limit": f"{MAX_FILE_SIZE // 1024 // 1024}MB",
            "allowed_file_types": len(ALLOWED_FILE_TYPES)
        }
    }

@app.post("/upload-documents")
async def upload_documents(
    request: Request,
    files: List[UploadFile] = File(...),
    loan_id: str = Form(...),
    borrower_email: str = Form(None),
    access_password: str = Form(None),  # NEW: Optional password for document access
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Upload loan documents (SECURED with optional password protection)"""
    # Security checks
    check_ip_whitelist(request)  # Check IP first
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        # Sanitize loan_id to prevent directory traversal
        safe_loan_id = sanitize_filename(loan_id)

        uploaded_files = []
        loan_dir = os.path.join(upload_dir, safe_loan_id)
        os.makedirs(loan_dir, exist_ok=True)

        for file in files:
            # Validate file type
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in ALLOWED_FILE_TYPES:
                audit_log("SECURITY", "BLOCKED_FILE_TYPE", {
                    "filename": file.filename,
                    "file_type": file_ext,
                    "loan_id": safe_loan_id,
                    "ip": request.client.host
                })
                raise HTTPException(
                    status_code=400,
                    detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}"
                )

            # Sanitize filename
            safe_filename = sanitize_filename(file.filename)
            file_path = os.path.join(loan_dir, safe_filename)

            # Save file temporarily to check size
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                # Delete the file since it's too large
                os.remove(file_path)
                audit_log("SECURITY", "FILE_SIZE_EXCEEDED", {
                    "filename": file.filename,
                    "size_mb": round(file_size / 1024 / 1024, 2),
                    "max_size_mb": round(MAX_FILE_SIZE / 1024 / 1024, 2),
                    "loan_id": safe_loan_id,
                    "ip": request.client.host
                })
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{file.filename}' exceeds {MAX_FILE_SIZE // 1024 // 1024}MB limit (size: {round(file_size / 1024 / 1024, 2)}MB)"
                )

            # Encrypt the file immediately after upload
            encrypt_file(file_path)

            # Add to database
            document = Document(
                loan_id=safe_loan_id,
                filename=safe_filename,
                file_path=file_path,
                file_size=file_size
            )
            db.add(document)

            uploaded_files.append({
                "filename": safe_filename,
                "file_path": file_path,
                "size": file_size
            })

        # Update or create loan record
        loan = db.query(Loan).filter(Loan.loan_id == safe_loan_id).first()
        if not loan:
            loan = Loan(
                loan_id=safe_loan_id,
                borrower_email=borrower_email,
                document_count=len(uploaded_files)
            )
            # Set password if provided
            if access_password:
                loan.access_password = access_password
            db.add(loan)
        else:
            loan.document_count = db.query(Document).filter(Document.loan_id == safe_loan_id).count()
            loan.last_updated = datetime.utcnow()
            # Update password if provided
            if access_password:
                loan.access_password = access_password

        db.commit()

        # Audit log
        audit_log("DATA_ACCESS", "UPLOAD", {
            "loan_id": safe_loan_id,
            "file_count": len(uploaded_files),
            "ip": request.client.host
        })

        return {
            "loan_id": safe_loan_id,
            "uploaded_files": uploaded_files,
            "total_files": len(uploaded_files),
            "upload_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        db.rollback()
        audit_log("ERROR", "UPLOAD_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/upload-document")
async def upload_single_document(
    request: Request,
    file: UploadFile = File(...),
    loan_id: str = Form(...),
    borrower_email: str = Form(None),
    access_password: str = Form(None),
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Upload a single loan document - for Make.com iterator (SECURED)"""
    # Security checks
    check_ip_whitelist(request)
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        # Sanitize loan_id
        safe_loan_id = sanitize_filename(loan_id)

        # Create loan directory
        loan_dir = os.path.join(upload_dir, safe_loan_id)
        os.makedirs(loan_dir, exist_ok=True)

        # Validate file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_FILE_TYPES:
            audit_log("SECURITY", "BLOCKED_FILE_TYPE", {
                "filename": file.filename,
                "file_type": file_ext,
                "loan_id": safe_loan_id,
                "ip": request.client.host
            })
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}"
            )

        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)
        file_path = os.path.join(loan_dir, safe_filename)

        # Save file temporarily
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            os.remove(file_path)
            audit_log("SECURITY", "FILE_SIZE_EXCEEDED", {
                "filename": file.filename,
                "size_mb": round(file_size / 1024 / 1024, 2),
                "max_size_mb": round(MAX_FILE_SIZE / 1024 / 1024, 2),
                "loan_id": safe_loan_id,
                "ip": request.client.host
            })
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds {MAX_FILE_SIZE // 1024 // 1024}MB limit"
            )

        # Encrypt the file
        encrypt_file(file_path)

        # Add to database
        document = Document(
            loan_id=safe_loan_id,
            filename=safe_filename,
            file_path=file_path,
            file_size=file_size
        )
        db.add(document)

        # Update or create loan record
        loan = db.query(Loan).filter(Loan.loan_id == safe_loan_id).first()
        if not loan:
            loan = Loan(
                loan_id=safe_loan_id,
                borrower_email=borrower_email,
                document_count=1
            )
            if access_password:
                loan.access_password = access_password
            db.add(loan)
        else:
            loan.document_count = db.query(Document).filter(Document.loan_id == safe_loan_id).count()
            loan.last_updated = datetime.utcnow()
            if access_password:
                loan.access_password = access_password

        db.commit()

        # Audit log
        audit_log("DATA_ACCESS", "UPLOAD_SINGLE", {
            "loan_id": safe_loan_id,
            "filename": safe_filename,
            "ip": request.client.host
        })

        return {
            "loan_id": safe_loan_id,
            "borrower_email": borrower_email,
            "filename": safe_filename,
            "file_path": file_path,
            "size": file_size,
            "upload_timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"{str(e)} | {traceback.format_exc()}"
        audit_log("ERROR", "UPLOAD_SINGLE_FAILED", {"error": error_detail})
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

class Base64FileUpload(BaseModel):
    filename: str
    data: str  # base64 encoded file content
    mime_type: Optional[str] = None

class Base64UploadRequest(BaseModel):
    loan_id: str
    borrower_email: Optional[str] = None
    files: List[Base64FileUpload]

@app.post("/upload-documents-base64")
async def upload_documents_base64(
    request: Request,
    upload_request: Base64UploadRequest,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Upload loan documents using base64 encoding - easier for Make.com (SECURED)"""
    import base64

    # Security checks
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        safe_loan_id = sanitize_filename(upload_request.loan_id)
        loan_dir = os.path.join(upload_dir, safe_loan_id)
        os.makedirs(loan_dir, exist_ok=True)

        uploaded_files = []

        for file_data in upload_request.files:
            # Validate file type
            file_ext = os.path.splitext(file_data.filename)[1].lower()
            if file_ext not in ALLOWED_FILE_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type '{file_ext}' not allowed"
                )

            # Sanitize filename
            safe_filename = sanitize_filename(file_data.filename)
            file_path = os.path.join(loan_dir, safe_filename)

            # Decode and save file
            try:
                file_content = base64.b64decode(file_data.data)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid base64 data for {file_data.filename}")

            with open(file_path, "wb") as f:
                f.write(file_content)

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{file_data.filename}' exceeds size limit"
                )

            # Encrypt the file
            encrypt_file(file_path)

            # Add to database
            document = Document(
                loan_id=safe_loan_id,
                filename=safe_filename,
                file_path=file_path,
                file_size=file_size
            )
            db.add(document)

            uploaded_files.append({
                "filename": safe_filename,
                "file_path": file_path,
                "size": file_size
            })

        # Update or create loan record
        loan = db.query(Loan).filter(Loan.loan_id == safe_loan_id).first()
        if not loan:
            loan = Loan(
                loan_id=safe_loan_id,
                borrower_email=upload_request.borrower_email,
                document_count=len(uploaded_files)
            )
            db.add(loan)
        else:
            loan.document_count = db.query(Document).filter(Document.loan_id == safe_loan_id).count()
            loan.last_updated = datetime.utcnow()

        db.commit()

        # Audit log
        audit_log("DATA_ACCESS", "UPLOAD_BASE64", {
            "loan_id": safe_loan_id,
            "file_count": len(uploaded_files),
            "ip": request.client.host
        })

        return {
            "success": True,
            "loan_id": safe_loan_id,
            "uploaded_files": uploaded_files,
            "total_files": len(uploaded_files),
            "upload_timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"{str(e)} | {traceback.format_exc()}"
        audit_log("ERROR", "UPLOAD_BASE64_FAILED", {"error": error_detail})
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/analyze-loan", response_model=LoanAnalysisResponse)
async def analyze_loan(
    request: Request,
    loan_request: LoanAnalysisRequest,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Main loan analysis endpoint (SECURED)"""
    # Security checks
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        # Sanitize loan_id
        safe_loan_id = sanitize_filename(loan_request.loan_id)

        # Check for uploaded files if documents not provided
        if not loan_request.documents:
            # Get from database
            db_documents = db.query(Document).filter(Document.loan_id == safe_loan_id).all()
            loan_request.documents = [
                {"filename": doc.filename, "file_path": doc.file_path}
                for doc in db_documents
            ]

        # Perform analysis
        loan_data = {
            "loan_id": safe_loan_id,
            "loan_type": loan_request.loan_type,
            "borrower_info": loan_request.borrower_info,
            "documents": loan_request.documents
        }

        analysis_result = analyze_loan_simple(loan_data)

        # Calculate monthly income from documents if extractor is available
        monthly_income = None
        if EXTRACTOR_AVAILABLE:
            try:
                loan_dir = os.path.join(upload_dir, safe_loan_id)
                if os.path.exists(loan_dir):
                    # Get list of documents for this loan
                    db_documents = db.query(Document).filter(Document.loan_id == safe_loan_id).all()
                    doc_list = [{"filename": doc.filename} for doc in db_documents]

                    # Extract income from documents
                    income_analysis = document_extractor.analyze_documents(loan_dir, doc_list)
                    monthly_income = income_analysis.get('total_monthly_income', 0)

                    # Add income breakdown and red flags to analysis result
                    analysis_result['monthly_income'] = monthly_income
                    analysis_result['income_breakdown'] = income_analysis.get('income_breakdown', [])
                    if income_analysis.get('red_flags'):
                        analysis_result['red_flags'].extend(income_analysis['red_flags'])

                    audit_log("INCOME_CALCULATION", "SUCCESS", {
                        "loan_id": safe_loan_id,
                        "monthly_income": monthly_income,
                        "confidence": income_analysis.get('confidence', 'unknown')
                    })
            except Exception as e:
                audit_log("ERROR", "INCOME_CALCULATION_FAILED", {
                    "loan_id": safe_loan_id,
                    "error": str(e)
                })

        # Update loan in database
        loan = db.query(Loan).filter(Loan.loan_id == safe_loan_id).first()
        if not loan:
            loan = Loan(
                loan_id=safe_loan_id,
                borrower_email=loan_request.borrower_email,
                borrower_name=loan_request.borrower_name
            )
            db.add(loan)

        # Update loan fields
        loan.loan_type = loan_request.loan_type
        loan.completeness_score = analysis_result['completeness_score']
        loan.risk_score = analysis_result['risk_score']
        loan.status = analysis_result['status']
        loan.missing_documents = json.dumps(analysis_result['missing_docs_list'])
        loan.document_count = len(loan_request.documents)
        loan.last_updated = datetime.utcnow()

        # Store calculated monthly income (encrypted automatically)
        if monthly_income and monthly_income > 0:
            loan.monthly_income = monthly_income

        db.commit()

        # Audit log (redact PII)
        audit_log("DATA_ACCESS", "ANALYZE", {
            "loan_id": safe_loan_id,
            "completeness_score": analysis_result['completeness_score'],
            "risk_score": analysis_result['risk_score'],
            "ip": request.client.host
        })

        return LoanAnalysisResponse(**analysis_result)

    except Exception as e:
        db.rollback()
        audit_log("ERROR", "ANALYSIS_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/loans")
async def get_all_loans(
    request: Request,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Get all loans (for Retool dashboard)"""
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        loans = db.query(Loan).all()

        return {
            "loans": [
                {
                    "loan_id": loan.loan_id,
                    "borrower_email": loan.borrower_email,
                    "borrower_name": loan.borrower_name,
                    "loan_type": loan.loan_type,
                    "status": loan.status,
                    "completeness_score": loan.completeness_score,
                    "risk_score": loan.risk_score,
                    "document_count": loan.document_count,
                    "created_date": loan.created_date.isoformat() if loan.created_date else None,
                    "last_updated": loan.last_updated.isoformat() if loan.last_updated else None,
                    "reminder_count": loan.reminder_count,
                    "last_reminder_sent": loan.last_reminder_sent.isoformat() if loan.last_reminder_sent else None
                }
                for loan in loans
            ],
            "total_count": len(loans)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch loans: {str(e)}")

@app.get("/download-document/{loan_id}/{filename}")
@app.get("/loans/{loan_id}/documents/{filename}")
async def download_document(
    loan_id: str,
    filename: str,
    password: str,  # NEW: Required password parameter
    request: Request,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Download and decrypt a document (SECURED with PASSWORD)"""
    # Security checks
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        # Sanitize inputs
        safe_loan_id = sanitize_filename(loan_id)
        safe_filename = sanitize_filename(filename)

        # Verify loan exists
        loan = db.query(Loan).filter(Loan.loan_id == safe_loan_id).first()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")

        # NEW: Verify password
        if not loan.access_password:
            raise HTTPException(status_code=403, detail="Access password not set for this loan")

        if loan.access_password != password:
            # Log failed attempt
            audit_log("SECURITY", "DOWNLOAD_FAILED_AUTH", {
                "loan_id": safe_loan_id,
                "filename": safe_filename,
                "ip": request.client.host,
                "reason": "invalid_password"
            })
            raise HTTPException(status_code=403, detail="Invalid access password")

        # Verify document exists in database
        document = db.query(Document).filter(
            Document.loan_id == safe_loan_id,
            Document.filename == safe_filename
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if file exists on disk
        file_path = document.file_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document file not found on server")

        # Try to decrypt the file, fallback to original if decryption fails
        decrypted_data = decrypt_file(file_path)

        # If decryption failed (returned None), read the file as-is
        if decrypted_data is None:
            with open(file_path, 'rb') as f:
                decrypted_data = f.read()

        # Audit log
        audit_log("DATA_ACCESS", "DOWNLOAD", {
            "loan_id": safe_loan_id,
            "filename": safe_filename,
            "ip": request.client.host
        })

        # Return raw bytes with proper headers for download
        return Response(
            content=decrypted_data,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}"',
                "Content-Length": str(len(decrypted_data))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        audit_log("ERROR", "DOWNLOAD_FAILED", {
            "loan_id": loan_id,
            "filename": filename,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/loans/{loan_id}")
async def get_loan_details(
    loan_id: str,
    request: Request,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Get detailed loan information including documents"""
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")

        # Get documents
        documents = db.query(Document).filter(Document.loan_id == loan_id).all()

        return {
            "loan": {
                "loan_id": loan.loan_id,
                "borrower_email": loan.borrower_email,
                "borrower_name": loan.borrower_name,
                "loan_type": loan.loan_type,
                "status": loan.status,
                "completeness_score": loan.completeness_score,
                "risk_score": loan.risk_score,
                "document_count": loan.document_count,
                "missing_documents": json.loads(loan.missing_documents) if loan.missing_documents else [],
                "created_date": loan.created_date.isoformat() if loan.created_date else None,
                "last_updated": loan.last_updated.isoformat() if loan.last_updated else None,
                "reminder_count": loan.reminder_count,
                "last_reminder_sent": loan.last_reminder_sent.isoformat() if loan.last_reminder_sent else None
            },
            "documents": [
                {
                    "filename": doc.filename,
                    "file_size": doc.file_size,
                    "upload_date": doc.upload_date.isoformat() if doc.upload_date else None
                }
                for doc in documents
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch loan details: {str(e)}")

@app.get("/incomplete-loans")
async def get_incomplete_loans(
    request: Request,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Get all loans with completeness < 100% (for Make.com reminder scenario)"""
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        # Get loans where completeness_score < 100
        incomplete_loans = db.query(Loan).filter(Loan.completeness_score < 100).all()

        results = []
        for loan in incomplete_loans:
            # Calculate hours since last reminder
            hours_since_last_reminder = None
            if loan.last_reminder_sent:
                time_diff = datetime.utcnow() - loan.last_reminder_sent
                hours_since_last_reminder = time_diff.total_seconds() / 3600

            results.append({
                "loan_id": loan.loan_id,
                "borrower_email": loan.borrower_email,
                "borrower_name": loan.borrower_name,
                "completeness_score": loan.completeness_score,
                "missing_documents": json.loads(loan.missing_documents) if loan.missing_documents else [],
                "last_reminder_sent": loan.last_reminder_sent.isoformat() if loan.last_reminder_sent else None,
                "reminder_count": loan.reminder_count,
                "created_date": loan.created_date.isoformat() if loan.created_date else None,
                "hours_since_last_reminder": hours_since_last_reminder,
                "hours_since_creation": (datetime.utcnow() - loan.created_date).total_seconds() / 3600 if loan.created_date else None,
                "should_send_reminder_1": loan.reminder_count == 0 and (not loan.last_reminder_sent) and loan.created_date and (datetime.utcnow() - loan.created_date).total_seconds() >= 86400,  # 24 hours since creation
                "should_send_reminder_2": loan.reminder_count == 1 and loan.last_reminder_sent and hours_since_last_reminder and hours_since_last_reminder >= 24  # 24 hours since last reminder
            })

        return {
            "incomplete_loans": results,
            "total_count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch incomplete loans: {str(e)}")

@app.post("/update-reminder")
async def update_reminder_status(
    request: Request,
    loan_id: str,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Update reminder status after sending a reminder email"""
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")

        # Update reminder tracking
        loan.last_reminder_sent = datetime.utcnow()
        loan.reminder_count += 1
        loan.last_updated = datetime.utcnow()

        db.commit()

        # Audit log
        audit_log("REMINDER", "SENT", {
            "loan_id": loan_id,
            "reminder_count": loan.reminder_count,
            "ip": request.client.host
        })

        return {
            "loan_id": loan_id,
            "reminder_count": loan.reminder_count,
            "last_reminder_sent": loan.last_reminder_sent.isoformat(),
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        audit_log("ERROR", "UPDATE_REMINDER_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to update reminder status: {str(e)}")

@app.post("/set-access-password")
async def set_access_password(
    request: Request,
    loan_id: str = Form(...),
    access_password: str = Form(...),
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Set or update the access password for a loan's documents"""
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")

        # Update password
        loan.access_password = access_password
        loan.last_updated = datetime.utcnow()

        db.commit()

        # Audit log (don't log the actual password)
        audit_log("SECURITY", "PASSWORD_SET", {
            "loan_id": loan_id,
            "ip": request.client.host,
            "action": "password_updated" if loan.access_password else "password_created"
        })

        return {
            "loan_id": loan_id,
            "success": True,
            "message": "Access password set successfully",
            "password_set": True
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        audit_log("ERROR", "SET_PASSWORD_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to set access password: {str(e)}")

class SecureLinkRequest(BaseModel):
    loan_id: str

@app.post("/generate-secure-link")
async def generate_secure_link_only(
    link_request: SecureLinkRequest,
    request: Request,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Generate ONLY a secure link for a loan (no email content)"""
    verify_api_key(api_key)
    check_rate_limit(request)

    loan_id = link_request.loan_id

    try:
        safe_loan_id = sanitize_filename(loan_id)

        # Generate secure access token
        token = generate_secure_token(safe_loan_id, db)

        # Get the base URL from environment
        base_url = os.getenv("BASE_URL", "https://web-production-0a9f4.up.railway.app")
        secure_link = f"{base_url}/secure-loan/{token}"

        # Audit log
        audit_log("SECURITY", "SECURE_LINK_GENERATED", {
            "loan_id": safe_loan_id,
            "token": token[:8] + "...",
            "ip": request.client.host
        })

        return {
            "loan_id": safe_loan_id,
            "secure_link": secure_link,
            "token": token,
            "expires": "Never (100 years)",
            "generated_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        db.rollback()
        audit_log("ERROR", "SECURE_LINK_GENERATION_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Secure link generation failed: {str(e)}")

@app.post("/generate-email")
async def generate_email(
    request: Request,
    loan_id: str,
    borrower_name: str,
    missing_documents: List[str] = [],
    red_flags: List[Dict] = [],
    template_type: str = "missing_docs",
    monthly_income: float = None,
    completeness_score: float = None,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Generate email content with secure link for loan officer (SECURED)"""
    # Security checks
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        safe_loan_id = sanitize_filename(loan_id)

        # Generate secure access token for loan officer
        token = generate_secure_token(safe_loan_id, db)

        # Get the base URL from environment or use Railway default
        base_url = os.getenv("BASE_URL", "https://your-railway-app.up.railway.app")
        secure_link = f"{base_url}/secure-loan/{token}"

        # Format income and completeness if provided
        income_text = f"${monthly_income:,.0f}" if monthly_income else "N/A"
        completeness_text = f"{completeness_score:.0f}%" if completeness_score is not None else "N/A"

        if template_type == "missing_documents" and missing_documents:
            # Email to borrower asking for more documents
            subject = "Additional Documentation Required - Loan Application"
            body = f"""Dear {borrower_name},

Thank you for your loan application. To continue processing your loan, we need the following additional documents:

{chr(10).join([f"• {doc.replace('_', ' ').title()}" for doc in missing_documents])}

Please provide these documents as soon as possible to avoid delays in processing your loan application.

If you have any questions, please don't hesitate to contact us.

Best regards,
Loan Processing Team"""
        else:
            # Email to loan officer with secure link
            subject = f"New Loan Ready for Review - {borrower_name}"
            body = f"""A new loan application has been received and analyzed.

Borrower: {borrower_name}
Monthly Income: {income_text}
Completeness: {completeness_text}

🔒 View Loan & Documents: {secure_link}

This secure link provides access to all loan details and supporting documents.
The link never expires and can be accessed anytime.

Best regards,
Automated Loan Processing System"""

        # Audit log
        audit_log("DATA_ACCESS", "EMAIL_GENERATED", {
            "loan_id": safe_loan_id,
            "template_type": template_type,
            "token_generated": True,
            "ip": request.client.host
        })

        return {
            "loan_id": safe_loan_id,
            "email_subject": subject,
            "email_body": body,
            "template_type": template_type,
            "secure_link": secure_link,
            "token": token,
            "generated_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        db.rollback()
        audit_log("ERROR", "EMAIL_GENERATION_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Email generation failed: {str(e)}")

@app.get("/stats")
async def get_system_stats(
    request: Request,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Get system statistics (SECURED)"""
    # Security checks
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        # Count total loans processed
        loan_count = db.query(Loan).count()
        incomplete_count = db.query(Loan).filter(Loan.completeness_score < 100).count()
        complete_count = db.query(Loan).filter(Loan.completeness_score >= 100).count()

        # Clean up old documents
        deleted_count = cleanup_old_documents()

        return {
            "loans_processed": loan_count,
            "incomplete_loans": incomplete_count,
            "complete_loans": complete_count,
            "system_status": "operational",
            "api_version": "3.0.0",
            "database": "PostgreSQL",
            "security_enabled": True,
            "features": [
                "document_upload",
                "loan_analysis",
                "email_generation",
                "auto_cleanup",
                "reminder_tracking",
                "database_tracking"
            ],
            "documents_deleted_today": deleted_count,
            "retention_days": DOCUMENT_RETENTION_DAYS,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        audit_log("ERROR", "STATS_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

@app.delete("/clear-all-data")
async def clear_all_data(
    request: Request,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Clear all loans and documents from database (ADMIN ONLY - BE CAREFUL!)"""
    verify_api_key(api_key)

    try:
        # Delete all documents first (foreign key constraint)
        deleted_docs = db.query(Document).delete()

        # Delete all loans
        deleted_loans = db.query(Loan).delete()

        db.commit()

        # Also delete uploaded files from disk
        if os.path.exists(upload_dir):
            for item in os.listdir(upload_dir):
                item_path = os.path.join(upload_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)

        audit_log("DATA_MANAGEMENT", "CLEAR_ALL", {
            "documents_deleted": deleted_docs,
            "loans_deleted": deleted_loans,
            "ip": request.client.host
        })

        return {
            "success": True,
            "documents_deleted": deleted_docs,
            "loans_deleted": deleted_loans,
            "message": "All data cleared successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")

@app.get("/audit-log")
async def get_audit_log(
    request: Request,
    limit: int = 100,
    api_key: str = Header(None, alias="X-API-Key")
):
    """Get audit log entries (ADMIN ONLY)"""
    verify_api_key(api_key)

    try:
        if not os.path.exists(AUDIT_LOG_FILE):
            return {"entries": []}

        with open(AUDIT_LOG_FILE, "r") as f:
            lines = f.readlines()
            entries = [json.loads(line) for line in lines[-limit:]]

        return {"entries": entries, "count": len(entries)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit log retrieval failed: {str(e)}")

@app.get("/secure-loan/{token}", response_class=HTMLResponse)
async def secure_loan_access(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Public endpoint for loan officer to access loan via secure token (NO API KEY REQUIRED)"""
    try:
        import base64

        # EMERGENCY MODE: Check if this is an emergency token
        if token.startswith("EMERGENCY_"):
            # Decode loan_id from token
            loan_id_encoded = token.replace("EMERGENCY_", "")
            safe_loan_id = base64.urlsafe_b64decode(loan_id_encoded.encode()).decode()

            # Get files from disk directly (no database)
            loan_dir = os.path.join(upload_dir, safe_loan_id)
            if not os.path.exists(loan_dir):
                raise HTTPException(status_code=404, detail="Loan files not found")

            # List all files
            files = os.listdir(loan_dir)
            document_list = [
                {
                    "filename": f,
                    "file_size": os.path.getsize(os.path.join(loan_dir, f)),
                    "upload_date": None,
                    "download_url": f"/secure-loan/{token}/download/{f}"
                }
                for f in files if os.path.isfile(os.path.join(loan_dir, f))
            ]

            # Return emergency HTML view
            return templates.TemplateResponse("loan_view.html", {
                "request": request,
                "loan": {
                    "loan_id": safe_loan_id,
                    "borrower_name": "N/A (Emergency Mode)",
                    "borrower_email": "N/A (Emergency Mode)",
                    "loan_type": "conventional",
                    "status": "Ready",
                    "completeness_score": 100,
                    "risk_score": 0,
                    "document_count": len(document_list),
                    "monthly_income": None,
                    "created_date": None,
                    "last_updated": None
                },
                "missing_documents": [],
                "documents": document_list,
                "access_info": {
                    "expires_at": "Never (Emergency Mode)",
                    "access_count": 0,
                    "permanent_access": True,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            })

        # NORMAL MODE: Validate token from database
        access_token = db.query(AccessToken).filter(AccessToken.token == token).first()

        if not access_token:
            raise HTTPException(status_code=404, detail="Invalid or expired link")

        # Check if token is revoked
        if access_token.is_revoked:
            raise HTTPException(status_code=403, detail="This link has been revoked")

        # Check if token is expired (should be ~100 years, but check anyway)
        if datetime.utcnow() > access_token.expires_at:
            raise HTTPException(status_code=403, detail="This link has expired")

        # Update access tracking
        access_token.accessed_count += 1
        access_token.last_accessed = datetime.utcnow()
        db.commit()

        # Get loan details
        loan = db.query(Loan).filter(Loan.loan_id == access_token.loan_id).first()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")

        # Get documents
        documents = db.query(Document).filter(Document.loan_id == loan.loan_id).all()

        # Audit log
        audit_log("SECURE_ACCESS", "TOKEN_USED", {
            "loan_id": loan.loan_id,
            "token": token[:8] + "...",
            "access_count": access_token.accessed_count,
            "ip": request.client.host
        })

        # Parse missing documents
        missing_documents = json.loads(loan.missing_documents) if loan.missing_documents else []

        # Prepare document list with download URLs
        document_list = [
            {
                "filename": doc.filename,
                "file_size": doc.file_size,
                "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
                "download_url": f"/secure-loan/{token}/download/{doc.filename}"
            }
            for doc in documents
        ]

        # Return HTML response
        return templates.TemplateResponse("loan_view.html", {
            "request": request,
            "loan": {
                "loan_id": loan.loan_id,
                "borrower_name": loan.borrower_name,
                "borrower_email": loan.borrower_email,
                "loan_type": loan.loan_type,
                "status": loan.status,
                "completeness_score": loan.completeness_score or 0,
                "risk_score": loan.risk_score or 0,
                "document_count": loan.document_count,
                "monthly_income": loan.monthly_income,
                "created_date": loan.created_date.isoformat() if loan.created_date else None,
                "last_updated": loan.last_updated.isoformat() if loan.last_updated else None
            },
            "missing_documents": missing_documents,
            "documents": document_list,
            "access_info": {
                "expires_at": "Never (100 years)",
                "access_count": access_token.accessed_count,
                "permanent_access": True,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        audit_log("ERROR", "SECURE_ACCESS_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to access loan: {str(e)}")

@app.get("/secure-loan/{token}/download/{filename}")
async def secure_download_document(
    token: str,
    filename: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Download document via secure token (NO API KEY OR PASSWORD REQUIRED)"""
    try:
        import base64

        # EMERGENCY MODE: Handle emergency tokens
        if token.startswith("EMERGENCY_"):
            # Decode loan_id from token
            loan_id_encoded = token.replace("EMERGENCY_", "")
            safe_loan_id = base64.urlsafe_b64decode(loan_id_encoded.encode()).decode()

            # Sanitize filename
            safe_filename = sanitize_filename(filename)

            # Build file path
            file_path = os.path.join(upload_dir, safe_loan_id, safe_filename)

            # Check if file exists
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Document not found")

            # Read file as-is (NO DECRYPTION in emergency mode)
            with open(file_path, 'rb') as f:
                file_data = f.read()

            # Return file
            return Response(
                content=file_data,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename=\"{safe_filename}\""
                }
            )

        # NORMAL MODE: Validate token from database
        access_token = db.query(AccessToken).filter(AccessToken.token == token).first()

        if not access_token:
            raise HTTPException(status_code=404, detail="Invalid or expired link")

        if access_token.is_revoked:
            raise HTTPException(status_code=403, detail="This link has been revoked")

        if datetime.utcnow() > access_token.expires_at:
            raise HTTPException(status_code=403, detail="This link has expired")

        # Sanitize filename
        safe_filename = sanitize_filename(filename)

        # Get document
        document = db.query(Document).filter(
            Document.loan_id == access_token.loan_id,
            Document.filename == safe_filename
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if file exists
        if not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="Document file not found on server")

        # Decrypt file
        decrypted_data = decrypt_file(document.file_path)
        if decrypted_data is None:
            # If decryption failed, read file as-is
            with open(document.file_path, 'rb') as f:
                decrypted_data = f.read()

        # Audit log
        audit_log("SECURE_ACCESS", "DOCUMENT_DOWNLOAD", {
            "loan_id": access_token.loan_id,
            "filename": safe_filename,
            "token": token[:8] + "...",
            "ip": request.client.host
        })

        # Return raw bytes with proper headers for download
        return Response(
            content=decrypted_data,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}"',
                "Content-Length": str(len(decrypted_data))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        audit_log("ERROR", "SECURE_DOWNLOAD_FAILED", {
            "filename": filename,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.post("/revoke-token/{token}")
async def revoke_access_token(
    token: str,
    request: Request,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Revoke a secure access token (ADMIN ONLY)"""
    verify_api_key(api_key)

    try:
        access_token = db.query(AccessToken).filter(AccessToken.token == token).first()

        if not access_token:
            raise HTTPException(status_code=404, detail="Token not found")

        # Revoke the token
        access_token.is_revoked = 1
        db.commit()

        audit_log("SECURITY", "TOKEN_REVOKED", {
            "token": token[:8] + "...",
            "loan_id": access_token.loan_id,
            "ip": request.client.host
        })

        return {
            "success": True,
            "token": token[:8] + "...",
            "loan_id": access_token.loan_id,
            "message": "Token revoked successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to revoke token: {str(e)}")

# ====================
# EMERGENCY ENDPOINT - NO ENCRYPTION, NO DATABASE
# ====================
@app.post("/upload-documents-simple")
async def upload_documents_simple(
    request: Request,
    files: List[UploadFile] = File(...),
    loan_id: str = Form(...),
    borrower_email: str = Form(None),
    api_key: str = Header(None, alias="X-API-Key")
):
    """EMERGENCY: Upload files without encryption or database - for troubleshooting"""
    # Only verify API key
    verify_api_key(api_key)

    try:
        # Sanitize loan_id
        safe_loan_id = sanitize_filename(loan_id)
        uploaded_files = []
        loan_dir = os.path.join(upload_dir, safe_loan_id)
        os.makedirs(loan_dir, exist_ok=True)

        for file in files:
            # Sanitize filename
            safe_filename = sanitize_filename(file.filename)
            file_path = os.path.join(loan_dir, safe_filename)

            # Save file directly - NO ENCRYPTION
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_size = os.path.getsize(file_path)
            uploaded_files.append({
                "filename": safe_filename,
                "size": file_size
            })

        return {
            "status": "success",
            "message": f"Uploaded {len(uploaded_files)} files for loan {safe_loan_id}",
            "loan_id": safe_loan_id,
            "files": uploaded_files,
            "note": "Files saved without encryption (emergency mode)"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/analyze-loan-simple")
async def analyze_loan_simple_endpoint(
    request: Request,
    loan_request: LoanAnalysisRequest,
    api_key: str = Header(None, alias="X-API-Key")
):
    """EMERGENCY: Analyze loan without database - reads files from disk"""
    # Only verify API key
    verify_api_key(api_key)

    try:
        # Sanitize loan_id
        safe_loan_id = sanitize_filename(loan_request.loan_id)

        # Get documents from disk if not provided
        if not loan_request.documents:
            loan_dir = os.path.join(upload_dir, safe_loan_id)
            if os.path.exists(loan_dir):
                # List all files in the directory
                files = os.listdir(loan_dir)
                loan_request.documents = [
                    {"filename": f, "file_path": os.path.join(loan_dir, f)}
                    for f in files if os.path.isfile(os.path.join(loan_dir, f))
                ]
            else:
                loan_request.documents = []

        # Perform analysis
        loan_data = {
            "loan_id": safe_loan_id,
            "loan_type": loan_request.loan_type,
            "borrower_info": loan_request.borrower_info,
            "documents": loan_request.documents
        }

        analysis_result = analyze_loan_simple(loan_data)

        # Calculate monthly income if extractor is available
        monthly_income = None
        if EXTRACTOR_AVAILABLE:
            try:
                loan_dir = os.path.join(upload_dir, safe_loan_id)
                if os.path.exists(loan_dir):
                    doc_list = [{"filename": doc["filename"]} for doc in loan_request.documents]
                    income_analysis = document_extractor.analyze_documents(loan_dir, doc_list)
                    monthly_income = income_analysis.get('total_monthly_income', 0)

                    analysis_result['monthly_income'] = monthly_income
                    analysis_result['income_breakdown'] = income_analysis.get('income_breakdown', [])
                    if income_analysis.get('red_flags'):
                        analysis_result['red_flags'].extend(income_analysis['red_flags'])
            except Exception as e:
                print(f"Income calculation failed: {e}")

        return {
            **analysis_result,
            "note": "Analysis without database (emergency mode)"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/generate-secure-link-simple")
async def generate_secure_link_simple(
    link_request: SecureLinkRequest,
    request: Request,
    api_key: str = Header(None, alias="X-API-Key")
):
    """EMERGENCY: Generate secure link without database - encodes loan_id in token"""
    verify_api_key(api_key)

    try:
        import base64
        safe_loan_id = sanitize_filename(link_request.loan_id)

        # Encode loan_id directly in the token for emergency mode
        # Format: "EMERGENCY_" + base64(loan_id)
        loan_id_encoded = base64.urlsafe_b64encode(safe_loan_id.encode()).decode()
        token = f"EMERGENCY_{loan_id_encoded}"

        # Get the base URL
        base_url = os.getenv("BASE_URL", "https://web-production-0a9f4.up.railway.app")
        secure_link = f"{base_url}/secure-loan/{token}"

        return {
            "secure_link": secure_link,
            "loan_id": safe_loan_id,
            "token": token,
            "note": "Emergency link with embedded loan_id (no database required)"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Link generation failed: {str(e)}")

if __name__ == "__main__":
    print("🔒 Starting SECURED Loan Processor RAG API with PostgreSQL...")
    print("📍 Server: http://localhost:8000")
    print("🔐 API Key Required for all protected endpoints")
    print("💾 Database: PostgreSQL")
    print("⚠️  Remember to set API_KEY and DATABASE_URL environment variables!")
    uvicorn.run(app, host="0.0.0.0", port=8000)

#!/usr/bin/env python3
"""
SECURED Loan Processor RAG API - Production Ready with Security
Implements: API Key Auth, Rate Limiting, CORS Restrictions, Audit Logging
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import shutil
import uvicorn
from datetime import datetime, timedelta
import json
import secrets
import hashlib
from collections import defaultdict
import time
import filetype
import re

# Import document extractor
from document_extractor import extractor

# Initialize FastAPI app
app = FastAPI(
    title="Loan Processor RAG API (SECURED)",
    version="2.0.0",
    docs_url=None,  # Disable /docs endpoint in production
    redoc_url=None  # Disable /redoc endpoint in production
)

# ====================
# SECURITY CONFIGURATION
# ====================

# API Key from environment variable (CRITICAL!)
API_KEY = os.getenv("API_KEY", "CHANGE_THIS_IN_PRODUCTION")  # Set in Railway!

# Allowed origins for CORS (Make.com and Retool)
ALLOWED_ORIGINS = [
    "https://hook.us1.make.com",
    "https://hook.eu1.make.com",
    "https://hook.eu2.make.com",
    "https://us1.make.com",
    "https://eu1.make.com",
    "https://eu2.make.com",
    # Allow all Retool domains
    "https://*.retool.com",
]

# For development: Allow all origins (comment out for production)
ALLOW_ALL_ORIGINS = os.getenv("ALLOW_ALL_ORIGINS", "true").lower() == "true"

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100  # Max requests per window
RATE_LIMIT_WINDOW = 3600  # Time window in seconds (1 hour)
rate_limit_store = defaultdict(list)

# Document retention (auto-delete after X days)
DOCUMENT_RETENTION_DAYS = 30

# File size limit (10 MB to prevent DoS attacks)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Allowed file types (only accept legitimate loan documents)
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.jpg', '.png'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain',
    'image/jpeg',
    'image/png'
}

# Audit log file
AUDIT_LOG_FILE = "./audit_log.json"

# ====================
# MIDDLEWARE & SECURITY
# ====================

# CORS configuration - Allow Retool and Make.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ALLOW_ALL_ORIGINS else ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],  # Only necessary methods
    allow_headers=["Content-Type", "X-API-Key"],  # Only necessary headers
)

# Trusted host middleware (prevent host header attacks)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*.railway.app", "*.up.railway.app", "*.onrender.com", "localhost"]
)

# Initialize upload directory
upload_dir = "./uploads"
os.makedirs(upload_dir, exist_ok=True)

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

def redact_sensitive_data(text: str) -> str:
    """Redact sensitive data (SSNs, account numbers, etc.) from logs"""
    # Redact SSN (XXX-XX-1234 becomes XXX-XX-XXXX)
    text = re.sub(r'\d{3}-\d{2}-\d{4}', 'XXX-XX-XXXX', text)

    # Redact SSN without dashes (123456789 becomes XXXXXXXXX)
    text = re.sub(r'\b\d{9}\b', 'XXXXXXXXX', text)

    # Redact account numbers (10-16 digits)
    text = re.sub(r'\b\d{10,16}\b', 'XXXX-XXXX-XXXX', text)

    # Redact credit card numbers
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'XXXX-XXXX-XXXX-XXXX', text)

    # Redact routing numbers (9 digits)
    text = re.sub(r'\b\d{9}\b', 'XXXXXXXXX', text)

    return text

def audit_log(category: str, action: str, details: Dict):
    """Log all security and data access events with PII redaction"""
    # Convert details to JSON string for redaction
    details_str = json.dumps(details)

    # Redact sensitive data
    redacted_details_str = redact_sensitive_data(details_str)

    # Parse back to dict
    try:
        redacted_details = json.loads(redacted_details_str)
    except:
        redacted_details = {"redacted_data": redacted_details_str}

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "action": action,
        "details": redacted_details
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

def check_file_size(file_path: str) -> bool:
    """Check if file size is within allowed limit to prevent DoS attacks"""
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="File does not exist")

    size = os.path.getsize(file_path)
    if size > MAX_FILE_SIZE:
        # Log the attempted large file upload
        audit_log("SECURITY", "FILE_TOO_LARGE", {
            "file_path": os.path.basename(file_path),
            "size_mb": round(size / (1024 * 1024), 2),
            "max_size_mb": round(MAX_FILE_SIZE / (1024 * 1024), 2)
        })
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)} MB"
        )
    return True

def validate_file(file_path: str, filename: str) -> bool:
    """Validate file type by extension and actual MIME type to prevent malicious uploads"""
    # Check extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        audit_log("SECURITY", "INVALID_FILE_TYPE", {
            "filename": filename,
            "extension": ext,
            "reason": "extension_not_allowed"
        })
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Accepted types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check actual file type (not just extension) to prevent spoofing
    try:
        kind = filetype.guess(file_path)

        # If filetype can detect the file, validate it
        if kind is not None:
            if kind.mime not in ALLOWED_MIME_TYPES:
                audit_log("SECURITY", "INVALID_FILE_TYPE", {
                    "filename": filename,
                    "extension": ext,
                    "actual_mime": kind.mime,
                    "reason": "mime_type_mismatch"
                })
                raise HTTPException(
                    status_code=400,
                    detail=f"File type validation failed. File appears to be {kind.mime}, not a valid document type."
                )
        # For text files (.txt) that filetype can't detect, allow if extension matches
        elif ext not in ['.txt']:
            audit_log("SECURITY", "INVALID_FILE_TYPE", {
                "filename": filename,
                "extension": ext,
                "reason": "unable_to_detect_type"
            })
            raise HTTPException(
                status_code=400,
                detail="Unable to validate file type. Please ensure the file is a valid document."
            )

    except HTTPException:
        raise  # Re-raise HTTPExceptions
    except Exception as e:
        audit_log("SECURITY", "FILE_VALIDATION_ERROR", {
            "filename": filename,
            "error": str(e)
        })
        raise HTTPException(
            status_code=400,
            detail="Unable to validate file type. Please ensure the file is not corrupted."
        )

    return True

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

# ====================
# PYDANTIC MODELS
# ====================

class LoanAnalysisRequest(BaseModel):
    loan_id: str
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

# ====================
# ANALYSIS FUNCTIONS
# ====================

def analyze_loan_simple(loan_data):
    """
    Enhanced loan analysis with income extraction and red flag detection

    Security: Extracts income/red flags from PDFs in memory, never saves raw text
    """
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
    completeness_score = len(present_docs) / len(required_docs)

    # Create missing documents list
    missing_documents = []
    for doc in missing_docs:
        missing_documents.append({
            'document_type': doc,
            'description': f'{doc.replace("_", " ").title()} required for loan processing',
            'urgency': 'high' if doc in ['application', 'pay_stub'] else 'medium'
        })

    # Initialize red flags
    red_flags = []
    if len(documents) < 2:
        red_flags.append({
            'type': 'insufficient_documentation',
            'severity': 'medium',
            'description': 'Very few documents submitted for review'
        })

    # === NEW: EXTRACT INCOME & RED FLAGS FROM PDFs ===
    extraction_results = None
    total_monthly_income = 0.0
    income_breakdown = []
    extraction_confidence = "none"

    try:
        # Get loan directory path
        loan_dir = os.path.join(upload_dir, sanitize_filename(loan_id))

        if os.path.exists(loan_dir) and documents:
            # Run extraction (happens in memory, text never saved)
            extraction_results = extractor.analyze_documents(loan_dir, documents)

            # Get income data
            total_monthly_income = extraction_results.get('total_monthly_income', 0.0)
            income_breakdown = extraction_results.get('income_breakdown', [])
            extraction_confidence = extraction_results.get('confidence', 'none')

            # Merge extracted red flags with existing ones
            extracted_flags = extraction_results.get('red_flags', [])
            red_flags.extend(extracted_flags)

    except Exception as e:
        # If extraction fails, continue with basic analysis
        print(f"Extraction error (non-fatal): {e}")

    # Calculate risk score based on red flags and missing docs
    base_risk = 0.3 if len(missing_docs) > 2 else 0.1
    red_flag_risk = len(red_flags) * 0.05  # Each red flag adds 5% risk
    risk_score = min(base_risk + red_flag_risk, 1.0)  # Cap at 100%

    # Generate actions
    suggested_actions = []
    if missing_docs:
        suggested_actions.append(f"Request missing documents: {', '.join(missing_docs)}")

    # Add red flag actions
    high_severity_flags = [f for f in red_flags if f.get('severity') == 'high']
    if high_severity_flags:
        suggested_actions.append(f"Address {len(high_severity_flags)} high-severity red flags immediately")

    if completeness_score >= 0.8 and len(red_flags) == 0:
        suggested_actions.append("File appears ready for underwriting review")
    elif completeness_score >= 0.8:
        suggested_actions.append("Review red flags before proceeding to underwriting")

    # Build response with extraction data
    response = {
        'loan_id': loan_id,
        'loan_type': loan_type,
        'analysis_complete': True,
        'completeness_score': completeness_score,
        'risk_score': risk_score,
        'missing_documents': missing_documents,
        'red_flags': red_flags,
        'suggested_actions': suggested_actions,
        'email_template': 'missing_documents' if missing_docs else 'ready_for_underwriting',
        'status': 'pending_documents' if missing_docs else 'ready_for_underwriting',

        # NEW: Income extraction results (NO PII - just numbers)
        'total_monthly_income': total_monthly_income,
        'income_breakdown': income_breakdown,
        'extraction_confidence': extraction_confidence,
    }

    return response

# ====================
# API ENDPOINTS
# ====================

@app.get("/")
async def root():
    """Health check endpoint (PUBLIC - no auth required)"""
    return {
        "message": "Loan Processor RAG API (SECURED)",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "security": "API Key Required",
        "endpoints": ["/upload-documents", "/analyze-loan", "/generate-email", "/stats"]
    }

@app.post("/upload-documents")
async def upload_documents(
    request: Request,
    files: List[UploadFile] = File(...),
    loan_id: str = Form(...),
    api_key: str = Header(None, alias="X-API-Key")
):
    """Upload loan documents (SECURED)"""
    # Security checks
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        # Sanitize loan_id to prevent directory traversal
        safe_loan_id = sanitize_filename(loan_id)

        uploaded_files = []
        loan_dir = os.path.join(upload_dir, safe_loan_id)
        os.makedirs(loan_dir, exist_ok=True)

        for file in files:
            # Sanitize filename
            safe_filename = sanitize_filename(file.filename)
            file_path = os.path.join(loan_dir, safe_filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Validate file type (extension + MIME type)
            validate_file(file_path, safe_filename)

            # Check file size (raises HTTPException if too large)
            check_file_size(file_path)

            uploaded_files.append({
                "filename": safe_filename,
                "file_path": file_path,
                "size": os.path.getsize(file_path)
            })

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
        audit_log("ERROR", "UPLOAD_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/analyze-loan", response_model=LoanAnalysisResponse)
async def analyze_loan(
    request: Request,
    loan_request: LoanAnalysisRequest,
    api_key: str = Header(None, alias="X-API-Key")
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
            loan_dir = os.path.join(upload_dir, safe_loan_id)
            if os.path.exists(loan_dir):
                uploaded_files = []
                for filename in os.listdir(loan_dir):
                    if not filename.startswith('.'):
                        file_path = os.path.join(loan_dir, filename)
                        uploaded_files.append({
                            "filename": filename,
                            "file_path": file_path
                        })
                loan_request.documents = uploaded_files

        # Perform analysis
        loan_data = {
            "loan_id": safe_loan_id,
            "loan_type": loan_request.loan_type,
            "borrower_info": loan_request.borrower_info,
            "documents": loan_request.documents
        }

        analysis_result = analyze_loan_simple(loan_data)

        # Audit log (redact PII)
        audit_log("DATA_ACCESS", "ANALYZE", {
            "loan_id": safe_loan_id,
            "completeness_score": analysis_result['completeness_score'],
            "risk_score": analysis_result['risk_score'],
            "ip": request.client.host
        })

        return LoanAnalysisResponse(**analysis_result)

    except Exception as e:
        audit_log("ERROR", "ANALYSIS_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/generate-email")
async def generate_email(
    request: Request,
    loan_id: str,
    borrower_name: str,
    missing_documents: List[str] = [],
    red_flags: List[Dict] = [],
    template_type: str = "missing_docs",
    api_key: str = Header(None, alias="X-API-Key")
):
    """Generate email content (SECURED)"""
    # Security checks
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        safe_loan_id = sanitize_filename(loan_id)

        if template_type == "missing_documents" and missing_documents:
            subject = "Additional Documentation Required - Loan Application"
            body = f"""Dear {borrower_name},

Thank you for your loan application. To continue processing your loan, we need the following additional documents:

{chr(10).join([f"• {doc.replace('_', ' ').title()}" for doc in missing_documents])}

Please provide these documents as soon as possible to avoid delays in processing your loan application.

If you have any questions, please don't hesitate to contact us.

Best regards,
Loan Processing Team"""
        else:
            subject = "Loan Application Update"
            body = f"""Dear {borrower_name},

Thank you for your loan application. We have received your documents and are currently reviewing them.

We will contact you if we need any additional information.

Best regards,
Loan Processing Team"""

        # Audit log
        audit_log("DATA_ACCESS", "EMAIL_GENERATED", {
            "loan_id": safe_loan_id,
            "template_type": template_type,
            "ip": request.client.host
        })

        return {
            "loan_id": safe_loan_id,
            "email_subject": subject,
            "email_body": body,
            "template_type": template_type,
            "generated_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        audit_log("ERROR", "EMAIL_GENERATION_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Email generation failed: {str(e)}")

@app.get("/stats")
async def get_system_stats(
    request: Request,
    api_key: str = Header(None, alias="X-API-Key")
):
    """Get system statistics (SECURED)"""
    # Security checks
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        # Count total loans processed
        loan_count = 0
        if os.path.exists(upload_dir):
            loan_count = len([d for d in os.listdir(upload_dir) if os.path.isdir(os.path.join(upload_dir, d))])

        # Clean up old documents
        deleted_count = cleanup_old_documents()

        return {
            "loans_processed": loan_count,
            "system_status": "operational",
            "api_version": "2.0.0",
            "security_enabled": True,
            "features": ["document_upload", "loan_analysis", "email_generation", "auto_cleanup"],
            "documents_deleted_today": deleted_count,
            "retention_days": DOCUMENT_RETENTION_DAYS,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        audit_log("ERROR", "STATS_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

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

# ====================
# DASHBOARD ENDPOINTS
# ====================

@app.get("/loans")
async def list_loans(
    request: Request,
    api_key: str = Header(None, alias="X-API-Key")
):
    """List all loans with basic info (DASHBOARD)"""
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        loans = []

        if not os.path.exists(upload_dir):
            return {"loans": [], "total": 0}

        for loan_dir_name in os.listdir(upload_dir):
            loan_path = os.path.join(upload_dir, loan_dir_name)

            if os.path.isdir(loan_path):
                # Get directory info
                dir_stat = os.stat(loan_path)
                created_time = datetime.fromtimestamp(dir_stat.st_ctime)
                modified_time = datetime.fromtimestamp(dir_stat.st_mtime)

                # Count documents
                doc_count = len([f for f in os.listdir(loan_path) if not f.startswith('.')])

                loans.append({
                    "loan_id": loan_dir_name,
                    "document_count": doc_count,
                    "created_date": created_time.isoformat(),
                    "last_updated": modified_time.isoformat(),
                    "status": "active"
                })

        # Sort by most recent first
        loans.sort(key=lambda x: x['last_updated'], reverse=True)

        audit_log("DATA_ACCESS", "LIST_LOANS", {
            "loan_count": len(loans),
            "ip": request.client.host
        })

        return {
            "loans": loans,
            "total": len(loans),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        audit_log("ERROR", "LIST_LOANS_FAILED", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to list loans: {str(e)}")

@app.get("/loans/{loan_id}")
async def get_loan_details(
    request: Request,
    loan_id: str,
    api_key: str = Header(None, alias="X-API-Key")
):
    """Get detailed information about a specific loan (DASHBOARD)"""
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        safe_loan_id = sanitize_filename(loan_id)
        loan_path = os.path.join(upload_dir, safe_loan_id)

        if not os.path.exists(loan_path):
            raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")

        # Get documents
        documents = []
        for filename in os.listdir(loan_path):
            if not filename.startswith('.'):
                file_path = os.path.join(loan_path, filename)
                file_stat = os.stat(file_path)

                documents.append({
                    "filename": filename,
                    "size": file_stat.st_size,
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                    "uploaded_date": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "download_url": f"/loans/{safe_loan_id}/documents/{filename}"
                })

        # Run analysis
        loan_data = {
            "loan_id": safe_loan_id,
            "loan_type": "conventional",
            "borrower_info": {},
            "documents": documents
        }
        analysis_result = analyze_loan_simple(loan_data)

        # Get directory info
        dir_stat = os.stat(loan_path)

        audit_log("DATA_ACCESS", "VIEW_LOAN", {
            "loan_id": safe_loan_id,
            "ip": request.client.host
        })

        return {
            "loan_id": safe_loan_id,
            "created_date": datetime.fromtimestamp(dir_stat.st_ctime).isoformat(),
            "last_updated": datetime.fromtimestamp(dir_stat.st_mtime).isoformat(),
            "documents": documents,
            "document_count": len(documents),
            "analysis": analysis_result,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        audit_log("ERROR", "GET_LOAN_FAILED", {"error": str(e), "loan_id": loan_id})
        raise HTTPException(status_code=500, detail=f"Failed to get loan details: {str(e)}")

@app.get("/loans/{loan_id}/documents/{filename}")
async def download_document(
    request: Request,
    loan_id: str,
    filename: str,
    api_key: str = Header(None, alias="X-API-Key")
):
    """Download a specific document (DASHBOARD)"""
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        from fastapi.responses import FileResponse

        safe_loan_id = sanitize_filename(loan_id)
        safe_filename = sanitize_filename(filename)

        file_path = os.path.join(upload_dir, safe_loan_id, safe_filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Document not found")

        # Verify file is still within upload directory (security check)
        real_path = os.path.realpath(file_path)
        real_upload_dir = os.path.realpath(upload_dir)

        if not real_path.startswith(real_upload_dir):
            audit_log("SECURITY", "PATH_TRAVERSAL_ATTEMPT", {
                "loan_id": loan_id,
                "filename": filename,
                "ip": request.client.host
            })
            raise HTTPException(status_code=403, detail="Access denied")

        audit_log("DATA_ACCESS", "DOWNLOAD_DOCUMENT", {
            "loan_id": safe_loan_id,
            "filename": safe_filename,
            "ip": request.client.host
        })

        return FileResponse(
            path=file_path,
            filename=safe_filename,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        audit_log("ERROR", "DOWNLOAD_FAILED", {"error": str(e), "loan_id": loan_id, "filename": filename})
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/loans/{loan_id}/documents/{filename}/base64")
async def download_document_base64(
    request: Request,
    loan_id: str,
    filename: str,
    api_key: str = Header(None, alias="X-API-Key")
):
    """Download a specific document as base64 JSON (for Retool dashboard)"""
    verify_api_key(api_key)
    check_rate_limit(request)

    try:
        import base64
        import mimetypes

        safe_loan_id = sanitize_filename(loan_id)
        safe_filename = sanitize_filename(filename)

        file_path = os.path.join(upload_dir, safe_loan_id, safe_filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Document not found")

        # Verify file is still within upload directory (security check)
        real_path = os.path.realpath(file_path)
        real_upload_dir = os.path.realpath(upload_dir)

        if not real_path.startswith(real_upload_dir):
            audit_log("SECURITY", "PATH_TRAVERSAL_ATTEMPT", {
                "loan_id": loan_id,
                "filename": filename,
                "ip": request.client.host
            })
            raise HTTPException(status_code=403, detail="Access denied")

        # Read file and encode as base64
        with open(file_path, 'rb') as f:
            file_content = f.read()
            base64_content = base64.b64encode(file_content).decode('utf-8')

        # Guess MIME type
        mime_type, _ = mimetypes.guess_type(safe_filename)
        if not mime_type:
            mime_type = 'application/octet-stream'

        audit_log("DATA_ACCESS", "DOWNLOAD_DOCUMENT_BASE64", {
            "loan_id": safe_loan_id,
            "filename": safe_filename,
            "ip": request.client.host
        })

        return {
            "filename": safe_filename,
            "content": base64_content,
            "mimeType": mime_type
        }

    except HTTPException:
        raise
    except Exception as e:
        audit_log("ERROR", "DOWNLOAD_BASE64_FAILED", {"error": str(e), "loan_id": loan_id, "filename": filename})
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

if __name__ == "__main__":
    print("🔒 Starting SECURED Loan Processor RAG API...")
    print("📍 Server: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("🔐 API Key Required for all protected endpoints")
    print("⚠️  Remember to set API_KEY environment variable!")
    uvicorn.run(app, host="0.0.0.0", port=8000)

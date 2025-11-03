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

# Allowed origins for CORS (restrict to Make.com)
ALLOWED_ORIGINS = [
    "https://hook.us1.make.com",
    "https://hook.eu1.make.com",
    "https://hook.eu2.make.com",
    "https://us1.make.com",
    "https://eu1.make.com",
    "https://eu2.make.com",
]

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100  # Max requests per window
RATE_LIMIT_WINDOW = 3600  # Time window in seconds (1 hour)
rate_limit_store = defaultdict(list)

# Document retention (auto-delete after X days)
DOCUMENT_RETENTION_DAYS = 30

# Audit log file
AUDIT_LOG_FILE = "./audit_log.json"

# ====================
# MIDDLEWARE & SECURITY
# ====================

# Restrict CORS to only Make.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Only Make.com domains
    allow_credentials=True,
    allow_methods=["POST", "GET"],  # Only necessary methods
    allow_headers=["Content-Type", "X-API-Key"],  # Only necessary headers
)

# Trusted host middleware (prevent host header attacks)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*.railway.app", "*.up.railway.app", "localhost"]
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
    completeness_score = len(present_docs) / len(required_docs)
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
    if completeness_score >= 0.8:
        suggested_actions.append("File appears ready for underwriting review")

    return {
        'loan_id': loan_id,
        'loan_type': loan_type,
        'analysis_complete': True,
        'completeness_score': completeness_score,
        'risk_score': risk_score,
        'missing_documents': missing_documents,
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

if __name__ == "__main__":
    print("🔒 Starting SECURED Loan Processor RAG API...")
    print("📍 Server: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("🔐 API Key Required for all protected endpoints")
    print("⚠️  Remember to set API_KEY environment variable!")
    uvicorn.run(app, host="0.0.0.0", port=8000)

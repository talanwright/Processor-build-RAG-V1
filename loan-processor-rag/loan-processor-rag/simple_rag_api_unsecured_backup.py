#!/usr/bin/env python3
"""
Simplified RAG API for Loan Processing - Ready for Make.com Integration
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import shutil
import uvicorn
from datetime import datetime
import json

# Initialize FastAPI app
app = FastAPI(title="Loan Processor RAG API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize upload directory
upload_dir = "./uploads"
os.makedirs(upload_dir, exist_ok=True)

# Pydantic models
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

# Simple mock analysis functions
def analyze_loan_simple(loan_data):
    """Simplified loan analysis"""
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

    present_docs = list(set(present_docs))  # Remove duplicates
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

    # Create red flags (simplified)
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

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Loan Processor RAG API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "endpoints": ["/upload-documents", "/analyze-loan", "/generate-email", "/stats"]
    }

@app.post("/upload-documents")
async def upload_documents(files: List[UploadFile] = File(...), loan_id: str = Form(...)):
    """Upload loan documents"""
    try:
        uploaded_files = []
        loan_dir = os.path.join(upload_dir, loan_id)
        os.makedirs(loan_dir, exist_ok=True)

        for file in files:
            file_path = os.path.join(loan_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            uploaded_files.append({
                "filename": file.filename,
                "file_path": file_path,
                "size": os.path.getsize(file_path)
            })

        return {
            "loan_id": loan_id,
            "uploaded_files": uploaded_files,
            "total_files": len(uploaded_files),
            "upload_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/analyze-loan", response_model=LoanAnalysisResponse)
async def analyze_loan(request: LoanAnalysisRequest):
    """Main loan analysis endpoint - This is what Make.com will call"""
    try:
        # Check for uploaded files if documents not provided
        if not request.documents:
            loan_dir = os.path.join(upload_dir, request.loan_id)
            if os.path.exists(loan_dir):
                uploaded_files = []
                for filename in os.listdir(loan_dir):
                    if not filename.startswith('.'):  # Skip hidden files
                        file_path = os.path.join(loan_dir, filename)
                        uploaded_files.append({
                            "filename": filename,
                            "file_path": file_path
                        })
                request.documents = uploaded_files

        # Perform analysis
        loan_data = {
            "loan_id": request.loan_id,
            "loan_type": request.loan_type,
            "borrower_info": request.borrower_info,
            "documents": request.documents
        }

        analysis_result = analyze_loan_simple(loan_data)

        return LoanAnalysisResponse(**analysis_result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/generate-email")
async def generate_email(loan_id: str, borrower_name: str, missing_documents: List[str] = [], red_flags: List[Dict] = [], template_type: str = "missing_docs"):
    """Generate email content for borrower communication"""
    try:
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

        return {
            "loan_id": loan_id,
            "email_subject": subject,
            "email_body": body,
            "template_type": template_type,
            "generated_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email generation failed: {str(e)}")

@app.get("/loan-status/{loan_id}")
async def get_loan_status(loan_id: str):
    """Get loan processing status"""
    try:
        loan_dir = os.path.join(upload_dir, loan_id)

        if not os.path.exists(loan_dir):
            raise HTTPException(status_code=404, detail="Loan not found")

        files = [f for f in os.listdir(loan_dir) if not f.startswith('.')]

        return {
            "loan_id": loan_id,
            "documents_uploaded": len(files),
            "last_updated": datetime.fromtimestamp(os.path.getmtime(loan_dir)).isoformat(),
            "files": files
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        # Count total loans processed
        loan_count = 0
        if os.path.exists(upload_dir):
            loan_count = len([d for d in os.listdir(upload_dir) if os.path.isdir(os.path.join(upload_dir, d))])

        return {
            "loans_processed": loan_count,
            "system_status": "operational",
            "api_version": "1.0.0",
            "features": ["document_upload", "loan_analysis", "email_generation"],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Loan Processor RAG API...")
    print("📍 Server: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("🔍 Ready for Make.com integration!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
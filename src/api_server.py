from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import shutil
import uvicorn
from datetime import datetime
import json

from document_processor import DocumentProcessor
from vector_database import VectorDatabase
from loan_analyzer import LoanAnalyzer

# Initialize FastAPI app
app = FastAPI(title="Loan Processor RAG API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
upload_dir = "./uploads"
os.makedirs(upload_dir, exist_ok=True)

vector_db = VectorDatabase()
analyzer = LoanAnalyzer(vector_db)

# Load knowledge base on startup
@app.on_event("startup")
async def startup_event():
    knowledge_base_path = "./knowledge_base"
    if os.path.exists(knowledge_base_path):
        vector_db.add_knowledge_base(knowledge_base_path)
        print("Knowledge base loaded successfully!")
    else:
        print("Warning: Knowledge base directory not found")

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

class EmailGenerationRequest(BaseModel):
    loan_id: str
    borrower_name: str
    missing_documents: List[str]
    red_flags: List[Dict]
    template_type: Optional[str] = "missing_docs"

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Loan Processor RAG API",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload-documents")
async def upload_documents(
    files: List[UploadFile] = File(...),
    loan_id: str = Form(...),
    borrower_email: Optional[str] = Form(None)
):
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
            "borrower_email": borrower_email,
            "uploaded_files": uploaded_files,
            "total_files": len(uploaded_files),
            "upload_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/upload-document")
async def upload_single_document(
    file: UploadFile = File(...),
    loan_id: str = Form(...),
    borrower_email: Optional[str] = Form(None)
):
    """Upload a single loan document (for Make.com iterator)"""
    try:
        loan_dir = os.path.join(upload_dir, loan_id)
        os.makedirs(loan_dir, exist_ok=True)

        file_path = os.path.join(loan_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "loan_id": loan_id,
            "borrower_email": borrower_email,
            "filename": file.filename,
            "file_path": file_path,
            "size": os.path.getsize(file_path),
            "upload_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/analyze-loan", response_model=LoanAnalysisResponse)
async def analyze_loan(request: LoanAnalysisRequest):
    """Main loan analysis endpoint - This is what Make.com will call"""
    try:
        # Convert request to format expected by analyzer
        loan_data = {
            "loan_id": request.loan_id,
            "loan_type": request.loan_type,
            "borrower_info": request.borrower_info,
            "documents": request.documents
        }

        # If documents don't have file_path, look in uploads directory
        if not any("file_path" in doc for doc in request.documents):
            loan_dir = os.path.join(upload_dir, request.loan_id)
            if os.path.exists(loan_dir):
                uploaded_files = []
                for filename in os.listdir(loan_dir):
                    file_path = os.path.join(loan_dir, filename)
                    uploaded_files.append({
                        "file_path": file_path,
                        "filename": filename
                    })
                loan_data["documents"] = uploaded_files

        # Perform analysis
        analysis_result = analyzer.analyze_loan_file(loan_data)

        # Determine email template based on analysis
        email_template = _determine_email_template(analysis_result)

        # Determine status
        status = _determine_loan_status(analysis_result)

        # Format response for Make.com
        response = LoanAnalysisResponse(
            loan_id=analysis_result["loan_id"],
            loan_type=analysis_result["loan_type"],
            analysis_complete=True,
            completeness_score=analysis_result["completeness_score"],
            risk_score=analysis_result["risk_score"],
            missing_documents=analysis_result["missing_documents"],
            red_flags=analysis_result["red_flag_analysis"]["red_flags"],
            suggested_actions=analysis_result["suggested_actions"],
            email_template=email_template,
            status=status
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/generate-email")
async def generate_email(request: EmailGenerationRequest):
    """Generate email content for borrower communication"""
    try:
        email_content = _generate_email_content(
            request.borrower_name,
            request.missing_documents,
            request.red_flags,
            request.template_type
        )

        return {
            "loan_id": request.loan_id,
            "email_subject": email_content["subject"],
            "email_body": email_content["body"],
            "template_type": request.template_type,
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

        files = os.listdir(loan_dir)

        return {
            "loan_id": loan_id,
            "documents_uploaded": len(files),
            "last_updated": datetime.fromtimestamp(os.path.getmtime(loan_dir)).isoformat(),
            "files": files
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/knowledge-base/search")
async def search_knowledge_base(query: str, collection: Optional[str] = None):
    """Search the knowledge base"""
    try:
        if collection == "requirements":
            results = vector_db.search_requirements(query)
        elif collection == "compliance":
            results = vector_db.search_compliance(query)
        elif collection == "red_flags":
            results = vector_db.search_red_flags(query)
        else:
            results = vector_db.search_all(query)

        return {
            "query": query,
            "collection": collection or "all",
            "results": results,
            "search_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        stats = vector_db.get_collection_stats()

        # Count total loans processed
        loan_count = 0
        if os.path.exists(upload_dir):
            loan_count = len([d for d in os.listdir(upload_dir) if os.path.isdir(os.path.join(upload_dir, d))])

        return {
            "vector_database": stats,
            "loans_processed": loan_count,
            "system_status": "operational",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

# Helper functions

def _determine_email_template(analysis_result: Dict) -> str:
    """Determine appropriate email template based on analysis"""
    missing_docs = analysis_result.get("missing_documents", [])
    red_flags = analysis_result.get("red_flag_analysis", {}).get("red_flags", [])
    completeness_score = analysis_result.get("completeness_score", 0)

    if len(missing_docs) > 0:
        return "missing_documents"
    elif len(red_flags) > 0:
        return "red_flag_follow_up"
    elif completeness_score >= 0.9:
        return "ready_for_underwriting"
    else:
        return "general_follow_up"

def _determine_loan_status(analysis_result: Dict) -> str:
    """Determine loan processing status"""
    completeness_score = analysis_result.get("completeness_score", 0)
    risk_score = analysis_result.get("risk_score", 1)
    missing_docs = analysis_result.get("missing_documents", [])

    if len(missing_docs) > 0:
        return "pending_documents"
    elif risk_score > 0.7:
        return "requires_review"
    elif completeness_score >= 0.9 and risk_score < 0.3:
        return "ready_for_underwriting"
    else:
        return "in_progress"

def _generate_email_content(borrower_name: str, missing_docs: List[str], red_flags: List[Dict], template_type: str) -> Dict:
    """Generate email content based on template type"""

    templates = {
        "missing_documents": {
            "subject": f"Additional Documentation Required - Loan Application",
            "body": f"""Dear {borrower_name},

Thank you for your loan application. To continue processing your loan, we need the following additional documents:

{_format_missing_docs_list(missing_docs)}

Please provide these documents as soon as possible to avoid delays in processing your loan application.

If you have any questions, please don't hesitate to contact us.

Best regards,
Loan Processing Team"""
        },

        "red_flag_follow_up": {
            "subject": f"Clarification Needed - Loan Application",
            "body": f"""Dear {borrower_name},

While reviewing your loan application, we need clarification on the following items:

{_format_red_flags_list(red_flags)}

Please provide explanations or additional documentation to address these items.

Best regards,
Loan Processing Team"""
        },

        "ready_for_underwriting": {
            "subject": f"Loan Application Update - Moving to Underwriting",
            "body": f"""Dear {borrower_name},

Great news! Your loan application is complete and has been submitted to underwriting for final review.

We will contact you if the underwriter requires any additional information.

Best regards,
Loan Processing Team"""
        }
    }

    return templates.get(template_type, templates["missing_documents"])

def _format_missing_docs_list(missing_docs: List[str]) -> str:
    """Format missing documents list for email"""
    if not missing_docs:
        return "No missing documents"

    formatted_list = []
    for i, doc in enumerate(missing_docs, 1):
        doc_name = doc.replace('_', ' ').title()
        formatted_list.append(f"{i}. {doc_name}")

    return "\n".join(formatted_list)

def _format_red_flags_list(red_flags: List[Dict]) -> str:
    """Format red flags list for email"""
    if not red_flags:
        return "No issues found"

    formatted_list = []
    for i, flag in enumerate(red_flags, 1):
        description = flag.get('description', 'Requires clarification')
        formatted_list.append(f"{i}. {description}")

    return "\n".join(formatted_list)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
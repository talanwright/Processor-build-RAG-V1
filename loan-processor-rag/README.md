# Loan Processor RAG System

## Quick Start

### 1. Setup Virtual Environment
```bash
cd loan-processor-rag
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start the System
```bash
python3 run.py
```

**API will be available at:** `http://localhost:8000`
**Documentation:** `http://localhost:8000/docs`

## Make.com Integration

The RAG system is ready to connect to Make.com! See `MAKE_INTEGRATION_GUIDE.md` for detailed setup instructions.

### Key Integration Points:

**1. Upload Documents:** `POST /upload-documents`
**2. Analyze Loan:** `POST /analyze-loan` (Main endpoint for Make.com)
**3. Generate Email:** `POST /generate-email`

### Example Make.com Flow:
```
Email with Loan Docs → Upload to RAG → Analyze → Generate Response Email → Send to Borrower
```

## What This System Does

✅ **Document Processing** - Extracts text from PDFs, Word docs, and more
✅ **Intelligence** - Identifies missing documents and red flags
✅ **Knowledge Base** - Loan requirements, compliance rules, red flag patterns
✅ **Analysis** - Calculates completeness and risk scores
✅ **Email Generation** - Creates professional responses based on analysis
✅ **Make.com Ready** - RESTful API designed for workflow automation

## For Your Mac Hardware

This system is optimized for your MacBook Air M3 (16GB RAM):
- Uses smaller, efficient models
- Local processing for security
- Lightweight vector database
- CPU-optimized inference

## Security Features

- All data processing stays local
- No cloud APIs for sensitive documents
- Encrypted document storage (when configured)
- GLBA compliance monitoring
- Audit logging capabilities

## Getting Help

- **API Docs:** `http://localhost:8000/docs`
- **System Stats:** `http://localhost:8000/stats`
- **Make.com Setup:** See `MAKE_INTEGRATION_GUIDE.md`
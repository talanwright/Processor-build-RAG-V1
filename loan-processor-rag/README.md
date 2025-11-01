# Loan Processor RAG System

A smart loan document analysis system that automatically processes loan applications, identifies missing documents, and generates professional email responses.

## Features

- **Document Analysis**: Automatically processes PDFs, Word docs, and other loan documents
- **Missing Document Detection**: Identifies what documentation is still needed
- **Risk Assessment**: Calculates completeness and risk scores
- **Email Generation**: Creates professional borrower communications
- **Make.com Integration**: Ready for workflow automation
- **RESTful API**: Easy integration with any system

## Quick Start

### Local Development

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/loan-processor-rag.git
cd loan-processor-rag

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python3 simple_rag_api.py
```

Server will be available at `http://localhost:8000`

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Core Endpoints

### Health Check
```
GET /
```

### Upload Documents
```
POST /upload-documents
Form Data:
- loan_id: string
- files: file(s)
```

### Analyze Loan
```
POST /analyze-loan
{
  "loan_id": "string",
  "borrower_info": {
    "name": "string",
    "email": "string"
  },
  "loan_type": "conventional",
  "documents": [...]
}
```

### Generate Email
```
POST /generate-email?loan_id=string&borrower_name=string&template_type=string
```

## Sample Response

```json
{
  "loan_id": "12345",
  "analysis_complete": true,
  "completeness_score": 0.6,
  "missing_documents": [
    {
      "document_type": "bank_statement",
      "description": "Bank Statement required for loan processing",
      "urgency": "high"
    }
  ],
  "suggested_actions": [
    "Request missing documents: bank_statement, tax_return"
  ],
  "status": "pending_documents"
}
```

## Deployment

### Railway (Recommended)
1. Push to GitHub
2. Connect to Railway.app
3. Auto-deploys with permanent HTTPS URL

### Heroku
```bash
heroku create your-app-name
git push heroku main
```

### Docker
```bash
docker build -t loan-processor .
docker run -p 8000:8000 loan-processor
```

## Document Types Supported

- **Applications**: 1003 forms, loan applications
- **Income**: Pay stubs, W-2s, tax returns
- **Assets**: Bank statements, asset verification
- **Employment**: Employment verification letters
- **Property**: Appraisals, title reports

## Loan Types

- Conventional
- FHA
- VA
- USDA

## Integration Examples

### Make.com Workflow
```
Email Trigger → Upload Docs → Analyze → Generate Response → Send Email
```

### Zapier Integration
```
Gmail → HTTP Request → Email Response
```

### Direct API Usage
```python
import requests

# Analyze loan
response = requests.post("https://your-app.railway.app/analyze-loan", json={
    "loan_id": "test123",
    "borrower_info": {"name": "John Doe", "email": "john@email.com"},
    "loan_type": "conventional"
})

analysis = response.json()
print(f"Missing docs: {analysis['missing_documents']}")
```

## Security Features

- Document encryption support
- API authentication ready
- CORS configuration
- Rate limiting compatible

## Technology Stack

- **Backend**: FastAPI (Python)
- **Document Processing**: PyPDF2, python-docx
- **API**: RESTful with automatic OpenAPI docs
- **Deployment**: Railway, Heroku, Docker ready

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Check the API docs at `/docs`
- Review the deployment guide
- Open an issue on GitHub

---

**Built for modern loan processing workflows** 🚀
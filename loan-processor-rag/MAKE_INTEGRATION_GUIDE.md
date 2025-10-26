# Make.com Integration Guide for Loan Processor RAG

## Overview
This guide explains how to connect your RAG system to Make.com for automated loan processing.

## RAG System Setup

### 1. Start the RAG System
```bash
cd loan-processor-rag
python run.py
```

**Your RAG API will be running at:** `http://localhost:8000`

**API Documentation:** `http://localhost:8000/docs`

---

## Make.com Scenario Setup

### Scenario Flow:
```
Email Trigger → Extract Attachments → Upload to RAG → Analyze Loan → Generate Email → Send Response
```

### 1. Email Trigger Module
**Module:** Gmail/Email - Watch Emails
**Settings:**
- Monitor: Inbox
- Filter: Subject contains "loan" OR "application"
- Mark as read: Yes

### 2. Extract Attachments Module
**Module:** Email - Get Attachments
**Settings:**
- Email ID: From previous module
- Save attachments: Yes

### 3. Upload Documents to RAG
**Module:** HTTP - Make a Request
**Settings:**
- URL: `http://YOUR_LOCAL_IP:8000/upload-documents`
- Method: POST
- Headers: `Content-Type: multipart/form-data`
- Body Type: Multipart/form-data

**Body Fields:**
```
loan_id: {{emailData.messageId}} (or generate unique ID)
files: {{attachments}} (from step 2)
```

### 4. Analyze Loan File
**Module:** HTTP - Make a Request
**Settings:**
- URL: `http://YOUR_LOCAL_IP:8000/analyze-loan`
- Method: POST
- Headers: `Content-Type: application/json`

**JSON Body:**
```json
{
  "loan_id": "{{emailData.messageId}}",
  "borrower_info": {
    "name": "{{emailData.fromName}}",
    "email": "{{emailData.fromEmail}}"
  },
  "loan_type": "conventional",
  "documents": []
}
```

### 5. Generate Email Response
**Module:** HTTP - Make a Request
**Settings:**
- URL: `http://YOUR_LOCAL_IP:8000/generate-email`
- Method: POST
- Headers: `Content-Type: application/json`

**JSON Body:**
```json
{
  "loan_id": "{{analyzeResult.loan_id}}",
  "borrower_name": "{{emailData.fromName}}",
  "missing_documents": "{{analyzeResult.missing_documents}}",
  "red_flags": "{{analyzeResult.red_flags}}",
  "template_type": "{{analyzeResult.email_template}}"
}
```

### 6. Send Email Response
**Module:** Gmail - Send an Email
**Settings:**
- To: `{{emailData.fromEmail}}`
- Subject: `{{emailResponse.email_subject}}`
- Content: `{{emailResponse.email_body}}`
- In reply to: `{{emailData.messageId}}`

---

## Key API Endpoints for Make.com

### 1. Upload Documents
**POST** `/upload-documents`

**Form Data:**
- `loan_id`: Unique identifier
- `files`: Document files

**Response:**
```json
{
  "loan_id": "12345",
  "uploaded_files": [...],
  "total_files": 3
}
```

### 2. Analyze Loan (Main Endpoint)
**POST** `/analyze-loan`

**Request:**
```json
{
  "loan_id": "12345",
  "borrower_info": {
    "name": "John Doe",
    "email": "john@email.com"
  },
  "loan_type": "conventional"
}
```

**Response:**
```json
{
  "loan_id": "12345",
  "analysis_complete": true,
  "completeness_score": 0.75,
  "missing_documents": [
    {
      "document_type": "pay_stub",
      "description": "Recent pay stub required",
      "urgency": "high"
    }
  ],
  "red_flags": [
    {
      "type": "large_deposit",
      "severity": "high",
      "description": "Large deposit requiring explanation"
    }
  ],
  "suggested_actions": [
    "Request missing pay stub",
    "Clarify large deposit source"
  ],
  "email_template": "missing_documents",
  "status": "pending_documents"
}
```

### 3. Generate Email
**POST** `/generate-email`

**Response:**
```json
{
  "loan_id": "12345",
  "email_subject": "Additional Documentation Required",
  "email_body": "Dear John Doe, we need...",
  "template_type": "missing_documents"
}
```

---

## Make.com Configuration Tips

### 1. Local Network Access
**Option A: Use ngrok (Recommended for testing)**
```bash
ngrok http 8000
```
Use the ngrok URL in Make.com: `https://abc123.ngrok.io`

**Option B: Direct Local IP**
- Find your local IP: `ipconfig getifaddr en0` (Mac) or `ipconfig` (Windows)
- Use in Make.com: `http://192.168.1.100:8000`
- Ensure firewall allows connections

### 2. Error Handling in Make.com
Add error handling modules:
- **HTTP Response Status**: Check for 200 status
- **Router**: Route based on analysis results
- **Data Store**: Log all loan processing activities

### 3. Conditional Logic
Use Make.com routers to handle different scenarios:

**Route 1:** `completeness_score >= 0.9` → Send "Ready for Underwriting" email
**Route 2:** `missing_documents.length > 0` → Send "Missing Documents" email
**Route 3:** `red_flags.length > 0` → Send to loan officer for review

### 4. Data Storage
Use Make.com Data Store to track:
- Loan processing history
- Document upload timestamps
- Analysis results
- Email communications

---

## Testing the Integration

### 1. Test RAG System Independently
```bash
# Test upload
curl -X POST "http://localhost:8000/upload-documents" \
  -F "loan_id=test123" \
  -F "files=@sample_application.pdf"

# Test analysis
curl -X POST "http://localhost:8000/analyze-loan" \
  -H "Content-Type: application/json" \
  -d '{"loan_id": "test123", "borrower_info": {"name": "Test User"}, "loan_type": "conventional"}'
```

### 2. Test Make.com Scenario
1. Send test email with loan documents
2. Check Make.com execution logs
3. Verify RAG API receives requests
4. Confirm email response is generated

### 3. Monitor Logs
- Make.com: Check scenario execution history
- RAG System: Monitor console output
- API Docs: Use `http://localhost:8000/docs` for testing

---

## Security Considerations

### 1. Network Security
- Use VPN for remote access
- Firewall rules for specific IP ranges
- HTTPS with SSL certificates in production

### 2. Data Protection
- All sensitive data stays local
- Implement access controls
- Regular security audits
- Encrypted document storage

### 3. API Security
- Add API key authentication
- Rate limiting
- Input validation
- Audit logging

---

## Troubleshooting

### Common Issues:

**1. Make.com can't reach RAG API**
- Check local IP address
- Verify firewall settings
- Use ngrok for testing

**2. File upload failures**
- Check file size limits
- Verify file format support
- Monitor disk space

**3. Analysis errors**
- Check document quality
- Verify knowledge base loaded
- Review API error logs

**4. Email generation fails**
- Verify template selection logic
- Check missing documents format
- Review borrower information

---

## Production Deployment

For production use:
1. Deploy RAG system on dedicated server
2. Use proper domain name and SSL
3. Implement authentication and authorization
4. Set up monitoring and alerting
5. Regular backups of loan data
6. Compliance auditing tools

---

## Support

**RAG System Logs:** Check console output when running `python run.py`
**API Documentation:** `http://localhost:8000/docs`
**Make.com Logs:** Scenario execution history
**Test Endpoint:** `http://localhost:8000/stats`
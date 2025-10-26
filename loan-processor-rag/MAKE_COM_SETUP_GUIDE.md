# Make.com Setup Guide for Loan Processor RAG System

## Overview
This guide will walk you through setting up Make.com to automatically process loan applications using your RAG system. When someone emails you loan documents, Make.com will automatically analyze them and send a professional response.

---

## Prerequisites

### 1. Your RAG System Status
✅ **Confirm your RAG API is running:**
- Open `http://localhost:8000` in browser
- Should see: `"status": "running"`
- If not running, start it: `cd "/Users/talanwright/Test RAG/loan-processor-rag" && source venv/bin/activate && python3 simple_rag_api.py`

### 2. Make Your RAG System Accessible to Make.com

**Option A: ngrok (Recommended)**
```bash
# Install ngrok
brew install ngrok

# Start ngrok tunnel
ngrok http 8000
```
**Copy the https URL** (like `https://abc123.ngrok.io`) - you'll use this in Make.com

**Option B: Local Network**
```bash
# Get your local IP
ipconfig getifaddr en0
```
Use `http://YOUR_IP:8000` in Make.com

---

## Make.com Account Setup

### 1. Create Make.com Account
- Go to `https://make.com`
- Sign up for free account
- Verify email

### 2. Connect Email Service
- Click **Apps** in sidebar
- Search for **Gmail** (or your email provider)
- Click **Create a connection**
- Follow OAuth setup to connect your email

---

## Create the Loan Processing Scenario

### Step 1: Create New Scenario
1. Click **Scenarios** in sidebar
2. Click **Create a new scenario**
3. Name it: "Loan Document Processor"

### Step 2: Email Trigger Setup

**Module:** Gmail - Watch Emails
1. Click the **+** button
2. Search and select **Gmail**
3. Choose **Watch Emails**
4. **Connection:** Select your Gmail connection
5. **Settings:**
   - **Folder:** Inbox
   - **Criteria:**
     - Subject contains: `loan` OR `application` OR `mortgage`
     - Has attachment: Yes
   - **Limit:** 10
   - **Mark as read:** Yes

### Step 3: Filter for Loan Emails

**Module:** Filter
1. Click **+** after Gmail module
2. Search and select **Filter**
3. **Condition:**
   ```
   {{1.subject}} contains loan
   OR
   {{1.subject}} contains application
   OR
   {{1.subject}} contains mortgage
   ```

### Step 4: Extract Email Attachments

**Module:** Gmail - Download an Attachment
1. Click **+** after Filter
2. Select **Gmail**
3. Choose **Download an Attachment**
4. **Settings:**
   - **Message ID:** `{{1.id}}`
   - **Attachment ID:** `{{1.attachments[].id}}`
   - **File Name:** `{{1.attachments[].filename}}`

### Step 5: Upload Documents to RAG System

**Module:** HTTP - Make a Request
1. Click **+** after Download Attachment
2. Search and select **HTTP**
3. Choose **Make a Request**
4. **Settings:**
   - **URL:** `YOUR_NGROK_URL/upload-documents` (e.g., `https://abc123.ngrok.io/upload-documents`)
   - **Method:** POST
   - **Headers:**
     ```
     Content-Type: multipart/form-data
     ```
   - **Body Type:** Multipart/form-data
   - **Fields:**
     ```
     loan_id: {{1.id}}
     files: {{3.data}}
     ```

### Step 6: Analyze Loan with RAG System

**Module:** HTTP - Make a Request
1. Click **+** after Upload Documents
2. Select **HTTP** → **Make a Request**
3. **Settings:**
   - **URL:** `YOUR_NGROK_URL/analyze-loan`
   - **Method:** POST
   - **Headers:**
     ```
     Content-Type: application/json
     ```
   - **Body Type:** Raw
   - **Content:**
     ```json
     {
       "loan_id": "{{1.id}}",
       "borrower_info": {
         "name": "{{1.from.name}}",
         "email": "{{1.from.address}}"
       },
       "loan_type": "conventional",
       "documents": []
     }
     ```

### Step 7: Generate Response Email

**Module:** HTTP - Make a Request
1. Click **+** after Analyze Loan
2. Select **HTTP** → **Make a Request**
3. **Settings:**
   - **URL:** `YOUR_NGROK_URL/generate-email`
   - **Method:** POST
   - **Headers:**
     ```
     Content-Type: application/x-www-form-urlencoded
     ```
   - **Body Type:** Form urlencoded
   - **Fields:**
     ```
     loan_id: {{5.loan_id}}
     borrower_name: {{1.from.name}}
     missing_documents: {{5.missing_documents[].document_type}}
     template_type: {{5.email_template}}
     ```

### Step 8: Send Response Email

**Module:** Gmail - Send an Email
1. Click **+** after Generate Response Email
2. Select **Gmail** → **Send an Email**
3. **Settings:**
   - **To:** `{{1.from.address}}`
   - **Subject:** `{{6.email_subject}}`
   - **Content:** `{{6.email_body}}`
   - **In Reply To:** `{{1.id}}`

---

## Advanced Configuration

### Add Router for Different Actions

**Module:** Router
1. Add **Router** after Step 6 (Analyze Loan)
2. Create routes based on analysis results:

**Route 1: Missing Documents**
- **Filter:** `{{5.status}} = "pending_documents"`
- **Action:** Send missing documents email

**Route 2: Ready for Underwriting**
- **Filter:** `{{5.status}} = "ready_for_underwriting"`
- **Action:** Forward to underwriter + send confirmation email

**Route 3: High Risk**
- **Filter:** `{{5.risk_score}} > 0.7`
- **Action:** Send to loan officer for manual review

### Add Data Storage

**Module:** Data Store - Add a Record
1. Add after Analyze Loan step
2. **Data Structure:**
   ```json
   {
     "loan_id": "{{5.loan_id}}",
     "borrower_name": "{{1.from.name}}",
     "borrower_email": "{{1.from.address}}",
     "completeness_score": "{{5.completeness_score}}",
     "risk_score": "{{5.risk_score}}",
     "status": "{{5.status}}",
     "processed_date": "{{now}}",
     "missing_documents": "{{5.missing_documents}}",
     "red_flags": "{{5.red_flags}}"
   }
   ```

### Add Error Handling

**Module:** Error Handler
1. Add to each HTTP request module
2. **Settings:**
   - **Directive:** Resume
   - **Action:** Send notification email to loan officer

---

## Testing Your Scenario

### 1. Test with Sample Email
1. Click **Run once** in Make.com
2. Send yourself a test email with:
   - Subject: "Loan Application - John Doe"
   - Attach a PDF file (any PDF will work for testing)
3. Watch the scenario execute step by step

### 2. Check RAG System Logs
Monitor your terminal where the RAG system is running to see incoming requests.

### 3. Verify Response Email
Check that you receive a professional response email with missing document requests.

---

## Sample Test Emails

### Test Email 1: Complete Application
**Subject:** "Loan Application - Complete Documentation"
**Attachments:**
- application.pdf
- paystub.pdf
- bank_statement.pdf
- tax_return.pdf
- employment_verification.pdf

**Expected Result:** "Ready for underwriting" email

### Test Email 2: Incomplete Application
**Subject:** "Mortgage Application - Missing Docs"
**Attachments:**
- application.pdf
- paystub.pdf

**Expected Result:** Email requesting missing documents

---

## Troubleshooting

### Common Issues

**1. Make.com can't reach RAG system**
- ✅ Check ngrok is running: `ngrok http 8000`
- ✅ Use https URL from ngrok in Make.com
- ✅ Verify RAG system is running: `curl http://localhost:8000`

**2. Email not triggering scenario**
- ✅ Check Gmail connection is active
- ✅ Verify email meets filter criteria (subject contains "loan")
- ✅ Ensure email has attachments

**3. RAG analysis returning errors**
- ✅ Check request format matches API documentation
- ✅ Verify all required fields are present
- ✅ Check RAG system terminal for error messages

**4. Generated emails are generic**
- ✅ Verify missing_documents field is populated correctly
- ✅ Check template_type is being set properly
- ✅ Ensure borrower_name is being passed correctly

### Debug Mode

**Enable Debug Logging:**
1. In Make.com scenario, click **Settings**
2. Enable **Debug mode**
3. Check execution logs for detailed information

**RAG System Debug:**
Check your terminal running the RAG system for request/response logs.

---

## Production Considerations

### 1. Security
- **API Authentication:** Add API keys to RAG system
- **HTTPS Only:** Never use http in production
- **Access Controls:** Limit Make.com webhook access

### 2. Scalability
- **Rate Limiting:** Add request limits to RAG system
- **Error Handling:** Implement retry logic in Make.com
- **Monitoring:** Set up alerts for failed scenarios

### 3. Compliance
- **Data Retention:** Implement automatic document deletion
- **Audit Logging:** Track all loan processing activities
- **GLBA Compliance:** Ensure all data handling meets regulations

---

## Sample Make.com JSON Configuration

For advanced users, here's the complete scenario configuration:

```json
{
  "name": "Loan Document Processor",
  "flow": [
    {
      "id": 1,
      "module": "gmail:watchEmails",
      "parameters": {
        "folder": "INBOX",
        "criteria": {
          "subject": "loan OR application OR mortgage",
          "hasAttachment": true
        }
      }
    },
    {
      "id": 2,
      "module": "builtin:filter",
      "filter": {
        "conditions": [
          {
            "a": "{{1.subject}}",
            "o": "text:contains",
            "b": "loan"
          }
        ]
      }
    },
    {
      "id": 3,
      "module": "gmail:downloadAttachment",
      "parameters": {
        "messageId": "{{1.id}}",
        "attachmentId": "{{1.attachments[].id}}"
      }
    },
    {
      "id": 4,
      "module": "http:ActionSendData",
      "parameters": {
        "url": "YOUR_NGROK_URL/upload-documents",
        "method": "POST",
        "bodyType": "multipart",
        "bodyFields": [
          {
            "name": "loan_id",
            "value": "{{1.id}}"
          },
          {
            "name": "files",
            "value": "{{3.data}}"
          }
        ]
      }
    },
    {
      "id": 5,
      "module": "http:ActionSendData",
      "parameters": {
        "url": "YOUR_NGROK_URL/analyze-loan",
        "method": "POST",
        "bodyType": "raw",
        "bodyRaw": {
          "loan_id": "{{1.id}}",
          "borrower_info": {
            "name": "{{1.from.name}}",
            "email": "{{1.from.address}}"
          },
          "loan_type": "conventional"
        }
      }
    },
    {
      "id": 6,
      "module": "http:ActionSendData",
      "parameters": {
        "url": "YOUR_NGROK_URL/generate-email",
        "method": "POST",
        "bodyType": "urlencoded",
        "bodyFields": [
          {
            "name": "loan_id",
            "value": "{{5.loan_id}}"
          },
          {
            "name": "borrower_name",
            "value": "{{1.from.name}}"
          },
          {
            "name": "template_type",
            "value": "{{5.email_template}}"
          }
        ]
      }
    },
    {
      "id": 7,
      "module": "gmail:sendEmail",
      "parameters": {
        "to": "{{1.from.address}}",
        "subject": "{{6.email_subject}}",
        "content": "{{6.email_body}}",
        "inReplyTo": "{{1.id}}"
      }
    }
  ]
}
```

---

## Success Metrics

Track these KPIs to measure success:
- **Processing Time:** Average time from email received to response sent
- **Accuracy:** Percentage of correctly identified missing documents
- **Borrower Satisfaction:** Response time and email quality
- **Efficiency:** Number of loans processed per hour

---

## Next Steps

1. **Set up the basic scenario** following steps 1-8
2. **Test with sample emails** to verify functionality
3. **Add advanced features** (routing, data storage, error handling)
4. **Monitor and optimize** based on real usage
5. **Scale up** with additional loan types and requirements

Your automated loan processor is now ready to handle incoming applications 24/7! 🚀
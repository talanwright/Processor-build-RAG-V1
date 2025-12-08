# Secure Email Implementation Guide

## Overview

This guide explains how to implement secure email notifications with permanent access links for your loan processing system.

## What Was Implemented

### 1. Database Changes
- Added `AccessToken` table to store secure access tokens
- Tokens link to loan IDs with expiration tracking
- Tracks access count and last access time
- Supports token revocation

### 2. API Endpoints

#### New Public Endpoints (No API Key Required)
- `GET /secure-loan/{token}` - View loan details and documents via secure link
- `GET /secure-loan/{token}/download/{filename}` - Download specific document via secure link

#### Updated Endpoints
- `POST /generate-email` - Now generates secure token and includes link in email

#### Admin Endpoints (API Key Required)
- `POST /revoke-token/{token}` - Revoke a secure access token

### 3. Security Features
- Tokens are cryptographically secure (32-byte URL-safe)
- **Permanent access** - Tokens don't expire (set to 100 years)
- Documents remain encrypted at rest
- Audit logging for all token access
- Token revocation capability

## Email Template

When you call `/generate-email`, you now get:

```
Subject: Loan Ready for Review - John Smith

A loan application is ready for your review.

Borrower: John Smith
Monthly Income: $8,500
Completeness: 100%

🔒 View Secure Documents: https://your-app.railway.app/secure-loan/[TOKEN]

This is a secure link that provides access to the loan application and all supporting documents.

Best regards,
Loan Processing Team
```

## How to Use in Make.com

### Step 1: Update Your Generate Email Module

In your Make.com scenario, update the HTTP module that calls `/generate-email`:

**URL:** `https://your-railway-app.up.railway.app/generate-email`

**Method:** POST

**Headers:**
```
X-API-Key: YOUR_API_KEY
Content-Type: application/json
```

**Body:**
```json
{
  "loan_id": "{{loan_id}}",
  "borrower_name": "{{borrower_name}}",
  "template_type": "ready_for_review",
  "monthly_income": {{monthly_income}},
  "completeness_score": {{completeness_score}}
}
```

**Response will include:**
- `email_subject` - Subject line
- `email_body` - Email body with secure link
- `secure_link` - Direct link URL
- `token` - The access token (for your records)

### Step 2: Send Email with Secure Link

Update your Gmail/Email module to use the response:

**To:** Underwriter's email address
**Subject:** `{{email_subject}}`
**Body:** `{{email_body}}`

The body will automatically include the secure link.

### Step 3: Set BASE_URL Environment Variable

In Railway, add this environment variable:

**Variable:** `BASE_URL`
**Value:** Your actual Railway URL (e.g., `https://web-production-abc123.up.railway.app`)

This ensures the secure links use the correct URL.

## What Recipients See

When someone clicks the secure link, they see:

```json
{
  "loan": {
    "loan_id": "LOAN123",
    "borrower_name": "John Smith",
    "loan_type": "conventional",
    "status": "ready_for_underwriting",
    "completeness_score": 100,
    "document_count": 5,
    "missing_documents": []
  },
  "documents": [
    {
      "filename": "pay_stub.pdf",
      "file_size": 125000,
      "upload_date": "2025-01-15T10:30:00",
      "download_url": "/secure-loan/{token}/download/pay_stub.pdf"
    }
  ],
  "access_info": {
    "expires_at": "Never",
    "hours_remaining": "Unlimited",
    "access_count": 3,
    "permanent_access": true
  }
}
```

## Download Documents

Recipients can download individual documents by clicking the download URLs:

`GET https://your-app.railway.app/secure-loan/{token}/download/pay_stub.pdf`

This will:
1. Verify the token is valid and not revoked
2. Decrypt the file from storage
3. Return the file for download
4. Log the access in audit logs

## Revoking Access

If you need to revoke access to a link:

**Request:**
```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  https://your-app.railway.app/revoke-token/{token}
```

**Response:**
```json
{
  "success": true,
  "token": "abcd1234...",
  "loan_id": "LOAN123",
  "message": "Token revoked successfully"
}
```

After revocation, the link will return "This link has been revoked".

## Security Benefits

### ✅ Documents Stay on Encrypted Server
- Files are encrypted at rest
- Only decrypted when downloaded via secure link
- No sensitive data in emails

### ✅ Audit Trail
All access is logged:
```json
{
  "timestamp": "2025-01-15T10:30:00",
  "category": "SECURE_ACCESS",
  "action": "TOKEN_USED",
  "details": {
    "loan_id": "LOAN123",
    "token": "abcd1234...",
    "access_count": 1,
    "ip": "192.168.1.1"
  }
}
```

### ✅ Can Revoke Access Anytime
- Admin can revoke tokens
- Immediate access denial
- Useful if link is shared inappropriately

### ✅ No Sensitive Data in Email
- Email only contains secure link
- No loan documents attached
- Borrower info minimal

## Testing the Implementation

### 1. Test Token Generation

```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_id": "TEST123",
    "borrower_name": "Test User",
    "template_type": "ready_for_review",
    "monthly_income": 8500,
    "completeness_score": 100
  }' \
  https://your-app.railway.app/generate-email
```

You should get back:
- Email subject and body
- `secure_link` with a token
- The token itself

### 2. Test Secure Access

Copy the `secure_link` from the response and paste it in your browser, or:

```bash
curl https://your-app.railway.app/secure-loan/{TOKEN}
```

You should see the loan details and document list.

### 3. Test Document Download

```bash
curl -o downloaded.pdf \
  https://your-app.railway.app/secure-loan/{TOKEN}/download/pay_stub.pdf
```

The file should download and be readable.

### 4. Test Token Revocation

```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  https://your-app.railway.app/revoke-token/{TOKEN}
```

Then try accessing the link again - it should be denied.

## Database Migration

Before deploying, you need to create the new `access_tokens` table:

### Option 1: Automatic (Recommended)

The table will be created automatically when the app starts because of this line:

```python
@app.on_event("startup")
def startup_event():
    init_database()
```

### Option 2: Manual

If you prefer to create it manually:

```sql
CREATE TABLE access_tokens (
    token VARCHAR(255) PRIMARY KEY,
    loan_id VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    is_revoked INTEGER DEFAULT 0
);

CREATE INDEX idx_access_tokens_loan_id ON access_tokens(loan_id);
CREATE INDEX idx_access_tokens_token ON access_tokens(token);
```

## Deployment Steps

1. **Update your code:**
   - Copy the updated `simple_rag_api.py`
   - Copy the updated `database.py`

2. **Set environment variable in Railway:**
   - Add `BASE_URL` with your Railway app URL

3. **Deploy to Railway:**
   ```bash
   git add .
   git commit -m "Add secure email links with permanent access"
   git push
   ```

4. **Verify deployment:**
   - Check Railway logs for "Database tables created successfully!"
   - Test the root endpoint: `https://your-app.railway.app/`
   - Should show version 3.1.0 with new endpoints

5. **Update Make.com scenario:**
   - Update the email generation module with new parameters
   - Test with a sample loan

## Make.com Scenario Updates

### Scenario A: New Loan Email

**When to send:** Loan completeness >= 80%

**HTTP Module (Generate Email):**
```json
{
  "loan_id": "{{analyze_response.loan_id}}",
  "borrower_name": "{{borrower_name}}",
  "template_type": "ready_for_review",
  "monthly_income": {{monthly_income}},
  "completeness_score": {{analyze_response.completeness_score}}
}
```

**Email Module:**
- To: underwriter@yourcompany.com
- Subject: `{{generate_email.email_subject}}`
- Body: `{{generate_email.email_body}}`

### Scenario B: Reminder Emails

For incomplete loans, you can still use the old template or also include a secure link to show what's missing.

## FAQ

**Q: What if I want links to expire after 24 hours?**
A: Change the `generate_secure_token` call to include `expiry_hours=24`:
```python
token = generate_secure_token(safe_loan_id, db, expiry_hours=24)
```

**Q: Can I customize the email template?**
A: Yes! Edit the email body in the `/generate-email` endpoint in `simple_rag_api.py`.

**Q: How do I track who accessed what?**
A: Check the audit logs at `/audit-log` endpoint or query the database:
```sql
SELECT * FROM access_tokens WHERE loan_id = 'LOAN123';
```

**Q: Can I send multiple links for the same loan?**
A: Yes! Each call to `/generate-email` creates a new token. You can revoke old ones if needed.

**Q: What if someone shares the link?**
A: The link will work for anyone who has it (like a shared Google Drive link). If this is a concern:
1. Use shorter expiration times
2. Implement IP restrictions
3. Revoke tokens after first use

**Q: Do documents stay encrypted?**
A: Yes! Files are encrypted at rest and only decrypted when downloaded via secure link.

## Next Steps

1. ✅ Deploy the updated code to Railway
2. ✅ Set the `BASE_URL` environment variable
3. ✅ Test with a sample loan
4. ✅ Update Make.com scenario
5. ✅ Send test email to yourself
6. ✅ Verify you can access loan via link
7. ✅ Enable for production use

## Support

If you encounter issues:
1. Check Railway logs for errors
2. Test endpoints individually with curl
3. Verify environment variables are set
4. Check database for `access_tokens` table

---

**Version:** 3.1.0
**Last Updated:** January 2025

# URGENT: Fix Retool Download Button

## What I Just Fixed

I fixed your Railway deployment issue. The problem was:
- **Docker image was 8.1 GB** (exceeded 4 GB limit)
- Railway config was pointing to wrong nested directory paths
- Nested `loan-processor-rag/loan-processor-rag/` directory was being included in build

## Changes Made

1. **railway.json** - Fixed paths to point to root directory
2. **.dockerignore** - Excluded nested directory causing bloat

Your code is now pushed to GitHub and Railway should be rebuilding automatically.

## What You Need to Do NOW

### Step 1: Wait for Railway to Deploy (5-10 minutes)

1. Go to Railway dashboard: https://railway.app
2. Watch the deployment progress
3. Wait for status to change from "Building" → "Deployed" with green checkmark
4. **CRITICAL**: The deployment MUST show "Deployment successful" before proceeding

### Step 2: Get Your API Key from Railway

1. In Railway, go to your project
2. Click on the "Variables" tab
3. Look for `API_KEY` variable
4. **Copy the value** (you'll need this in Step 3)

If you don't see API_KEY:
1. Click "Add Variable"
2. Name: `API_KEY`
3. Value: Create a secure random string (at least 32 characters)
4. Click "Add"
5. Railway will automatically redeploy

### Step 3: Fix Retool Download Button

Your button query `downloadDocument` needs TWO things added:

#### A. Add API Key Header

1. In Retool, open your `downloadDocument` query
2. Look for the "Headers" section (should already have a + button)
3. Click the + button to add a new header
4. Add this header:
   - **Key**: `X-API-Key`
   - **Value**: `{{ "your-actual-api-key-from-railway" }}`
   - Replace `your-actual-api-key-from-railway` with the actual key from Railway

#### B. Verify the URL is Correct

Your current URL looks correct:
```
https://function-bbd3.up.railway.app/loans/{{listLoans.data.email}}/documents/{{table1.selectedRow.filename}}/base64
```

But make sure:
- `listLoans.data.email` contains the loan ID (email address)
- `table1.selectedRow.filename` contains the exact filename (like "w2.pdf")

### Step 4: Test the Button

1. Click "Test" in the downloadDocument query
2. You should now see a JSON response like:
   ```json
   {
     "filename": "w2.pdf",
     "content": "JVBERi0xLjQK...",
     "mimeType": "application/pdf"
   }
   ```
3. If you still get "Not Found", check:
   - Did you upload documents for this loan ID?
   - Is the filename exactly right? (case-sensitive!)

### Step 5: Common Issues

**Still getting 404 "Not Found"?**
- The loan ID or filename doesn't exist in uploads
- Try calling `/loans` endpoint first to see what loans exist

**Getting 401 "Unauthorized"?**
- API key is missing or wrong
- Check Railway variables match Retool header

**Getting 429 "Too Many Requests"?**
- Rate limit hit (100 requests per minute)
- Wait 60 seconds and try again

**Railway still showing "Failed"?**
- Check deployment logs in Railway
- The Docker image might still be too large
- Contact me if this happens

## Quick Verification

Once Railway shows "Deployment successful":

1. Test if API is running by visiting:
   ```
   https://function-bbd3.up.railway.app/
   ```
   You should see: `{"message": "Loan Processor RAG API", "status": "running"}`

2. If that works, your API is live and you can proceed to Step 3

## Need Help?

If you're still stuck after following these steps:
1. Screenshot the Railway deployment logs
2. Screenshot the Retool error
3. Let me know which step failed

# Quick Test - Secure Email Feature

## Step 1: Wait for Railway Deployment
Wait about 2-3 minutes for Railway to finish deploying with the new BASE_URL.

## Step 2: Run This Test Command

Open your terminal and run:

```bash
cd "/Users/talanwright/Test RAG"
./test_secure_email.sh
```

It will ask you for:
1. **Railway URL** - Enter the BASE_URL you just added (e.g., `https://web-production-abc123.up.railway.app`)
2. **API Key** - Enter your API key from Railway

## Alternative: Manual Test

If you prefer to test manually, replace the values below and run:

```bash
# Replace these with your actual values
RAILWAY_URL="https://your-app.up.railway.app"
API_KEY="your_api_key_here"

# Test the email generation
curl -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_id": "TEST123",
    "borrower_name": "John Smith",
    "template_type": "ready_for_review",
    "monthly_income": 8500,
    "completeness_score": 100
  }' \
  "$RAILWAY_URL/generate-email"
```

## What You Should See

If it works, you'll get a response with:
- `email_subject`: "Loan Ready for Review - John Smith"
- `email_body`: Contains the secure link
- `secure_link`: A URL like `https://your-app.railway.app/secure-loan/ABC123...`
- `token`: The access token

## Step 3: Test the Secure Link

Copy the `secure_link` from the response and paste it in your browser.

You should see JSON with loan details!

## If You Get Errors

**Error: "Missing API key"**
- Check that your API_KEY is correct

**Error: 404 or connection refused**
- Railway might still be deploying, wait a bit longer
- Check that your RAILWAY_URL is correct

**BASE_URL still shows "your-railway-app.up.railway.app"**
- The BASE_URL environment variable wasn't set correctly
- Go back to Railway and verify it's there

## Next Steps After Successful Test

Once the test passes:
1. ✅ Secure email feature is working!
2. Update your Make.com scenario (optional)
3. Start using secure links in emails

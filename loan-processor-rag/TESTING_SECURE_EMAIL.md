# Testing Secure Email Feature

## Step 1: Deploy the Updated Code

First, let's deploy your changes to Railway:

```bash
cd "/Users/talanwright/Test RAG"
git add .
git commit -m "Add secure email links with permanent access"
git push
```

After pushing, wait 2-3 minutes for Railway to deploy.

## Step 2: Set BASE_URL in Railway

1. Go to Railway dashboard: https://railway.app
2. Click your project
3. Click "Variables" tab
4. Add new variable:
   - **Name:** `BASE_URL`
   - **Value:** Your Railway URL (find it in the "Deployments" tab)
   - Example: `https://web-production-0a9f4.up.railway.app`
5. Click "Add" and redeploy if needed

## Step 3: Test Token Generation (Using curl or Postman)

This tests if the secure link generation works:

### Option A: Using Terminal (Mac/Linux)

```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_id": "TEST123",
    "borrower_name": "John Smith",
    "template_type": "ready_for_review",
    "monthly_income": 8500,
    "completeness_score": 100
  }' \
  https://YOUR-RAILWAY-URL.up.railway.app/generate-email
```

**Replace:**
- `YOUR_API_KEY` with your actual API key
- `YOUR-RAILWAY-URL` with your Railway URL

### Option B: Using Postman/Insomnia

**Method:** POST
**URL:** `https://YOUR-RAILWAY-URL.up.railway.app/generate-email`

**Headers:**
```
X-API-Key: YOUR_API_KEY
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "loan_id": "TEST123",
  "borrower_name": "John Smith",
  "template_type": "ready_for_review",
  "monthly_income": 8500,
  "completeness_score": 100
}
```

### Expected Response:

You should get something like this:

```json
{
  "loan_id": "TEST123",
  "email_subject": "Loan Ready for Review - John Smith",
  "email_body": "A loan application is ready for your review.\n\nBorrower: John Smith\nMonthly Income: $8,500\nCompleteness: 100%\n\n🔒 View Secure Documents: https://your-app.railway.app/secure-loan/ABC123XYZ...\n\nThis is a secure link...",
  "template_type": "ready_for_review",
  "secure_link": "https://your-app.railway.app/secure-loan/ABC123XYZ...",
  "token": "ABC123XYZ...",
  "generated_timestamp": "2025-01-15T10:30:00"
}
```

**✅ SUCCESS:** You got a response with `secure_link` and `token`
**❌ FAILED:** Check Railway logs for errors

## Step 4: Test the Secure Link

Copy the `secure_link` from the response above and:

### Option A: Open in Browser

Just paste the link in your browser. You should see JSON with loan details.

### Option B: Using curl

```bash
curl https://YOUR-RAILWAY-URL.up.railway.app/secure-loan/YOUR_TOKEN
```

### Expected Response:

```json
{
  "loan": {
    "loan_id": "TEST123",
    "borrower_name": "John Smith",
    "status": "...",
    "completeness_score": 100,
    "document_count": 0
  },
  "documents": [],
  "access_info": {
    "expires_at": "Never",
    "hours_remaining": "Unlimited",
    "access_count": 1,
    "permanent_access": true
  }
}
```

**✅ SUCCESS:** You can see the loan details
**❌ FAILED:** Check if token is correct or if there's an error message

## Step 5: Update Make.com Scenario (Only After Tests Pass)

Now that you know it works, let's update Make.com:

### Find Your "Generate Email" HTTP Module

In your Make.com scenario, find the module that calls `/generate-email`.

### Update the Request Body

**OLD (what you might have):**
```json
{
  "loan_id": "{{loan_id}}",
  "borrower_name": "{{borrower_name}}",
  "template_type": "missing_docs",
  "missing_documents": []
}
```

**NEW (what you need):**
```json
{
  "loan_id": "{{loan_id}}",
  "borrower_name": "{{borrower_name}}",
  "template_type": "ready_for_review",
  "monthly_income": {{monthly_income}},
  "completeness_score": {{completeness_score}}
}
```

**Notes:**
- Replace `{{monthly_income}}` with wherever you get income from (could be from form data, email parsing, etc.)
- Replace `{{completeness_score}}` with the response from your `/analyze-loan` call
- If you don't have these values, you can omit them and they'll show as "N/A" in the email

### Update the Email Body Module

Your Gmail/Email module should use:

**Subject:** `{{generate_email_response.email_subject}}`
**Body:** `{{generate_email_response.email_body}}`

The body will automatically include the secure link!

### Test the Updated Scenario

1. Turn off your scenario temporarily
2. Make your updates
3. Turn it back on
4. Send a test email to trigger it
5. Check if you receive an email with the secure link
6. Click the link to verify it works

## Quick Verification Checklist

After deployment:

- [ ] Railway deployment successful (check Railway dashboard)
- [ ] `BASE_URL` environment variable set in Railway
- [ ] Test API call to `/generate-email` returns secure link
- [ ] Secure link works when opened in browser
- [ ] Make.com scenario updated (if applicable)
- [ ] Test email sent with working secure link

## Troubleshooting

### Error: "Missing API key"
- Make sure you're including `X-API-Key` header in your request
- Check that your API key is correct

### Error: "Token not found" or "Invalid link"
- The loan might not exist yet
- Try uploading documents first, then generate email

### Error: BASE_URL shows "your-railway-app.up.railway.app"
- You haven't set the `BASE_URL` environment variable
- Links will still work, but will have the wrong domain

### No documents show up in secure link
- This is normal if you just created a test loan
- Upload documents first, then the link will show them

### Email body looks wrong in Make.com
- Make sure you're using `{{email_body}}` not building it manually
- The endpoint now returns the full formatted email body

## What You DON'T Need to Change in Make.com

You do NOT need to change:
- Document upload logic
- Loan analysis logic
- The API key
- The base URL endpoints
- File iteration/processing

## What You DO Need to Change in Make.com (Optional)

Only if you want to use the secure email feature:

1. **Add parameters to `/generate-email` call:**
   - `monthly_income` (optional)
   - `completeness_score` (from analyze-loan response)
   - `template_type: "ready_for_review"` (instead of "missing_docs")

2. **Use the returned email body:**
   - Subject: `{{email_subject}}`
   - Body: `{{email_body}}` (includes secure link automatically)

That's it! Everything else stays the same.

## Simple Manual Test (No Code)

If you want to test without changing anything:

1. Deploy the code to Railway
2. Use Postman or curl to call `/generate-email` manually
3. Copy the `secure_link` from response
4. Open it in your browser
5. See if you can view loan details

If this works, you're good to go! Make.com changes are optional.

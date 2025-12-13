# Complete Make.com Setup Guide - Loan Processor with Railway API

**Start to Finish: Build Your Automated Loan Processing System**

---

## Prerequisites

Before you start, make sure you have:

- ✅ Railway API deployed and running: `https://web-production-bbd3.up.railway.app`
- ✅ API Key generated and added to Railway
- ✅ Make.com account (free tier is fine)
- ✅ Gmail account for receiving/sending emails
- ✅ OpenAI API key (for generating professional emails)

---

## What This Scenario Will Do

```
📧 Email arrives with loan documents
    ↓
🔄 Loop through each attachment
    ↓
📤 Upload documents to Railway API
    ↓
🔍 Analyze loan (check for missing documents, calculate risk)
    ↓
🤖 OpenAI generates personalized email response
    ↓
📧 Send email to borrower
    ↓
✅ Done!
```

---

## STEP 1: Create New Scenario

1. **Go to:** https://make.com
2. **Log in** to your account
3. **Click** "Scenarios" in the left sidebar
4. **Click** the blue "Create a new scenario" button
5. **Name it:** "Loan Document Processor"
6. **Click** "Continue"

You'll see a blank canvas with a big **"+"** button in the center.

---

## STEP 2: Set Up Email Trigger (Gmail)

### **Add Gmail Module:**

1. **Click** the big **"+"** button
2. **Search for:** "Gmail"
3. **Select:** "Gmail" (with the Gmail icon)
4. **Choose trigger:** "Watch Emails"

### **Configure Gmail Connection:**

1. **Click** "Add" next to Connection
2. **Click** "Sign in with Google"
3. **Select** your Gmail account
4. **Allow** Make.com to access your Gmail
5. **Click** "Save"

### **Configure Watch Emails Settings:**

Fill in these fields:

- **Folder:** `INBOX`
- **Criteria:**
  - **Label:** Leave empty
  - **From:** Leave empty
  - **Subject:** Leave empty (we'll filter in next step)
  - **Search:** Leave empty
- **Maximum number of results:** `10`
- **Mark messages as read when fetched:** `Yes` (so you don't process them twice)

**Click** "OK" to save

---

## STEP 3: Add Filter (Only Process Loan Emails)

### **Add Filter Module:**

1. **Click** the **"+"** button after the Gmail module
2. **Search for:** "Filter"
3. **Select:** "Filter" (looks like a funnel icon)

### **Configure Filter:**

1. **Click** "Setup a filter"
2. **Add condition:**
   - **Label:** "Subject contains loan keywords"
   - **Condition:** Click and select the first module (Gmail)
   - Find `Subject` in the dropdown
   - **Operator:** Contains (text operators)
   - **Value:** `loan`
3. **Click** "Add OR rule"
4. **Add second condition:**
   - **Condition:** Gmail → `Subject`
   - **Operator:** Contains
   - **Value:** `application`
5. **Click** "Add OR rule"
6. **Add third condition:**
   - **Condition:** Gmail → `Subject`
   - **Operator:** Contains
   - **Value:** `mortgage`

**Click** "OK"

---

## STEP 4: Add Iterator (Loop Through Attachments)

### **Add Iterator Module:**

1. **Click** the **"+"** after the Filter
2. **Search for:** `Iterator`
3. **Select:** `Iterator` (looks like a circular arrow icon)

### **Configure:**

- **Array:** Click in the field and select: Gmail (module 1) → `Attachments[]`

**What this does:** If someone sends multiple PDF files (e.g., 3 documents), the Iterator will loop through and process each attachment one by one.

**Note:** The `[]` means it's an array (list) of attachments

**Click** "OK"

---

## STEP 5: Upload Documents to Railway API

### **Add HTTP Module:**

1. **Click** the **"+"** after Iterator
2. **Search for:** "HTTP"
3. **Select:** "Make a request"

### **Configure HTTP Request:**

**URL:**
```
https://web-production-bbd3.up.railway.app/upload-documents
```

**Method:** `POST`

**Headers:**
Click "Add item" and add:

| Name | Value |
|------|-------|
| `X-API-Key` | `YOUR_API_KEY_HERE` (paste your actual API key) |

**Body type:** `Multipart/form-data`

**Fields:**
Click "Add item" for each field:

| Key | Value |
|-----|-------|
| `loan_id` | Click and select: Gmail (module 1) → `Message ID` |
| `files` | Click and select: Iterator → `Data` |

**Parse response:** `Yes`

**Click** "OK"

---

## STEP 6: Analyze Loan with Railway API

### **Add HTTP Module:**

1. **Click** the **"+"** after Upload Documents
2. **Search for:** "HTTP"
3. **Select:** "Make a request"

### **Configure HTTP Request:**

**URL:**
```
https://web-production-bbd3.up.railway.app/analyze-loan
```

**Method:** `POST`

**Headers:**
Click "Add item" twice to add these headers:

| Name | Value |
|------|-------|
| `X-API-Key` | `YOUR_API_KEY_HERE` (paste your actual API key) |
| `Content-Type` | `application/json` |

**Body type:** `Raw`

**Request content:**
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

**IMPORTANT:** Replace the `{{}}` placeholders:
- Click inside the `loan_id` value field
- Select: Gmail (module 1) → `ID`
- Click inside the `name` value field
- Select: Gmail → `From: Name`
- Click inside the `email` value field
- Select: Gmail → `From: Address`

**Parse response:** `Yes`

**Click** "OK"

---

## STEP 7: Router (Split Based on Analysis Results)

### **Add Router:**

1. **Click** the **"+"** after Analyze Loan
2. **Search for:** "Router"
3. **Select:** "Router"

**Click** "OK"

You'll see the Router creates two empty paths. We'll configure these next.

---

## STEP 8: Route 1 - Missing Documents Path

### **Configure Route 1 Filter:**

1. **Click** the wrench icon on the first route path
2. **Label:** `Missing Documents`
3. **Add condition:**
   - **Field:** Click and select: Analyze Loan (module 5) → `status`
   - **Operator:** Equal to (text operators)
   - **Value:** `pending_documents`

**Click** "OK"

### **Add OpenAI Module (Generate Email for Missing Docs):**

1. **Click** the **"+"** on the first route path
2. **Search for:** "OpenAI"
3. **Select:** "OpenAI"
4. **Choose:** "Create a Completion" or "Create a Chat Completion"

### **Configure OpenAI Connection:**

1. **Click** "Add" next to Connection
2. **API Key:** Paste your OpenAI API key (get it from https://platform.openai.com/api-keys)
3. **Click** "Save"

### **Configure OpenAI Request:**

- **Model:** `gpt-4` or `gpt-3.5-turbo`
- **Messages:** Click "Add item"
  - **Role:** `user`
  - **Message Content:**

```
Write a professional email to a loan applicant requesting missing documents.

Borrower Name: {{1.from.name}}

Missing Documents:
{{5.missing_documents[].document_type}}

Tone: Professional, friendly, helpful
Length: 3-4 paragraphs
Include: Clear list of what's needed and why it's important
```

**Replace placeholders by clicking inside the field and selecting:**
- `{{1.from.name}}` → Gmail → From: Name
- `{{5.missing_documents[].document_type}}` → Analyze Loan → missing_documents[] → document_type

- **Temperature:** `0.7`
- **Max Tokens:** `500`

**Click** "OK"

---

## STEP 9: Route 1 - Send Email (Missing Documents)

### **Add Gmail Send Email Module:**

1. **Click** the **"+"** after OpenAI
2. **Search for:** "Gmail"
3. **Select:** "Send an Email"

### **Configure:**

- **Connection:** Same Gmail connection
- **To:** Click and select: Gmail → `From: Address`
- **Subject:** `Additional Documentation Required - Loan Application`
- **Content:** Click and select: OpenAI → `Choices[] → Message → Content`
- **Type:** `Text`
- **In Reply To:** Click and select: Gmail → `Message ID` (this makes it a reply thread)

**Click** "OK"

---

## STEP 10: Route 2 - Ready for Underwriting Path

### **Configure Route 2 Filter:**

1. **Click** the wrench icon on the second route path
2. **Label:** `Ready for Underwriting`
3. **Add condition:**
   - **Field:** Analyze Loan → `status`
   - **Operator:** Equal to
   - **Value:** `ready_for_underwriting`

**Click** "OK"

### **Add OpenAI Module (Generate Approval Email):**

1. **Click** the **"+"** on the second route path
2. **Search for:** "OpenAI"
3. **Select:** "Create a Completion" or "Create a Chat Completion"
4. **Use same OpenAI connection**

### **Configure OpenAI Request:**

- **Model:** `gpt-4` or `gpt-3.5-turbo`
- **Messages:** Click "Add item"
  - **Role:** `user`
  - **Message Content:**

```
Write a professional email to a loan applicant confirming we've received all their documents.

Borrower Name: {{1.from.name}}

Status: All documents received and complete
Next Steps: Application is being forwarded to underwriting for review
Timeline: 3-5 business days for initial review

Tone: Professional, congratulatory, reassuring
Length: 2-3 paragraphs
```

- **Temperature:** `0.7`
- **Max Tokens:** `400`

**Click** "OK"

### **Add Gmail Send Email Module:**

1. **Click** the **"+"** after OpenAI
2. **Search for:** "Gmail"
3. **Select:** "Send an Email"

### **Configure:**

- **Connection:** Same Gmail connection
- **To:** Gmail → `From: Address`
- **Subject:** `Loan Application Update - Documents Received`
- **Content:** OpenAI → `Choices[] → Message → Content`
- **Type:** `Text`
- **In Reply To:** Gmail → `Message ID`

**Click** "OK"

---

## STEP 11: Add Data Storage (Optional but Recommended)

After the Analyze Loan module, you can add a data store to track all loans:

### **Add Data Store Module:**

1. **Click** the **"+"** after Analyze Loan (before Router)
2. **Search for:** "Data store"
3. **Select:** "Add a record"

### **Create Data Store:**

1. **Click** "Add" next to Data store
2. **Name:** `Loan Records`
3. **Add these fields:**

| Field Name | Type |
|------------|------|
| loan_id | Text |
| borrower_name | Text |
| borrower_email | Text |
| status | Text |
| completeness_score | Number |
| risk_score | Number |
| processed_date | Date |

4. **Click** "Save"

### **Configure Add Record:**

Map the fields:

- **loan_id:** Analyze Loan → `loan_id`
- **borrower_name:** Gmail → `From: Name`
- **borrower_email:** Gmail → `From: Address`
- **status:** Analyze Loan → `status`
- **completeness_score:** Analyze Loan → `completeness_score`
- **risk_score:** Analyze Loan → `risk_score`
- **processed_date:** Click "now" function or select current timestamp

**Click** "OK"

---

## STEP 12: Add Error Handlers (Important!)

For each HTTP module (Upload Documents, Analyze Loan), add error handling:

1. **Right-click** on the HTTP module
2. **Select** "Add error handler"
3. **Choose** "Resume" directive
4. **Add** a Gmail module to send you a notification:
   - **To:** Your email
   - **Subject:** `Loan Processor Error`
   - **Content:**
   ```
   Error processing loan: {{1.from.name}}
   Error: {{Error message}}
   ```

---

## STEP 13: Save and Test

### **Save Your Scenario:**

1. **Click** the "Save" icon (floppy disk) in the bottom left
2. Scenario is now saved!

### **Test Your Scenario:**

1. **Click** "Run once" at the bottom
2. **Send yourself a test email:**
   - **To:** Your Gmail address
   - **Subject:** "Loan Application - John Doe"
   - **Attach:** 1-2 PDF files (any PDFs work for testing)
   - **Body:** "Here are my loan documents"

3. **Watch the scenario execute:**
   - You'll see each module light up as it runs
   - Check for green checkmarks (success) or red X's (errors)
   - Click on modules to see the data they processed

4. **Check your email:**
   - You should receive a response email from your Gmail
   - It should mention missing documents (since test PDFs aren't real loan docs)

---

## STEP 14: Turn On Scheduling

Once testing works:

1. **Click** the clock icon at the bottom left
2. **Select** "Every 15 minutes" (or your preferred interval)
3. **Click** "OK"

Now your scenario will automatically check for new loan emails every 15 minutes!

---

## Your Complete Scenario Flow

```
[1] Gmail: Watch Emails
      ↓
[2] Filter: Only loan-related emails
      ↓
[3] Iterator: Loop through attachments
      ↓
[4] HTTP: Upload to Railway (/upload-documents)
      ↓
[5] HTTP: Analyze Loan (/analyze-loan)
      ↓
[6] Data Store: Save loan record (optional)
      ↓
[7] Router: Split based on status
      ↓
   ┌──────────────┴──────────────┐
   │                             │
[Route 1]                    [Route 2]
Missing Docs                 Ready for Underwriting
   │                             │
[8] OpenAI: Generate         [10] OpenAI: Generate
    missing docs email            approval email
   │                             │
[9] Gmail: Send email        [11] Gmail: Send email
```

---

## Critical Security Checklist

Before going live, verify:

- [ ] ✅ API Key is added to ALL HTTP modules calling Railway
- [ ] ✅ API Key is stored in Railway environment variables
- [ ] ✅ Gmail has 2FA enabled
- [ ] ✅ OpenAI API key is valid and has billing set up
- [ ] ✅ Make.com account has 2FA enabled (Settings → Security)
- [ ] ✅ Railway account has 2FA enabled
- [ ] ✅ Test scenario works with real loan email

---

## Troubleshooting Common Issues

### **"Invalid API Key" Error**

**Problem:** Railway API returns 401/403 error

**Solution:**
1. Check API key is correct in Railway Variables
2. Verify `X-API-Key` header is in ALL HTTP modules
3. Make sure there are no extra spaces in the API key

---

### **"No emails being processed"**

**Problem:** Scenario runs but doesn't find emails

**Solution:**
1. Check Gmail connection is active
2. Verify emails match the filter criteria (subject contains "loan", "application", or "mortgage")
3. Make sure emails have attachments
4. Check "Mark as read" setting isn't hiding new emails

---

### **"OpenAI returns generic emails"**

**Problem:** Emails aren't personalized

**Solution:**
1. Check that borrower name is being passed correctly
2. Verify missing documents list is populating
3. Increase temperature to 0.8 for more creative responses
4. Add more context to the prompt

---

### **"Attachments not uploading"**

**Problem:** Railway returns error on file upload

**Solution:**
1. Check Railway logs for specific error
2. Verify Railway service is running (ACTIVE status)
3. Check file size limits (Railway may have limits)
4. Ensure multipart/form-data is set correctly

---

## Monitoring Your Scenario

### **Check Scenario Health:**

1. Go to Make.com → Scenarios
2. Look at your scenario's stats:
   - **Successful runs** (green)
   - **Failed runs** (red)
   - **Operations used** (for billing)

### **View Execution History:**

1. Click on your scenario
2. Click "History" at the bottom
3. See every execution with details

### **Set Up Notifications:**

1. Scenario Settings → Notifications
2. Enable email notifications for:
   - Errors
   - Warnings
   - First successful run after error

---

## Estimated Costs

### **Make.com:**
- Free tier: 1,000 operations/month
- Each loan processes ~10-15 operations
- **Free for ~60-100 loans/month**
- Paid: $9/month for 10,000 operations

### **OpenAI:**
- GPT-3.5-turbo: ~$0.002 per email
- GPT-4: ~$0.03 per email
- **~$5-10/month for 100-200 emails**

### **Railway:**
- Free tier: $5 credit
- **Usually stays free** unless high traffic

### **Total: FREE to $20/month depending on volume**

---

## Next Steps After Setup

1. **Test with 5-10 real loan emails** before going live
2. **Monitor for first week** to catch any issues
3. **Train your client** on what to expect
4. **Set up monthly reports** to show value
5. **Scale up** as needed

---

## Getting Help

If you get stuck:

1. **Check Make.com documentation:** https://www.make.com/en/help
2. **Railway docs:** https://docs.railway.app
3. **OpenAI API docs:** https://platform.openai.com/docs
4. **Check your audit logs** in Railway for API errors

---

## Success Metrics to Track

After 1 month, review:

- ✅ Number of loans processed automatically
- ✅ Time saved (before vs after automation)
- ✅ Error rate (should be < 5%)
- ✅ Email quality (ask borrowers for feedback)
- ✅ Response time (should be < 30 minutes)

---

**Your automated loan processor is now ready! 🚀**

When a borrower sends a loan application email:
1. ✅ System receives it instantly
2. ✅ Downloads and processes documents
3. ✅ Analyzes completeness
4. ✅ AI generates personalized response
5. ✅ Sends professional email back
6. ✅ All in under 2 minutes, 24/7!

**You've just built a system that would cost $10,000+ to hire someone to build!**

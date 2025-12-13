

# Test Email Templates for Loan Processing System

Use these templates to test your Make.com scenario by sending emails to yourself.

---

## Test Email #1: Complete Loan Application (High Score)

**Subject:** Loan Application - Complete Documentation

**From:** Your personal email

**To:** The email address that Make.com is watching (your Gmail)

**Body:**
```
Hello,

I am submitting my loan application with all required documents attached.

Borrower Name: Sarah Johnson
Loan Type: Conventional
Property Address: 123 Main Street, Austin, TX 78701
Loan Amount: $350,000

Please review and let me know if you need anything else.

Thank you,
Sarah Johnson
sarah.johnson.test@email.com
```

**Attachments:**
- Create 3-5 PDF files (can be any PDFs you have - rename them to look like loan docs):
  - `pay_stub_January_2025.pdf`
  - `tax_return_2024.pdf`
  - `bank_statement_December_2024.pdf`
  - `employment_verification.pdf`
  - `credit_report.pdf`

**Expected Result:**
- Make.com processes email ✅
- Uploads 3-5 documents to Railway ✅
- Analyzes loan (should show ~80-100% complete) ✅
- Sends automated response email ✅
- Shows in Retool dashboard ✅

---

## Test Email #2: Incomplete Loan Application (Low Score)

**Subject:** Mortgage Application Documents

**From:** Your personal email

**To:** The email Make.com watches

**Body:**
```
Hi,

I'm applying for a mortgage and here are some of my documents.

Name: Mike Chen
Loan Type: FHA
Property: 456 Oak Avenue, Dallas, TX 75201
Amount: $280,000

I'll send more documents soon.

Mike Chen
mike.chen.test@email.com
```

**Attachments:**
- Create only 1-2 PDFs (to simulate incomplete):
  - `pay_stub.pdf`
  - `id_copy.pdf`

**Expected Result:**
- Make.com processes ✅
- Uploads only 2 documents ✅
- Analyzes loan (should show ~30-50% complete) ✅
- Response mentions missing documents ✅
- Should trigger reminder emails in 24h (Scenario B) ✅

---

## Test Email #3: No Attachments (Should Fail Gracefully)

**Subject:** Loan Application Question

**From:** Your personal email

**To:** The email Make.com watches

**Body:**
```
Hello,

I have a question about my loan application. Can you help?

Thanks,
Test User
```

**Attachments:** NONE

**Expected Result:**
- Make.com processes email ✅
- Iterator has no attachments to loop through ✅
- Should skip or handle gracefully (no error) ✅
- Might send response asking for documents ✅

---

## Test Email #4: Multiple File Types (Test File Handling)

**Subject:** Application Documents - Various Formats

**From:** Your personal email

**To:** The email Make.com watches

**Body:**
```
Hi there,

Sending my loan documents in various formats.

Borrower: Jessica Martinez
Loan: Conventional $420,000

Thanks,
Jessica
jessica.martinez.test@email.com
```

**Attachments:**
- Mix of file types:
  - `W2_2024.pdf`
  - `bank_statement.jpg` (image)
  - `employment_letter.docx` (Word doc)
  - `tax_return.pdf`

**Expected Result:**
- Tests if Make.com handles different file types ✅
- Shows which file types your RAG can process ✅
- Might get errors on non-PDF files (this is good to know!) ⚠️

---

## Test Email #5: Large Volume (Stress Test)

**Subject:** Complete Loan Application Package

**From:** Your personal email

**To:** The email Make.com watches

**Body:**
```
Dear Loan Officer,

Attached is my complete loan application package with all supporting documentation.

Borrower: David Thompson
Property: 789 Elm Street, Houston, TX 77001
Loan Amount: $500,000
Loan Type: Jumbo

Please process at your earliest convenience.

Best regards,
David Thompson
david.thompson.test@email.com
```

**Attachments:**
- Create 8-10 PDFs (tests Make.com iteration speed):
  - `pay_stub_jan.pdf`
  - `pay_stub_dec.pdf`
  - `pay_stub_nov.pdf`
  - `tax_return_2024.pdf`
  - `tax_return_2023.pdf`
  - `bank_statement_1.pdf`
  - `bank_statement_2.pdf`
  - `bank_statement_3.pdf`
  - `credit_report.pdf`
  - `employment_verification.pdf`

**Expected Result:**
- Tests Iterator performance ✅
- Tests API upload speed ✅
- Tests database handling ✅
- Should show 100% completeness ✅

---

## How to Create Quick Test PDFs

If you don't have real PDFs to use, here are quick ways to create them:

### **Option 1: Convert Web Pages to PDF**
1. Open any website
2. Press `Cmd + P` (Mac) or `Ctrl + P` (Windows)
3. Select "Save as PDF"
4. Rename to test filenames above

### **Option 2: Create Blank PDFs with Preview (Mac)**
1. Open Preview app
2. File → New from Clipboard
3. Type some text or draw something
4. Save as PDF with test filename

### **Option 3: Use Google Docs**
1. Create a new Google Doc
2. Type: "This is a test document for [filename]"
3. File → Download → PDF
4. Rename file

### **Option 4: Command Line (Mac/Linux)**
```bash
# Create a simple text file and convert to PDF
echo "Test pay stub document" > pay_stub.txt
textutil -convert pdf pay_stub.txt
mv pay_stub.pdf pay_stub_January_2025.pdf
```

---

## Testing Checklist

After sending each test email, verify:

- [ ] Make.com scenario triggered (check History tab)
- [ ] No errors in Make.com execution log
- [ ] Files uploaded to Railway (check Railway logs)
- [ ] Database updated (check `/stats` endpoint or Retool)
- [ ] Loan analysis completed (check completeness_score)
- [ ] Automated response email received
- [ ] Loan appears in Retool dashboard
- [ ] All data is encrypted (check Railway database)

---

## Quick API Check (Before Testing)

Before sending test emails, verify your API is running:

**Option 1: Browser**
```
https://web-production-0a9f4.up.railway.app/
```
Should show: `{"message": "Loan RAG API v3.0.0", ...}`

**Option 2: Command Line**
```bash
curl https://web-production-0a9f4.up.railway.app/
```

**Option 3: Check Stats**
```bash
curl -H "X-API-Key: YOUR_API_KEY" https://web-production-0a9f4.up.railway.app/stats
```

---

## Monitoring Test Results

### **1. Make.com Scenario History:**
- Go to Make.com → Scenarios → Your scenario
- Click "History" tab
- See each execution with timestamp
- Click execution to see detailed logs

### **2. Railway Logs:**
- Go to Railway dashboard
- Click your project
- Click "Deployments" → "View Logs"
- Look for upload and analysis logs

### **3. Retool Dashboard:**
- Open your Retool app
- Check if new loans appear
- Verify completeness scores
- Check document counts

### **4. Database Direct Check (API):**
```bash
# Get all loans
curl -H "X-API-Key: YOUR_API_KEY" https://web-production-0a9f4.up.railway.app/stats

# Get specific loan
curl -H "X-API-Key: YOUR_API_KEY" https://web-production-0a9f4.up.railway.app/loan/{loan_id}
```

---

## Common Issues & Solutions

### **Issue: Make.com doesn't trigger**
- **Solution:** Make sure scenario is turned ON (toggle switch)
- **Solution:** Check Gmail is connected properly
- **Solution:** Send email with keywords: "loan", "application", or "mortgage" in subject

### **Issue: Files not uploading**
- **Solution:** Check API key in Make.com HTTP module
- **Solution:** Verify Railway API is running
- **Solution:** Check file size limits (might be too large)

### **Issue: No response email received**
- **Solution:** Check OpenAI API key is set in Make.com
- **Solution:** Check Gmail send module is configured
- **Solution:** Check spam folder

### **Issue: Loan not appearing in Retool**
- **Solution:** Refresh Retool dashboard
- **Solution:** Check database connection in Retool
- **Solution:** Verify loan_id was created (check Make.com logs)

---

## Next Steps After Testing

Once tests are successful:

1. ✅ Keep scenario running for production
2. ✅ Give client access to Retool dashboard
3. ✅ Enable IP whitelisting (after adding Retool IPs)
4. ✅ Build Make.com Scenario B (reminder emails)
5. ✅ Monitor for first real loan applications

---

**Ready to test? Start with Test Email #1 and work your way through!**

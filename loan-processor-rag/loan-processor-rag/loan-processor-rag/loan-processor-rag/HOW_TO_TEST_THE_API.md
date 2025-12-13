# How to Test Your API (What You're Looking At)

## What Is This Screen?

You're looking at **Swagger UI** - an interactive playground to test your API.

Each colored bar = A different thing your API can do

---

## Test #1: Check If It's Running (Easiest)

1. **Click** on the blue bar that says **GET /** "Root"
2. It will expand and show more options
3. **Click** the "Try it out" button
4. **Click** the blue "Execute" button
5. **Scroll down** - you'll see the response:

```json
{
  "message": "Loan Processor RAG API",
  "status": "running",
  "timestamp": "2025-11-02T...",
  "version": "1.0.0"
}
```

**✅ If you see this = Your API is working!**

---

## Test #2: See System Stats

1. **Click** on the blue bar **GET /stats** "Get System Stats"
2. **Click** "Try it out"
3. **Click** "Execute"
4. **Scroll down** - you'll see statistics like:
   - How many loans processed
   - How many documents uploaded
   - System health

---

## Test #3: Upload a Document (More Advanced)

To test uploading an actual document, you need a PDF file. Here's how:

1. **Click** on the green bar **POST /upload-documents**
2. **Click** "Try it out"
3. You'll see fields to fill in:
   - **files**: Click "Choose File" and select a PDF from your computer
   - **loan_id**: Type something like "TEST-001"
4. **Click** "Execute"
5. **Scroll down** - you'll see what the API detected:

```json
{
  "loan_id": "TEST-001",
  "uploaded_files": [
    {
      "filename": "document.pdf",
      "document_type": "pay_stub",
      "size": 245678,
      "status": "uploaded"
    }
  ]
}
```

---

## Test #4: Analyze a Complete Loan

This is the "magic" - where the API tells you what's missing, any problems, etc.

1. **Click** on the green bar **POST /analyze-loan**
2. **Click** "Try it out"
3. You'll see a big text box with example JSON. **Replace it with this:**

```json
{
  "loan_id": "TEST-001",
  "loan_type": "conventional",
  "borrower_info": {
    "name": "John Smith",
    "email": "john@example.com"
  },
  "documents": [
    {
      "filename": "paystub.pdf",
      "document_type": "pay_stub"
    },
    {
      "filename": "w2.pdf",
      "document_type": "tax_return"
    }
  ]
}
```

4. **Click** "Execute"
5. **Scroll down** - you'll see a detailed analysis:

```json
{
  "loan_id": "TEST-001",
  "completeness_score": 0.4,
  "missing_documents": [
    "Bank Statement",
    "Employment Verification",
    "Appraisal"
  ],
  "red_flags": [],
  "risk_score": "medium",
  "status": "incomplete",
  "suggested_actions": [
    "Request bank statements",
    "Order employment verification"
  ]
}
```

**This tells you:**
- ✅ File is only 40% complete
- ❌ Missing 3 types of documents
- ⚠️ No red flags detected
- 📊 Medium risk
- 💡 What to do next

---

## What This Actually Does For You

Imagine you have a loan file for "John Smith":
- He sent you 2 documents
- You don't know what else you need
- You don't know if there are any problems

**Without this API:**
- You manually check each document (10 minutes)
- You compare to a checklist (5 minutes)
- You look for red flags (10 minutes)
- You write an email to John (5 minutes)
- **Total: 30 minutes**

**With this API:**
- Upload documents (10 seconds)
- Click "Analyze Loan" (5 seconds)
- Get complete analysis instantly
- Get suggested email text
- **Total: 30 seconds**

---

## The Real-World Workflow

Once you connect this to **Make.com** (the automation platform):

```
1. Borrower emails you documents
   ↓
2. Make.com automatically uploads to your API
   ↓
3. Your API analyzes everything
   ↓
4. Make.com gets the results
   ↓
5. Make.com sends professional email back
   ↓
ALL AUTOMATIC - Zero manual work!
```

---

## What Each Color Means

- **🔵 Blue (GET)** = "Read" operations
  - Just getting information
  - Nothing changes
  - Safe to click repeatedly

- **🟢 Green (POST)** = "Write" operations
  - Uploading files
  - Analyzing data
  - Generating results
  - Actually does something

---

## The Bottom Section: "Schemas"

Those are technical definitions of the data structures. You can ignore these unless you're a developer integrating with the API.

They just define what format the data should be in.

---

## Try This Right Now

**Step 1:** Click the blue **GET /** bar
**Step 2:** Click "Try it out"
**Step 3:** Click "Execute"
**Step 4:** Scroll down and see the response

**That's it!** You just successfully called your API.

---

## Common Questions

**Q: Why is this running on my computer?**
A: This is the "local" version for testing. When you deploy to Railway (cloud), it runs 24/7 online.

**Q: Can anyone access this?**
A: Right now only you can (it's on localhost = your computer only). When deployed, it has API key security.

**Q: Do I need to keep this page open?**
A: No. This is just the documentation. The API runs in the background (the terminal window).

**Q: What if I close the browser?**
A: The API still runs. Just go back to http://localhost:8000/docs to see this page again.

**Q: How do I stop the API?**
A: Go to the terminal where it's running and press **Ctrl+C**

**Q: What's the difference between this and Make.com?**
A:
- **This API** = The brain (analyzes documents)
- **Make.com** = The hands (connects email → API → email automatically)

---

## Next Steps

1. ✅ **Test the endpoints** on this page (you're here!)
2. 📤 **Deploy to Railway** so it runs 24/7 in the cloud
3. 🔗 **Connect to Make.com** for full automation
4. 🚀 **Start processing loans automatically!**

---

## Quick Reference

| Endpoint | What It Does | When to Use |
|----------|--------------|-------------|
| GET / | Health check | "Is the API running?" |
| POST /upload-documents | Upload files | When borrower sends documents |
| POST /analyze-loan | Full analysis | To check what's missing |
| POST /generate-email | Write email | To respond to borrower |
| GET /loan-status/{id} | Check one loan | "What's the status of loan XYZ?" |
| GET /stats | System stats | Check performance |

---

**You've got a working loan processing API!** 🎉

It's currently only on your computer, but it's fully functional and ready to deploy.

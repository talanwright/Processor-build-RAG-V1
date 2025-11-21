# Make.com Scenario B: Automated Reminder System
## Daily Follow-Up Emails for Incomplete Loan Applications

---

## 🎯 What This Scenario Does

Runs **once per day at 9:00 AM** and:
1. Checks for loans with incomplete documents (completeness < 100%)
2. Sends **Reminder #1** if 24 hours have passed since loan creation
3. Sends **Reminder #2** if 24 hours have passed since Reminder #1
4. Updates the database to track which reminders were sent

---

## 📋 Prerequisites

Before you start, make sure you have:
- ✅ Railway API deployed with PostgreSQL database
- ✅ Your API URL: `https://web-production-0a9f4.up.railway.app`
- ✅ Your API Key from Railway (same one used in Scenario A)
- ✅ Gmail account connected to Make.com

---

## 🛠️ Step-by-Step Setup

### **Step 1: Create New Scenario**

1. Go to https://make.com
2. Click **"Create a new scenario"**
3. Name it: **"Loan Reminder System - Daily"**
4. Click **"Continue"**

---

### **Step 2: Add Schedule Trigger**

1. Click the **"+"** button to add first module
2. Search for **"Schedule"**
3. Select **"Schedule" → "Every day"**
4. Configure:
   - **Time**: `09:00` (9:00 AM)
   - **Time zone**: Choose your timezone (e.g., `America/New_York`)
5. Click **"OK"**

**Why 9 AM?** This is a good time because:
- Business hours just started
- Borrowers are likely checking email
- Gives them the full day to respond

---

### **Step 3: Get Incomplete Loans**

1. Click **"+"** after the Schedule module
2. Search for **"HTTP"**
3. Select **"HTTP" → "Make a request"**
4. Configure:

   **URL:**
   ```
   https://web-production-0a9f4.up.railway.app/incomplete-loans
   ```

   **Method:** `GET`

   **Headers:**
   - Click **"Add item"**
   - **Name:** `X-API-Key`
   - **Value:** `YOUR_API_KEY_HERE` (paste your Railway API key)

5. Click **"OK"**

**What this does:** Fetches all loans where completeness_score < 100% and calculates if they need reminders.

---

### **Step 4: Parse the Response**

1. Click **"+"** after the HTTP module
2. Search for **"JSON"**
3. Select **"JSON" → "Parse JSON"**
4. Configure:

   **JSON string:** Click the field and select from the HTTP module:
   - Find `Data` → `incomplete_loans`
   - Or just map: `{{2.data.incomplete_loans}}`

5. Click **"OK"**

---

### **Step 5: Add Iterator (Loop Through Each Loan)**

1. Click **"+"** after Parse JSON
2. Search for **"Iterator"**
3. Select **"Flow control" → "Iterator"**
4. Configure:

   **Array:** Click and select the array from Parse JSON module
   - Should map to the parsed incomplete_loans array

5. Click **"OK"**

**What this does:** Loops through each incomplete loan one by one.

---

### **Step 6: Add Router (Branch for Different Reminder Types)**

1. Click **"+"** after Iterator
2. Search for **"Router"**
3. Select **"Flow control" → "Router"**
4. Click **"OK"**

The router will create 2 branches:
- **Branch 1:** Send Reminder #1 (24 hours after loan creation)
- **Branch 2:** Send Reminder #2 (24 hours after Reminder #1)

---

### **Step 7: Configure Branch 1 - First Reminder**

1. Click the **wrench icon** on Route 1
2. **Label:** `First Reminder (24h after creation)`
3. Click **"Set up a filter"**
4. Configure filter:

   **Condition 1:**
   - **Label:** `Should send reminder 1`
   - **Field:** Click and select `should_send_reminder_1` from Iterator
   - **Operator:** `Equal to`
   - **Value:** `true`

5. Click **"OK"**

---

### **Step 8: Send First Reminder Email**

1. Click **"+"** on Route 1 (after the filter)
2. Search for **"Gmail"**
3. Select **"Gmail" → "Send an Email"**
4. **Connect your Gmail account** if not already connected
5. Configure:

   **To:**
   ```
   {{borrower_email}}
   ```
   (Map from Iterator)

   **Subject:**
   ```
   Reminder: Additional Documents Needed for Your Loan Application
   ```

   **Content:**
   ```
   Dear {{borrower_name}},

   This is a friendly reminder that we're still waiting for some documents to complete your loan application.

   Currently, your application is {{completeness_score}}% complete.

   Missing documents:
   {{join(missing_documents; ", ")}}

   Please upload these documents as soon as possible to avoid delays in processing your loan.

   If you have any questions, please don't hesitate to contact us.

   Best regards,
   Loan Processing Team
   ```

   **Content Type:** `Text`

6. Click **"OK"**

---

### **Step 9: Update Database After Sending First Reminder**

1. Click **"+"** after the Gmail module
2. Search for **"HTTP"**
3. Select **"HTTP" → "Make a request"**
4. Configure:

   **URL:**
   ```
   https://web-production-0a9f4.up.railway.app/update-reminder?loan_id={{loan_id}}
   ```
   (Map `loan_id` from Iterator)

   **Method:** `POST`

   **Headers:**
   - Click **"Add item"**
   - **Name:** `X-API-Key`
   - **Value:** `YOUR_API_KEY_HERE`

5. Click **"OK"**

**What this does:** Tells the database that Reminder #1 was sent, so it won't send it again.

---

### **Step 10: Configure Branch 2 - Second Reminder**

1. Click the **wrench icon** on Route 2
2. **Label:** `Second Reminder (24h after first)`
3. Click **"Set up a filter"**
4. Configure filter:

   **Condition 1:**
   - **Label:** `Should send reminder 2`
   - **Field:** Click and select `should_send_reminder_2` from Iterator
   - **Operator:** `Equal to`
   - **Value:** `true`

5. Click **"OK"**

---

### **Step 11: Send Second Reminder Email**

1. Click **"+"** on Route 2
2. Search for **"Gmail"**
3. Select **"Gmail" → "Send an Email"**
4. Configure:

   **To:**
   ```
   {{borrower_email}}
   ```

   **Subject:**
   ```
   URGENT: Documents Still Needed for Your Loan Application
   ```

   **Content:**
   ```
   Dear {{borrower_name}},

   This is our second reminder regarding your loan application.

   Your application is currently {{completeness_score}}% complete and we still need:

   {{join(missing_documents; ", ")}}

   To avoid delays or potential rejection, please upload these documents within the next 24 hours.

   If you're having trouble obtaining any documents, please contact us immediately so we can assist you.

   Best regards,
   Loan Processing Team
   ```

   **Content Type:** `Text`

5. Click **"OK"**

---

### **Step 12: Update Database After Sending Second Reminder**

1. Click **"+"** after the Gmail module (Route 2)
2. Search for **"HTTP"**
3. Select **"HTTP" → "Make a request"**
4. Configure:

   **URL:**
   ```
   https://web-production-0a9f4.up.railway.app/update-reminder?loan_id={{loan_id}}
   ```

   **Method:** `POST`

   **Headers:**
   - **Name:** `X-API-Key`
   - **Value:** `YOUR_API_KEY_HERE`

5. Click **"OK"**

---

## ✅ Final Steps

### **Step 13: Save and Activate**

1. Click **"Save"** (bottom left)
2. Toggle the scenario to **"ON"**
3. The scenario will now run automatically every day at 9 AM

---

### **Step 14: Test It Now (Don't Wait for 9 AM!)**

1. Right-click the **Schedule module**
2. Select **"Run this module only"**
3. Watch the scenario run through all modules
4. Check if emails are sent (if you have incomplete loans in the system)

**If no emails sent:** That's normal if you don't have any incomplete loans yet!

---

## 🎯 Visual Flow Summary

```
[Schedule: Daily 9 AM]
        ↓
[HTTP: GET /incomplete-loans]
        ↓
[Parse JSON]
        ↓
[Iterator: Loop each loan]
        ↓
   [Router: Split into 2 branches]
        ↓                    ↓
   [Route 1]           [Route 2]
   Filter: reminder=0  Filter: reminder=1
        ↓                    ↓
   [Send Email #1]     [Send Email #2]
        ↓                    ↓
   [Update Database]   [Update Database]
```

---

## 📊 How the Logic Works

### **Reminder #1 Trigger:**
- Loan created more than 24 hours ago
- Completeness < 100%
- `reminder_count = 0`
- No previous reminders sent

### **Reminder #2 Trigger:**
- Reminder #1 was sent more than 24 hours ago
- Completeness still < 100%
- `reminder_count = 1`
- Only 1 reminder sent so far

### **Stop After 2 Reminders:**
- Once `reminder_count = 2`, no more automatic reminders
- Loan officer needs to manually follow up

---

## 🔧 Customization Options

### **Change Timing:**

**Send reminders at different times:**
- Edit Schedule module → Change time from 09:00 to whatever you want

**Change reminder intervals:**
- Currently: 24 hours between reminders
- To change: You'd need to modify the API logic in `simple_rag_api_with_db.py`
- Search for `>= 86400` (24 hours in seconds)
- Change to `>= 172800` for 48 hours, etc.

### **Customize Email Templates:**

Feel free to modify the email content in Gmail modules:
- Add your company logo
- Change tone (more formal/casual)
- Add phone number or support links
- Include specific instructions

### **Add More Reminders:**

Want a 3rd reminder?
1. Add Route 3 to the Router
2. Filter: `reminder_count = 2`
3. Add Gmail + Update Database modules
4. Change the API to allow `reminder_count = 3`

---

## 🚨 Troubleshooting

### **No emails being sent:**
- **Check:** Do you have incomplete loans in the database?
- **Test:** Run Scenario A first to upload some documents
- **Verify:** Visit `https://web-production-0a9f4.up.railway.app/incomplete-loans` in browser (will ask for auth, but you can test via Postman)

### **"Invalid API Key" error:**
- **Check:** Make sure X-API-Key header is set in ALL HTTP modules
- **Verify:** API key matches what's in Railway → Variables → API_KEY

### **"Loan not found" error:**
- **Check:** Make sure loan_id is being mapped correctly from Iterator
- **Test:** Run scenario and look at the data being passed to each module

### **Emails sent multiple times:**
- **Check:** Make sure the "Update Database" modules are running
- **Verify:** `/update-reminder` endpoint is being called successfully

---

## 📈 Monitoring Your Reminders

### **Check What Reminders Were Sent:**

1. Go to Railway → Your API
2. Check the audit log endpoint:
   ```
   GET https://web-production-0a9f4.up.railway.app/audit-log
   ```
3. Look for entries with `"category": "REMINDER"`

### **Check Loan Reminder Status:**

Query a specific loan:
```
GET https://web-production-0a9f4.up.railway.app/loans/{loan_id}
```

You'll see:
- `reminder_count`: How many reminders sent (0, 1, or 2)
- `last_reminder_sent`: Timestamp of last reminder

---

## 🎉 You're All Set!

Your automated reminder system is now:
- ✅ Checking daily for incomplete loans
- ✅ Sending Reminder #1 at 24 hours
- ✅ Sending Reminder #2 at 48 hours
- ✅ Tracking all reminders in the database
- ✅ Preventing duplicate reminders

**The system will:**
- Free up your time
- Improve document collection rates
- Speed up loan processing
- Provide better borrower experience

---

## 🔗 Related Documentation

- **Scenario A Setup:** Your existing email processing scenario
- **API Endpoints:** See `simple_rag_api_with_db.py` for all available endpoints
- **Database Schema:** See `database.py` for loan tracking fields

---

## 💡 Pro Tips

1. **Test with fake loans first** - Create test loans to verify reminders work
2. **Monitor for the first week** - Check Make.com execution history daily
3. **Adjust timing if needed** - You might want reminders at 24h/72h instead
4. **Add notifications** - Set up alerts in Make.com if scenario fails
5. **Track metrics** - Monitor how many borrowers respond after each reminder

---

**Questions or issues?** Check the troubleshooting section or review the Make.com execution logs!

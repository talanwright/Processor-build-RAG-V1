# Make.com Scenario B - Final Configuration Steps
## What to Do After Railway Deployment Completes

---

## ✅ Current Status

You have successfully built the scenario structure:
- ✅ Schedule (9 AM daily)
- ✅ HTTP module (get incomplete loans)
- ✅ Iterator (loop through loans)
- ✅ Router (2 branches)
- ✅ Route 1: Gmail → HTTP (First reminder)
- ✅ Route 2: Gmail → HTTP (Second reminder)

---

## 🔧 Configuration Needed (After Railway Deploys)

### **Step 1: Test the HTTP Module**

1. Go to your Make.com scenario
2. **Right-click** the HTTP module (#2)
3. Select **"Run this module only"**
4. Check the output - you should see:
   ```json
   {
     "incomplete_loans": [],
     "total_count": 0
   }
   ```
   (Empty array is fine - means no incomplete loans yet)

---

### **Step 2: Fix the Iterator Array Path**

1. Click on the **Iterator module** (#4)
2. Click in the **Array** field
3. Expand **"2. Data"**
4. Select **"incomplete_loans"** (not just "Data")
5. It should show: `2. Data > incomplete_loans`
6. Click **"Save"**

---

### **Step 3: Configure Route 1 Filter**

1. Click the **wrench icon** on Route 1
2. Click **"Set up a filter"**
3. Configure:
   - **Label:** `Should send first reminder`
   - **Condition:**
     - Click the field
     - Select from Iterator: `should_send_reminder_1`
     - **Operator:** `Equal to`
     - **Value:** `true`
4. Click **"OK"**

---

### **Step 4: Fix Route 1 Gmail Module**

1. Click the **Gmail module** on Route 1 (#6)
2. Update the fields:

**To:** (click field and map from Iterator)
- Select: `borrower_email`

**Subject:**
```
Reminder: Additional Documents Needed for Your Loan Application
```

**Content:**
```
Dear {{4.borrower_name}},

This is a friendly reminder that we're still waiting for some documents to complete your loan application.

Currently, your application is {{4.completeness_score}}% complete.

Missing documents:
{{join(4.missing_documents; ", ")}}

Please upload these documents as soon as possible to avoid delays in processing your loan.

If you have any questions, please don't hesitate to contact us.

Best regards,
Loan Processing Team
```

3. Click **"OK"**

---

### **Step 5: Fix Route 1 HTTP Update Module**

1. Click the **HTTP module** on Route 1 (#7)
2. Update the URL to include the loan_id from Iterator:

**URL:**
```
https://web-production-0a9f4.up.railway.app/update-reminder?loan_id={{4.loan_id}}
```

(Click in the URL field and map `loan_id` from Iterator module #4)

3. Make sure **Headers** has:
   - **Name:** `X-API-Key`
   - **Value:** Your Railway API key

4. Click **"OK"**

---

### **Step 6: Configure Route 2 Filter**

1. Click the **wrench icon** on Route 2
2. Click **"Set up a filter"**
3. Configure:
   - **Label:** `Should send second reminder`
   - **Condition:**
     - Click the field
     - Select from Iterator: `should_send_reminder_2`
     - **Operator:** `Equal to`
     - **Value:** `true`
4. Click **"OK"**

---

### **Step 7: Fix Route 2 Gmail Module**

1. Click the **Gmail module** on Route 2 (#8)
2. Update the fields:

**To:**
- Map: `borrower_email` from Iterator

**Subject:**
```
URGENT: Documents Still Needed for Your Loan Application
```

**Content:**
```
Dear {{4.borrower_name}},

This is our second reminder regarding your loan application.

Your application is currently {{4.completeness_score}}% complete and we still need:

{{join(4.missing_documents; ", ")}}

To avoid delays or potential rejection, please upload these documents within the next 24 hours.

If you're having trouble obtaining any documents, please contact us immediately so we can assist you.

Best regards,
Loan Processing Team
```

3. Click **"OK"**

---

### **Step 8: Fix Route 2 HTTP Update Module**

1. Click the **HTTP module** on Route 2 (#9)
2. Update the URL:

**URL:**
```
https://web-production-0a9f4.up.railway.app/update-reminder?loan_id={{4.loan_id}}
```

3. Headers should have your API key
4. Click **"OK"**

---

## 🧪 Testing the Complete Scenario

### **Option 1: Test with Real Data (After You Have Loans)**

1. Make sure you have at least one incomplete loan in the system
2. **Right-click** the Schedule module
3. Select **"Run this module only"**
4. Watch the scenario execute
5. Check if:
   - HTTP fetches incomplete loans ✅
   - Iterator loops through each ✅
   - Router filters correctly ✅
   - Emails are sent ✅
   - Database is updated ✅

---

### **Option 2: Test with Manual Data (Before You Have Loans)**

If you don't have any incomplete loans yet:

1. Skip the HTTP module
2. **Right-click** the Iterator
3. Select **"Choose where to start"**
4. Manually enter test data:
```json
[
  {
    "loan_id": "test123",
    "borrower_email": "your-email@gmail.com",
    "borrower_name": "Test Borrower",
    "completeness_score": 60,
    "missing_documents": ["pay_stub", "tax_return"],
    "should_send_reminder_1": true,
    "should_send_reminder_2": false,
    "reminder_count": 0
  }
]
```
5. Run from the Iterator forward
6. You should receive a test email!

---

## 🎯 Final Checklist

Before activating the scenario:

- [ ] Railway deployment completed successfully
- [ ] API shows version 3.0.0 and "PostgreSQL"
- [ ] HTTP module tested - returns data correctly
- [ ] Iterator array path fixed to `incomplete_loans`
- [ ] Route 1 filter configured (`should_send_reminder_1 = true`)
- [ ] Route 2 filter configured (`should_send_reminder_2 = true`)
- [ ] All Gmail modules have correct email mappings
- [ ] All HTTP update modules have correct loan_id in URL
- [ ] Test run completed successfully
- [ ] Emails received in inbox

---

## 🚀 Activate the Scenario

Once everything is tested and working:

1. Click **"Save"**
2. Toggle the scenario **"ON"**
3. Confirm the schedule: **9:00 AM daily**
4. Done! It will run automatically every day

---

## 📊 Monitoring

### **Check Execution History:**
1. Go to Make.com scenario
2. Click **"History"** tab
3. See all past executions
4. Check for errors or issues

### **Check What Reminders Were Sent:**
Visit Railway API:
```
GET https://web-production-0a9f4.up.railway.app/audit-log
```
Look for entries with "REMINDER" category.

---

## 🐛 Common Issues & Fixes

### **"No data" error on Iterator:**
- Fix: Make sure Iterator array is set to `2. Data > incomplete_loans` (not just `2. Data`)

### **Emails not sending:**
- Check: Filter conditions are correctly configured
- Check: `should_send_reminder_1` and `should_send_reminder_2` fields exist in data

### **"Invalid API Key" error:**
- Check: X-API-Key header is set in ALL HTTP modules (#2, #7, #9)
- Check: API key matches Railway environment variable

### **Database not updating:**
- Check: loan_id is correctly mapped in URL
- Check: HTTP module (#7, #9) shows successful response (200 OK)

---

## 📞 Support

If you encounter issues:
1. Check Make.com execution logs (History tab)
2. Check Railway deployment logs
3. Check API audit log endpoint
4. Review this guide step-by-step

---

**You're almost done! Just need to wait for Railway to finish deploying, then follow these steps to complete the configuration!**

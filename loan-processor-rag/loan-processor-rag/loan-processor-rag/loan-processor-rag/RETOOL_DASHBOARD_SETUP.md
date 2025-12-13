# 🎯 Retool Dashboard Setup Guide - Complete Instructions

## Overview
This guide will walk you through building a professional loan officer dashboard using Retool. Total time: 2-3 hours.

**What you'll build:**
- 📊 Loan list table with all active loans
- 📁 Click any loan to see details and documents
- ⬇️ Download documents with one click
- 🔍 Search and filter loans
- 🔐 Secure authentication for loan officers

---

## STEP 1: Create Retool Account (5 minutes)

### 1.1 Sign Up
1. Go to https://retool.com
2. Click **"Start building for free"**
3. Sign up with your email (or Google account)
4. Choose **"Cloud-hosted"** (easier, no setup)
5. Complete the onboarding questions:
   - **Use case:** Internal tool for team
   - **Company size:** 1-10
   - **Role:** Developer

### 1.2 Create Your First App
1. You'll land on the Retool dashboard
2. Click **"Create new" → "App"**
3. Name it: **"Loan Officer Dashboard"**
4. Click **"Create app"**

You'll now see the Retool app builder (drag-and-drop interface)

---

## STEP 2: Connect Your Railway API (10 minutes)

### 2.1 Create API Resource
1. In the Retool app, look at the bottom panel
2. Click **"+ Create New" → "Resource"**
3. Select **"REST API"**

### 2.2 Configure API Connection
Fill in these details:

**Base URL:**
```
https://web-production-bbd3.up.railway.app
```

**Headers:**
- Click **"+ Add"** to add a header
- **Key:** `X-API-Key`
- **Value:** `[YOUR_RAILWAY_API_KEY]` ← Get this from Railway environment variables

**Name this resource:** `Loan Processor API`

**Click "Create resource"**

### 2.3 Get Your Railway API Key
1. Open Railway dashboard: https://railway.app
2. Click on your **"web"** service
3. Go to **"Variables"** tab
4. Find `API_KEY` and copy the value
5. Paste it into the Retool header value above

---

## STEP 3: Create Loan List Query (10 minutes)

### 3.1 Add First Query
1. In the bottom panel, click **"+ New" → "Resource query"**
2. Select **"Loan Processor API"** (the resource you just created)
3. Name the query: `listLoans`

### 3.2 Configure Query
**Method:** `GET`
**Endpoint:** `/loans`

**Click "Save"**

### 3.3 Test Query
1. Click **"Run"** (or Preview)
2. You should see JSON response like:
```json
{
  "loans": [
    {
      "loan_id": "johnsmith@email.com",
      "document_count": 3,
      "created_date": "2025-11-02T10:30:00",
      "last_updated": "2025-11-02T14:20:00",
      "status": "active"
    }
  ],
  "total": 1
}
```

**If you get an error:** Check your API key is correct

---

## STEP 4: Build Loan List Table (15 minutes)

### 4.1 Add Table Component
1. In the left sidebar, search for **"Table"**
2. Drag it onto the canvas (main area)
3. Resize it to take up most of the screen

### 4.2 Connect Table to Data
1. Click on the table to select it
2. In the right panel, find **"Data source"**
3. Delete the example data
4. Enter: `{{ listLoans.data.loans }}`

Your table should now show your loans!

### 4.3 Format Table Columns
Click on the table, then in the right panel customize columns:

**loan_id column:**
- **Display name:** "Borrower Email"
- **Type:** Text

**document_count column:**
- **Display name:** "Documents"
- **Type:** Number

**last_updated column:**
- **Display name:** "Last Updated"
- **Type:** Date/Time
- **Format:** "MM/DD/YYYY HH:mm"

**status column:**
- **Display name:** "Status"
- **Type:** Badge
- **Colors:**
  - active → green
  - pending → yellow

### 4.4 Make Table Sortable & Searchable
In table properties (right panel):

- ✅ Enable **"Enable sorting"**
- ✅ Enable **"Enable filtering"**
- ✅ Enable **"Enable search"**
- ✅ Enable **"Enable pagination"** (if you have many loans)

### 4.5 Add Refresh Button
1. Drag a **"Button"** component above the table
2. **Button text:** "🔄 Refresh"
3. **Event handler:** Click **"+ Add"** → **"Control query"** → Select `listLoans` → **"Run query"**

---

## STEP 5: Create Loan Details Query (10 minutes)

### 5.1 Add Second Query
1. Bottom panel: **"+ New" → "Resource query"**
2. Select **"Loan Processor API"**
3. Name: `getLoanDetails`

### 5.2 Configure Query
**Method:** `GET`
**Endpoint:** `/loans/{{ table1.selectedRow.data.loan_id }}`

(Replace `table1` with your table's actual name - check the left sidebar)

**This query will run when you click a row in the table!**

### 5.3 Set Query to Run on Row Click
1. Click on your table
2. **Event handlers** section (right panel)
3. **Row clicked** → **"+ Add"**
4. **"Control query"** → Select `getLoanDetails` → **"Run query"**

---

## STEP 6: Build Loan Details Panel (20 minutes)

### 6.1 Add Container
1. Drag a **"Container"** component to the right side of your table
2. Make it about 40% of the screen width
3. This will show loan details when a row is clicked

### 6.2 Add Loan Info Section
Inside the container, drag these components:

**Text component #1:**
- **Text:** `## Loan Details`
- **Format:** Markdown

**Text component #2:**
- **Text:** `**Borrower:** {{ getLoanDetails.data.loan_id }}`

**Text component #3:**
- **Text:** `**Documents:** {{ getLoanDetails.data.document_count }}`

**Text component #4:**
- **Text:** `**Created:** {{ moment(getLoanDetails.data.created_date).format('MM/DD/YYYY HH:mm') }}`

### 6.3 Add Analysis Section
Add more text components:

```
### Analysis Results

**Completeness Score:** {{ (getLoanDetails.data.analysis.completeness_score * 100).toFixed(0) }}%

**Risk Score:** {{ (getLoanDetails.data.analysis.risk_score * 100).toFixed(0) }}%

**Status:** {{ getLoanDetails.data.analysis.status }}
```

### 6.4 Show Missing Documents
Add a **"List View"** component:

**Data source:**
```
{{ getLoanDetails.data.analysis.missing_documents }}
```

**Item template:** Customize to show:
- Document type
- Description
- Urgency (color code: red = high, yellow = medium)

---

## STEP 7: Add Document Download Table (20 minutes)

### 7.1 Add Documents Table
Inside the container, below the analysis section:

1. Drag a new **"Table"** component
2. Name it: `documentsTable`

### 7.2 Connect to Documents Data
**Data source:**
```
{{ getLoanDetails.data.documents }}
```

### 7.3 Format Document Columns
**filename column:**
- **Display name:** "Document"
- **Type:** Text

**size_mb column:**
- **Display name:** "Size (MB)"
- **Type:** Number
- **Format:** 2 decimals

**uploaded_date column:**
- **Display name:** "Uploaded"
- **Type:** Date/Time

### 7.4 Add Download Button Column
1. Click on the documents table
2. In columns section, click **"+ Add column"**
3. **Column type:** "Button"
4. **Column name:** "download"
5. **Button text:** "⬇️ Download"

### 7.5 Create Download Query
1. Bottom panel: **"+ New" → "Resource query"**
2. Select **"Loan Processor API"**
3. Name: `downloadDocument`

**Method:** `GET`
**Endpoint:**
```
/loans/{{ getLoanDetails.data.loan_id }}/documents/{{ documentsTable.selectedRow.data.filename }}
```

**Response type:** Change to **"Binary"** or **"File"**

### 7.6 Wire Download Button
1. Click on the documents table
2. Find the **download** column settings
3. **Event handler:** Button clicked → **"Download file"**
4. **File data:** `{{ downloadDocument.data }}`
5. **File name:** `{{ documentsTable.selectedRow.data.filename }}`

---


## STEP 8: Add Search & Filters (15 minutes)

### 8.1 Add Search Bar
1. Above the main table, drag a **"Text Input"** component
2. **Placeholder:** "Search by borrower email..."
3. **Name:** `searchInput`

### 8.2 Filter Table by Search
1. Click on main loans table
2. **Data source:** Change to:
```javascript
{{
  listLoans.data.loans.filter(loan =>
    loan.loan_id.toLowerCase().includes(searchInput.value.toLowerCase())
  )
}}
```

### 8.3 Add Status Filter (Optional)
1. Drag a **"Select"** component next to search
2. **Options:**
   - All
   - Active
   - Pending
   - Complete
3. Filter table based on selection

---

## STEP 9: Add Auto-Refresh (10 minutes)

### 9.1 Add Refresh Timer
1. Drag a **"Timer"** component (from Components)
2. **Interval:** 30000 (30 seconds)
3. **Auto-start:** Yes

### 9.2 Configure Timer Action
1. Click on timer
2. **Event handler:** Timer triggers → **"Control query"** → `listLoans` → **"Run query"**

**Now your dashboard auto-refreshes every 30 seconds!**

---

## STEP 10: Style the Dashboard (15 minutes)

### 10.1 Add Header
1. Drag a **"Container"** to the very top
2. **Background color:** Your client's brand color
3. Add a **"Text"** component inside:
   - **Text:** `# 📊 Loan Officer Dashboard`
   - **Color:** White
   - **Font size:** 24px

### 10.2 Add Stats Cards (Optional)
Above the table, add **"Statistic"** components:

**Card 1 - Total Loans:**
```
{{ listLoans.data.total }}
```

**Card 2 - Pending Docs:**
```
{{ listLoans.data.loans.filter(l => l.status === 'pending').length }}
```

**Card 3 - Complete:**
```
{{ listLoans.data.loans.filter(l => l.status === 'complete').length }}
```

### 10.3 Polish the Layout
- Add spacing between components
- Align items nicely
- Use consistent colors
- Add borders/shadows to containers

---

## STEP 11: Add Authentication (10 minutes)

### 11.1 Enable Login
1. Click **"⚙️ Settings"** (top right)
2. Go to **"Authentication"** section
3. Enable **"Require users to log in"**

### 11.2 Add Users
1. Go to **"Settings" → "Users & groups"**
2. Click **"+ Add user"**
3. Enter loan officer's email
4. Set **role:** "User" (can view) or "Editor" (can edit dashboard)
5. Click **"Send invite"**

They'll receive an email to set their password!

### 11.3 Create User Groups (Optional)
If you have multiple loan officers:
1. **"Users & groups" → "Groups" → "Create group"**
2. Name: "Loan Officers"
3. Add all loan officers to this group
4. Set permissions: Can view apps, cannot edit

---

## STEP 12: Test Everything (10 minutes)

### 12.1 Test Loan List
- ✅ Table loads with all loans
- ✅ Search works
- ✅ Sorting works
- ✅ Refresh button updates data

### 12.2 Test Loan Details
- ✅ Click a row → Details panel appears
- ✅ Analysis scores show correctly
- ✅ Missing documents list appears

### 12.3 Test Document Downloads
- ✅ Click a document's download button
- ✅ File downloads correctly
- ✅ Filename is correct

### 12.4 Test Authentication
- ✅ Log out
- ✅ Try to access dashboard → Redirects to login
- ✅ Log in with loan officer account → Works

---

## STEP 13: Deploy to Your Client (5 minutes)

### 13.1 Publish the App
1. Click **"🚀 Release"** (top right)
2. Add release notes: "Initial dashboard v1.0"
3. Click **"Release to production"**

### 13.2 Get Shareable Link
1. Click **"Share"** (top right)
2. Copy the app URL: `https://yourcompany.retool.com/apps/loan-dashboard`

### 13.3 Send to Client
Send them:
- Dashboard URL
- Their login credentials
- Quick start guide (see below)

---

## 📧 QUICK START GUIDE FOR YOUR CLIENT

Send this to your loan officers:

```
Subject: Your New Loan Dashboard is Ready!

Hi [Loan Officer Name],

Your new automated loan processing dashboard is live!

🔗 Dashboard URL: https://[your-company].retool.com/apps/loan-dashboard

📧 Login Email: [their-email@company.com]
🔑 Password: Check your email for the Retool invite

HOW TO USE IT:

1. LOG IN
   - Visit the dashboard URL
   - Enter your email and password

2. VIEW LOANS
   - All active loan applications appear in the table
   - Click any row to see full details

3. CHECK ANALYSIS
   - Completeness score (% of required docs)
   - Missing documents list
   - Risk assessment

4. DOWNLOAD DOCUMENTS
   - Scroll to the documents section
   - Click "⬇️ Download" next to any file
   - File downloads to your computer

5. SEARCH & FILTER
   - Use the search bar to find borrowers
   - Sort by any column
   - Dashboard auto-refreshes every 30 seconds

Questions? Reply to this email!

Best regards,
[Your Name]
```

---

## 🎨 ADVANCED CUSTOMIZATION (Optional)

### Add Email Template Preview
Create a new tab in your app to show the generated email templates

### Add Notes Field
Allow loan officers to add notes to each loan

### Add Status Updates
Add dropdown to change loan status (pending → in review → approved)

### Add Notifications
Use Retool workflows to send emails when new loans arrive

### Add Charts
Add a **"Chart"** component showing:
- Loans per day
- Average completion score
- Processing time stats

---

## 🔐 SECURITY CHECKLIST

Before giving to client, verify:

- ✅ API key is stored in Retool (not visible in app)
- ✅ Users must log in to access dashboard
- ✅ Each loan officer has their own account
- ✅ Railway API only accepts requests with API key
- ✅ Document downloads require authentication
- ✅ No sensitive data visible in browser console

---

## 🆘 TROUBLESHOOTING

### "Error: Unauthorized" when running queries
**Fix:** Check your API key in Retool resource settings matches Railway

### Table shows "Loading..." forever
**Fix:**
1. Check the query ran successfully (bottom panel)
2. Verify data path: `{{ listLoans.data.loans }}`
3. Click "Run" on the query manually

### Download button does nothing
**Fix:**
1. Check the downloadDocument query endpoint is correct
2. Verify response type is set to "Binary" or "File"
3. Check event handler is configured correctly

### Can't see loan details when clicking row
**Fix:**
1. Verify getLoanDetails query has correct endpoint
2. Check event handler on table: Row clicked → Run getLoanDetails
3. Make sure container is visible (not hidden)

### Dashboard looks broken on mobile
**Fix:** Retool is desktop-first. For mobile:
1. Create a separate mobile-optimized layout
2. Or use Retool Mobile app builder

---

## 📊 WHAT YOU'VE BUILT

Your client now has a professional dashboard with:

✅ **Real-time loan monitoring** - See all active loans
✅ **Automated analysis** - Completeness & risk scores
✅ **Document management** - Download any document
✅ **Secure access** - User authentication required
✅ **Search & filter** - Find loans quickly
✅ **Auto-refresh** - Updates every 30 seconds
✅ **Professional UI** - Clean, modern interface

**Market value of this dashboard:** $5,000 - $10,000
**Your time investment:** 2-3 hours
**Monthly cost:** Free (or $10/user for teams)

---

## 🚀 NEXT STEPS

1. **Test with real data** - Have Make.com process a test email
2. **Get client feedback** - Show them the dashboard, get input
3. **Add their branding** - Logo, colors, company name
4. **Train loan officers** - 15-minute walkthrough
5. **Monitor usage** - Check Retool analytics

---

## 💡 TIPS FOR YOUR CLIENT DEMO

When showing the client:

1. **Start with a test loan** - Show the full flow:
   - Email arrives
   - Make.com processes it
   - Documents appear in dashboard
   - Analysis shows completion score

2. **Highlight time savings:**
   - "Before: 30 minutes per loan"
   - "After: 30 seconds + instant dashboard view"

3. **Show security features:**
   - Authentication required
   - API key protection
   - Audit logging

4. **Demo document download:**
   - Click loan
   - See all documents
   - Download in one click

5. **Explain auto-refresh:**
   - "Dashboard updates automatically"
   - "Always shows latest data"

---

## 📞 SUPPORT

If you get stuck:
- Retool docs: https://docs.retool.com
- Retool community: https://community.retool.com
- Video tutorials: https://retool.com/video-tutorials

---

**You're now ready to build your Retool dashboard! Start with Step 1 and work through each section. It should take 2-3 hours total.**

Good luck! 🚀

# DEPLOY TO RENDER - STEP BY STEP (10 MINUTES)

## Why Render Instead of Railway?

Railway keeps failing because:
- Your app uses ML libraries (chromadb, sentence-transformers)
- Railway's free tier has short build timeouts
- The image size exceeds their limits

**Render handles Python ML apps perfectly** - it's designed for this.

---

## Step 1: Create Render Account (2 minutes)

1. Go to https://render.com
2. Click **"Get Started"**
3. Click **"Sign Up with GitHub"**
4. Authorize Render to access your GitHub repos

---

## Step 2: Create New Web Service (3 minutes)

1. Once logged in, click **"New +"** button (top right)
2. Select **"Web Service"**
3. Click **"Connect account"** if prompted to link GitHub
4. Find your repo: `Processor-build-RAG-V1`
5. Click **"Connect"**

---

## Step 3: Configure the Service (2 minutes)

Render will show you a configuration screen. Fill in:

**Name:** `loan-processor-api` (or whatever you want)

**Region:** Oregon (US West)

**Branch:** `main`

**Root Directory:** `loan-processor-rag`

**Environment:** `Python 3`

**Build Command:**
```
pip install --no-cache-dir -r requirements.txt
```

**Start Command:**
```
uvicorn simple_rag_api:app --host 0.0.0.0 --port $PORT
```

**Plan:** Free

---

## Step 4: Add Environment Variable (1 minute)

1. Scroll down to **"Environment Variables"**
2. Click **"Add Environment Variable"**
3. Add:
   - **Key:** `API_KEY`
   - **Value:** (click "Generate" or type a random 32-character string)
4. **IMPORTANT:** Copy this API_KEY value - you'll need it for Retool!

---

## Step 5: Deploy! (5-10 minutes)

1. Click **"Create Web Service"** at the bottom
2. Render will start building your app
3. Watch the logs - it will take 5-10 minutes to install ML dependencies
4. Wait for status to show **"Live"** with a green dot

---

## Step 6: Get Your API URL

Once deployed, you'll see a URL like:
```
https://loan-processor-api-xxxx.onrender.com
```

**Copy this URL!** This is what you'll use in Retool.

---

## Step 7: Fix Retool (2 minutes)

Now go to Retool:

1. Open your `Loan processor API` resource
2. Change the Base URL to your new Render URL:
   ```
   https://loan-processor-api-xxxx.onrender.com
   ```

3. Open your `downloadDocument` query
4. Add header:
   - **Key:** `X-API-Key`
   - **Value:** (the API_KEY you copied from Render)

5. Click **"Test"** - it should work!

---

## Troubleshooting

**Build is taking too long?**
- This is normal! ML dependencies take 5-10 minutes to install
- Be patient, let it finish

**Deploy failed?**
- Check the logs in Render
- Look for specific error messages
- Send me a screenshot

**Retool still showing error?**
- Make sure you updated BOTH the base URL AND added the API key header
- Check that the API_KEY matches exactly

---

## You're Done!

Once this works:
- Your API will stay online (Render free tier is reliable)
- It auto-deploys when you push to GitHub
- No more Railway timeout issues

**Delete your Railway project** to avoid confusion.

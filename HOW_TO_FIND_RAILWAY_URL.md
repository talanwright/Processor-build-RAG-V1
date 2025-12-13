# How to Find Your Railway Base URL

## Method 1: From Railway Dashboard (Easiest)

1. Go to https://railway.app
2. Click on your project (the one running your loan processor API)
3. Click on the **service/deployment** (should say "web" or your service name)
4. Look for **"Deployments"** tab
5. You'll see a URL that looks like:
   ```
   https://web-production-XXXXXXX.up.railway.app
   ```
   or
   ```
   https://PROJECTNAME.up.railway.app
   ```

6. **Copy that entire URL** - that's your BASE_URL!

## Method 2: From Railway Settings Tab

1. Go to https://railway.app
2. Click your project
3. Click **"Settings"** tab
4. Scroll down to **"Domains"** section
5. You'll see your Railway-provided domain listed there
6. Copy the full URL (starts with `https://`)

## Method 3: Check Your Current API

You probably already have this URL saved somewhere! It's the same URL you use in Make.com for your HTTP modules.

**Check your Make.com scenario:**
1. Open Make.com
2. Look at any HTTP module that calls your API
3. The URL there is your BASE_URL!
4. Example: If Make.com calls `https://web-production-0a9f4.up.railway.app/upload-documents`
5. Your BASE_URL is: `https://web-production-0a9f4.up.railway.app`

## Method 4: Test in Browser

1. Go to your Railway dashboard
2. Find the public URL
3. Open it in a browser
4. You should see JSON like:
   ```json
   {
     "message": "Loan Processor RAG API (SECURED with PostgreSQL)",
     "status": "running",
     "version": "3.1.0"
   }
   ```
5. The URL in your browser's address bar is your BASE_URL!

## What It Looks Like

Your BASE_URL will be one of these formats:

✅ `https://web-production-abc123.up.railway.app`
✅ `https://your-project-name.up.railway.app`
✅ `https://random-name-production.up.railway.app`

## Common Mistakes to Avoid

❌ Don't include `/` at the end: `https://your-app.up.railway.app/` (WRONG)
✅ Just the domain: `https://your-app.up.railway.app` (CORRECT)

❌ Don't include endpoint paths: `https://your-app.up.railway.app/generate-email` (WRONG)
✅ Just the base: `https://your-app.up.railway.app` (CORRECT)

## Once You Have It

Add it to Railway as an environment variable:

1. Railway Dashboard → Your Project
2. **Variables** tab
3. Click **"New Variable"**
4. Variable: `BASE_URL`
5. Value: `https://your-actual-railway-url.up.railway.app`
6. Click **"Add"**

The app will automatically use this when generating secure links in emails!

## Still Can't Find It?

Tell me:
1. What's the URL you use in Make.com to call your API?
2. Or share a screenshot of your Railway dashboard

I can help you identify it!

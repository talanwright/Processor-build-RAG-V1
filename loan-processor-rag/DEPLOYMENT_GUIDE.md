# Deployment Guide - Loan Processor RAG System

## Problem: Local Development vs Production Use

**Issue:** The RAG system currently runs on your local machine (`http://192.168.1.25:8000`), but your client needs it accessible 24/7 from anywhere.

**Solution:** Deploy to a cloud service for permanent access.

---

## Recommended Deployment Options

### 🚀 Option 1: Railway (Easiest - FREE)

**Why Railway:**
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Permanent URL
- ✅ Auto-deploys from GitHub
- ✅ Perfect for FastAPI apps

**Steps:**
1. **Push to GitHub:**
   ```bash
   cd "/Users/talanwright/Test RAG/loan-processor-rag"
   git init
   git add .
   git commit -m "Initial loan processor RAG system"
   git remote add origin https://github.com/YOUR_USERNAME/loan-processor-rag.git
   git push -u origin main
   ```

2. **Deploy to Railway:**
   - Go to https://railway.app
   - Sign up with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your loan-processor-rag repository
   - Railway auto-detects Python and deploys

3. **Get Your Permanent URL:**
   - Railway provides: `https://your-app-name.up.railway.app`
   - Use this URL in Make.com instead of local IP

**Cost:** FREE (with limits), $5/month for unlimited usage

---

### 🌐 Option 2: Heroku (Popular)

**Steps:**
1. **Install Heroku CLI:**
   ```bash
   brew install heroku/brew/heroku
   ```

2. **Deploy:**
   ```bash
   cd "/Users/talanwright/Test RAG/loan-processor-rag"
   git init
   git add .
   git commit -m "Initial commit"
   heroku create your-loan-processor
   git push heroku main
   ```

3. **Get URL:**
   - Heroku provides: `https://your-loan-processor.herokuapp.com`

**Cost:** $7/month (no free tier anymore)

---

### 🏠 Option 3: VPS Server (Most Control)

**Recommended Providers:**
- **DigitalOcean:** $6/month droplet
- **Linode:** $5/month server
- **AWS EC2:** Variable pricing
- **Google Cloud:** Variable pricing

**Setup Steps:**
1. **Rent a VPS**
2. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   ```
3. **Upload your code**
4. **Set up reverse proxy with nginx**
5. **Get permanent IP/domain**

**Cost:** $5-10/month + domain name

---

### 💰 Option 4: ngrok Pro (Quick Fix)

**For immediate solution:**
1. **Upgrade to ngrok Pro:** $8/month
2. **Get permanent subdomain:** `https://your-company.ngrok.io`
3. **Run from any computer:** No deployment needed

**Pros:**
- Immediate solution
- No code changes needed
- Works from your current setup

**Cons:**
- Still requires a computer running 24/7
- More expensive than cloud hosting

---

## 🎯 RECOMMENDED: Deploy to Railway

**I recommend Railway because:**
- **FREE to start**
- **Easiest deployment**
- **Perfect for your use case**
- **Automatic HTTPS**
- **No server management**

### Railway Deployment Steps:

1. **Create GitHub Repository:**
   ```bash
   cd "/Users/talanwright/Test RAG/loan-processor-rag"
   git init
   git add .
   git commit -m "Loan processor RAG system"
   ```

2. **Push to GitHub:**
   - Create new repo at github.com
   - Push your code

3. **Deploy to Railway:**
   - Sign up at railway.app
   - Connect GitHub
   - Deploy repository
   - Get permanent URL

4. **Update Make.com:**
   - Replace `http://192.168.1.25:8000` with Railway URL
   - Example: `https://loan-processor-abc123.up.railway.app`

---

## File Changes for Deployment

**✅ Already created these files for you:**

1. **`requirements.txt`** - Python dependencies
2. **`Procfile`** - Tells server how to run app
3. **`runtime.txt`** - Specifies Python version

**✅ Your `simple_rag_api.py` is deployment-ready**

---

## Testing Deployment

**After deployment, test these endpoints:**

1. **Health Check:**
   ```
   GET https://your-app.railway.app/
   ```

2. **Loan Analysis:**
   ```
   POST https://your-app.railway.app/analyze-loan
   ```

3. **Stats:**
   ```
   GET https://your-app.railway.app/stats
   ```

---

## Security for Production

**Before going live:**

1. **Add API Authentication:**
   ```python
   from fastapi import Header, HTTPException

   API_KEY = "your-secret-key"

   async def verify_api_key(x_api_key: str = Header()):
       if x_api_key != API_KEY:
           raise HTTPException(status_code=401, detail="Invalid API key")
   ```

2. **Environment Variables:**
   ```python
   import os
   API_KEY = os.getenv("API_KEY", "default-key")
   ```

3. **Rate Limiting:**
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

4. **CORS Configuration:**
   ```python
   allow_origins=["https://yourdomain.com"]  # Not "*"
   ```

---

## Make.com Integration After Deployment

**Update your Make.com scenario:**

1. **Replace all URLs:**
   ```
   OLD: http://192.168.1.25:8000/analyze-loan
   NEW: https://your-app.railway.app/analyze-loan
   ```

2. **Add API Key Header** (if implemented):
   ```
   Headers:
   X-API-Key: your-secret-key
   ```

3. **Test the complete workflow**

---

## Cost Comparison

| Option | Monthly Cost | Setup Time | Reliability |
|--------|-------------|------------|-------------|
| Railway Free | $0 | 15 min | High |
| Railway Pro | $5 | 15 min | High |
| Heroku | $7 | 20 min | High |
| DigitalOcean | $6 | 2 hours | High |
| ngrok Pro | $8 | 5 min | Medium |

---

## Next Steps

**Choose your deployment method:**

1. **Quick Start (Railway):** Follow Railway steps above
2. **Full Control (VPS):** Rent a server and deploy manually
3. **Immediate Fix (ngrok Pro):** Upgrade ngrok account

**After deployment:**
1. Update Make.com with new URL
2. Test complete workflow
3. Add security features
4. Monitor usage and performance

**Your client will have a permanent, reliable loan processing system!** 🎉
# IP Whitelisting Setup Guide

IP whitelisting adds an extra layer of security by only allowing requests from trusted IP addresses.

---

## 🔍 Step 1: Find the IP Addresses

### For Make.com:
1. **Option A:** Check Make.com documentation
   - Go to Make.com Help Center
   - Search for "webhook IP addresses" or "outbound IPs"
   - Copy the list of IPs

2. **Option B:** Check your audit logs
   - After Make.com makes a request, check `/audit-log` endpoint
   - Look for the IP address in the logs
   - Add that IP to whitelist

### For Retool:
1. Go to Retool Settings → Security
2. Look for "Outbound IP addresses" or similar
3. Copy the list of IPs

OR check Retool documentation: https://docs.retool.com/docs/ip-allowlists

### For Your IP (Optional):
1. Go to: https://whatismyipaddress.com/
2. Copy your IPv4 address
3. Add it to the whitelist (optional, for testing)

---

## ⚙️ Step 2: Add IPs to Your Code

Open `simple_rag_api.py` and find this section (around line 68):

```python
ALLOWED_IPS = [
    # Make.com webhook IPs (update with actual IPs from Make.com)
    # You can find these in Make.com documentation
    # Example: "34.89.123.456", "34.89.123.457"

    # Retool IPs (update with actual IPs from Retool)
    # You can find these in Retool settings
    # Example: "52.72.123.456", "52.72.123.457"

    # Your office/home IP (optional)
    # Find yours at: https://whatismyipaddress.com/
    # Example: "203.0.113.45"
]
```

Replace with your actual IPs:

```python
ALLOWED_IPS = [
    # Make.com IPs (example - replace with real ones)
    "34.89.123.45",
    "34.89.123.46",

    # Retool IPs (example - replace with real ones)
    "52.72.89.12",
    "52.72.89.13",

    # Your IP (optional for testing)
    "203.0.113.45",
]
```

---

## ✅ Step 3: Enable IP Whitelisting

In the same file, change this line (around line 83):

```python
ENABLE_IP_WHITELIST = False  # Currently disabled
```

To:

```python
ENABLE_IP_WHITELIST = True  # Now enabled!
```

---

## 🚀 Step 4: Deploy

```bash
git add simple_rag_api.py
git commit -m "Enable IP whitelisting for production security"
git push
```

Railway will automatically redeploy.

---

## 🧪 Step 5: Test

After deployment:

1. **Test from Make.com** - Should work (IP is whitelisted)
2. **Test from Retool** - Should work (IP is whitelisted)
3. **Test from random location** - Should be blocked with 403 error

---

## 📊 Monitoring

Check your audit logs to see blocked IPs:

```bash
# View audit log (use your actual API URL and key)
curl -H "X-API-Key: YOUR_API_KEY" https://your-api.railway.app/audit-log
```

Look for entries with `"action": "IP_BLOCKED"`

---

## ⚠️ Important Notes

### When to Use IP Whitelisting:
✅ Production environment with real client data
✅ When you have static IPs from Make.com/Retool
✅ For extra security layer

### When NOT to Use:
❌ Development/testing (IPs change frequently)
❌ If Make.com/Retool don't provide static IPs
❌ If you need to access from multiple locations

### Backup Plan:
If you get locked out:
1. Go to Railway → Variables
2. Add temporary variable: `ENABLE_IP_WHITELIST=False`
3. This overrides the code setting
4. Fix your IP list, then remove the variable

---

## 🔒 Current Security Stack (With IP Whitelist)

1. **IP Whitelist** ← NEW! (You're adding this)
2. **API Key Authentication**
3. **Rate Limiting**
4. **Data Encryption**
5. **File Encryption**
6. **Audit Logging**
7. **CORS Restrictions**

Your system is now **enterprise-grade secure**! 🎉

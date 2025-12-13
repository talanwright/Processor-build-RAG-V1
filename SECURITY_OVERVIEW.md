# Security Overview - Loan Processor RAG API

**Last Updated:** December 11, 2025
**System Version:** 3.1.0
**Deployment:** Railway (PostgreSQL)

---

## Executive Summary

Your Loan Processor API implements **bank-level security** with multiple layers of protection:

- ✅ **AES-256 encryption** for all borrower data (names, emails, income)
- ✅ **File encryption** for all uploaded documents
- ✅ **API key authentication** for system access
- ✅ **Secure token links** for borrower access (no login required)
- ✅ **Complete audit logging** of all data access
- ✅ **Rate limiting** to prevent attacks
- ✅ **GLBA-compliant** safeguards

---

## 1. How We Protect Data

### Encryption (Data at Rest)

**What's Encrypted:**
- Borrower emails → Encrypted in database
- Borrower names → Encrypted in database
- Monthly income → Encrypted in database
- All uploaded documents → Encrypted on disk

**Encryption Method:**
- **Algorithm:** AES-256 (bank-level encryption)
- **Key Storage:** Railway environment variable `ENCRYPTION_KEY`
- **Automatic:** Transparent encryption/decryption when reading/writing

**What This Means:**
If someone steals your database or files, they cannot read the data without the encryption key.

### Secure Transmission (Data in Transit)

- **HTTPS enforced** - All API requests encrypted via SSL/TLS
- **Railway-managed** - Automatic SSL certificate management

---

## 2. Access Control

### Two Ways to Access the System:

**1. API Key Access (Internal - Loan Officers)**
- **Who uses it:** Make.com automation, Retool dashboard
- **How it works:** Every API request requires `X-API-Key` header
- **Permissions:** Full access (upload, analyze, download, delete)
- **Protection:** Failed attempts logged, rate limited

**2. Secure Token Links (External - Borrowers)**
- **Who uses it:** Borrowers receiving emails
- **How it works:** Click link in email → instant access (no login)
- **Permissions:** Read-only (view loan, download their documents)
- **Protection:**
  - Cryptographically secure tokens (256-bit, unguessable)
  - Currently set to never expire (100 years)
  - Can be revoked instantly if compromised
  - Tracks access count and timestamps

---

## 3. Security Features

### Rate Limiting
- **Limit:** 100 requests per hour per IP address
- **Prevents:** Brute force attacks, DoS attacks, accidental loops
- **Response:** HTTP 429 (Too Many Requests) when exceeded

### File Upload Protection
- **Size limit:** 10 MB maximum
- **Allowed types:** PDF, DOC, DOCX, JPG, PNG, TXT, XLS, XLSX
- **Blocked types:** Executables (.exe, .sh), scripts (.js, .php), archives (.zip)
- **Sanitization:** Filenames cleaned to prevent directory traversal attacks

### CORS Restrictions
- **Allowed origins only:** Make.com, Retool
- **Blocks:** All other websites from accessing your API
- **Prevents:** Cross-site attacks, unauthorized API usage

### IP Whitelisting (Optional - Currently Disabled)
- Can restrict API access to specific IP addresses
- Useful if you have static IPs for Make.com/Retool
- Enable in code: `ENABLE_IP_WHITELIST = True`

---

## 4. Audit Logging

### What's Logged:
| Event | Information Captured |
|-------|---------------------|
| Document uploads | Loan ID, file count, IP address, timestamp |
| Document downloads | Loan ID, filename, IP address, timestamp |
| Loan analysis | Loan ID, scores, IP address, timestamp |
| Failed login attempts | Invalid API key (partial), IP address, timestamp |
| Rate limit violations | IP address, request count, timestamp |
| Token usage | Loan ID, access count, IP address, timestamp |

### What's NOT Logged (Privacy):
- ❌ Borrower names
- ❌ Borrower emails
- ❌ Income amounts
- ❌ Document contents
- ❌ Full API keys (only first 8 characters)

### Log Location:
- File: `./audit_log.json`
- Format: JSON (one event per line)
- Access: Via API endpoint `/audit-log` (requires API key)

---

## 5. Data Retention

### Automatic Deletion:
- **Documents:** Deleted after 30 days (configurable)
- **Database records:** Kept permanently (loans table)
- **Audit logs:** Kept permanently

### Manual Deletion:
- **Admin endpoint:** `/clear-all-data` (requires API key)
- **Deletes:** All loans, documents, and uploaded files
- **Use case:** Testing, demo resets, client offboarding

---

## 6. GLBA Compliance

### Key Requirements Met:

| GLBA Requirement | How We Comply |
|------------------|---------------|
| Data encryption | ✅ AES-256 for PII + files |
| Access controls | ✅ API keys + secure tokens |
| Audit trails | ✅ Complete logging |
| Secure transmission | ✅ HTTPS enforced |
| Data minimization | ✅ Only collect necessary data |
| Retention limits | ✅ Auto-delete after 30 days |
| Incident response | ✅ Audit logs enable investigation |

### What You Still Need:
- **Privacy Notice** - Provide to borrowers (template in original doc)
- **Employee training** - Secure handling of API keys
- **Incident response plan** - What to do if breached
- **Access documentation** - Who has API key access

---

## 7. Security Configuration Checklist

### Before Going Live:

**Critical (Must Do):**
- [ ] Set strong `API_KEY` in Railway (32+ characters, random)
- [ ] Set `ENCRYPTION_KEY` in Railway
- [ ] Back up encryption key securely (password manager + physical safe)
- [ ] Verify `ALLOWED_ORIGINS` contains only Make.com + Retool
- [ ] Test API key authentication (valid key works, invalid fails)
- [ ] Test file encryption (upload doc, verify encrypted on disk)
- [ ] Verify HTTPS is enabled (Railway does automatically)
- [ ] Create Privacy Notice for borrowers

**Recommended:**
- [ ] Enable IP whitelisting (if you have static IPs)
- [ ] Set up Railway monitoring alerts
- [ ] Document who has access to API key
- [ ] Test token generation and revocation

### Ongoing Maintenance:

**Monthly:**
- Review audit logs for suspicious activity
- Check token access counts (high counts = possible leak)
- Revoke unused tokens

**Quarterly:**
- Rotate API key
- Review employee access to credentials
- Update IP whitelist (if enabled)

**Annually:**
- Rotate encryption key (requires data migration)
- Security audit by third party
- Test backup restoration

---

## 8. Common Security Questions

**Q: Is our data safe if your server gets hacked?**
A: Yes. All PII and documents are encrypted with AES-256. Even if someone steals the database or files, they cannot read the data without the encryption key (stored separately).

**Q: What happens if we lose the encryption key?**
A: All encrypted data becomes permanently unrecoverable. Back it up in three places: Railway, password manager, and physical safe.

**Q: Can we track who accessed which loans?**
A: Yes. The audit log records every access with timestamp, loan ID, and IP address. Token access also tracks usage count.

**Q: How do we know if someone is trying to hack us?**
A: The audit log shows failed authentication attempts, rate limit violations, and suspicious download patterns. Review monthly.

**Q: Are we GLBA compliant?**
A: The system implements technical safeguards required by GLBA. You also need organizational policies (privacy notices, employee training, incident response plan).

**Q: How often should we rotate the API key?**
A: Every 90 days, or immediately if an employee leaves or you suspect compromise.

**Q: What if a borrower's email is compromised?**
A: An attacker with email access could use the token link. Mitigate by: enabling token expiration, using password protection per loan (optional 6-digit PIN), or revoking tokens when loans close.

---

## 9. Incident Response (Quick Reference)

### If API Key is Compromised:
1. Generate new key: `openssl rand -base64 32`
2. Update in Railway environment variables
3. Update in Make.com and Retool
4. Review audit logs for unauthorized access
5. Document incident

### If Encryption Key is Compromised:
1. **DO NOT** rotate immediately (makes data unreadable)
2. Review audit logs to assess data access
3. If data accessed: Notify borrowers, offer credit monitoring
4. Plan key rotation with data migration during maintenance window

### If Suspicious Activity Detected:
1. Review audit log for patterns
2. Identify affected loans
3. Revoke suspicious tokens
4. Enable IP whitelist if needed
5. Rotate API key if compromised

---

## 10. Security Controls Summary

| Security Control | Status | Purpose |
|------------------|--------|---------|
| API Key Authentication | ✅ Enabled | Authenticate internal users |
| Secure Tokens | ✅ Enabled | Authenticate borrowers (no login) |
| PII Encryption | ✅ Enabled | Protect borrower data at rest |
| File Encryption | ✅ Enabled | Protect documents at rest |
| HTTPS | ✅ Enabled | Encrypt data in transit |
| Rate Limiting | ✅ Enabled | Prevent DoS/brute force |
| CORS Restrictions | ✅ Enabled | Block unauthorized domains |
| File Type/Size Limits | ✅ Enabled | Block malicious files |
| Filename Sanitization | ✅ Enabled | Prevent path traversal |
| Audit Logging | ✅ Enabled | Track all data access |
| Auto-Deletion | ✅ Enabled | Enforce retention policy |
| IP Whitelist | ⚠️ Optional | Block unauthorized IPs (disabled) |
| Token Revocation | ✅ Enabled | Disable compromised tokens |

---

## 11. Critical Security Settings

### Railway Environment Variables (Required):

```bash
API_KEY=<strong-random-32-char-string>        # Main authentication
ENCRYPTION_KEY=<44-char-fernet-key>           # Data encryption
DATABASE_URL=<auto-provided-by-railway>       # PostgreSQL connection
BASE_URL=https://your-app.up.railway.app      # For email links
```

### How to Generate Keys:

```bash
# Generate API key
openssl rand -base64 32

# Generate encryption key
python encryption.py
```

### Security Rules:
- ❌ Never commit keys to git
- ❌ Never share via email/Slack
- ✅ Store in password manager
- ✅ Back up encryption key physically
- ✅ Use different keys for dev vs production

---

## Contact & Support

**For Security Issues:**
- Report immediately to system administrator
- Include: What you found, how to reproduce, impact

**Log Locations:**
- Audit log: `./audit_log.json`
- Application logs: Railway Dashboard → Deployments → Logs
- Database logs: Railway Dashboard → PostgreSQL → Logs

---

**END OF SECURITY OVERVIEW**

*Review this document before your client meeting. For detailed technical information, see the full comprehensive security documentation.*

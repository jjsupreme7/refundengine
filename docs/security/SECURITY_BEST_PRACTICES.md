# Security Best Practices - Explained Simply

A plain-English guide to keeping your client data secure.

---

## 🔐 The 5 Security Rules (And Why They Matter)

### 1. Keep Work Laptop Encrypted

**What it means:** Turn on BitLocker (Windows) or FileVault (Mac)

**Why it matters:**
Imagine you leave your laptop in a coffee shop. Without encryption:
- ❌ Anyone can remove the hard drive
- ❌ Plug it into another computer
- ❌ Read all your client invoices

With encryption:
- ✅ Hard drive is scrambled without your password
- ✅ Data is unreadable to thieves
- ✅ Client financial data stays safe

**How to do it:**

**Windows:**
```
1. Click Start → Type "BitLocker"
2. Click "Manage BitLocker"
3. Click "Turn on BitLocker" for your C: drive
4. Choose "Save to file" for recovery key
5. Wait ~30 minutes for encryption
```

**Mac:**
```
1. Click Apple menu → System Settings
2. Click "Privacy & Security"
3. Scroll to "FileVault"
4. Click "Turn On" (if not already on)
5. Save recovery key somewhere safe
```

---

### 2. Don't Email Client PDFs

**What it means:** Never attach invoices/POs to emails

**Why it matters:**
```
You email invoice.pdf → Client forwards it → Accounting forwards it
→ IT department gets it → Someone's personal email → Gmail servers
→ Stored forever → Could be in a data breach
```

Once you email a PDF, you lose control of where it goes.

**Do this instead:**
- ✅ Upload to secure client portal (SharePoint, client's system)
- ✅ Hand-deliver USB drive (if physical meeting)
- ✅ Use client's preferred secure file transfer
- ✅ Share via encrypted link (with expiration date)

**Example:**
```
❌ BAD: "Hi, here's the invoice attached..."
✅ GOOD: "Hi, I've uploaded the invoice to our SharePoint folder"
```

---

### 3. Don't Commit .env File

**What it means:** Never upload your credentials to GitHub

**Why it matters:**
Your `.env` file looks like this:
```env
OPENAI_API_KEY=sk-proj-abc123xyz...
SUPABASE_KEY=eyJhbGciOiJIUzI1...
```

If this gets on GitHub:
- ❌ Anyone on the internet can find it
- ❌ They can use your OpenAI credits ($$$)
- ❌ They can access your database
- ❌ They can read/delete client data

**Good news:** We already protected you!
The `.env` file is in `.gitignore`, so Git won't let you commit it.

**How to verify:**
```bash
git status
# Should NOT show .env file in the list
```

If you ever see `.env` in `git status`:
```bash
# DON'T commit! Instead:
git restore --staged .env  # Remove from staging
```

---

### 4. Archive/Delete Client Data After Projects

**What it means:** Don't keep old client invoices forever

**Real-world example:**
```
You finish 20 client projects over 2 years.
Your laptop now has:
- 200 invoices
- 150 POs
- Financial data from 20 companies
```

If your laptop is compromised, ALL 20 clients are affected.

**Better approach:**
```
Project lifecycle:
1. Get client invoices → Store in client_documents/
2. Run analysis → Generate report
3. Deliver to client → Get paid
4. Archive (if legally required) → External encrypted drive
5. Delete from laptop → Reduce risk

Only keep ACTIVE projects on laptop.
```

**How to archive:**
```bash
# After project completes
mkdir -p ~/SecureArchive/2024/Client_ACME
mv client_documents/invoices/acme_* ~/SecureArchive/2024/Client_ACME/
mv outputs/analysis/acme_analysis.xlsx ~/SecureArchive/2024/Client_ACME/

# Now only active projects on laptop
```

**When to permanently delete:**
Check your contract/industry requirements:
- Tax documents: Usually 7 years
- General business: Usually 3-7 years
- After that: Securely delete

---

## 🎯 Real-World Scenarios

### Scenario 1: Coffee Shop Work

**Situation:** You're at Starbucks analyzing invoices

**Security checklist:**
- ✅ Laptop is encrypted (BitLocker/FileVault on)
- ✅ Screen privacy filter (prevents shoulder-surfing)
- ✅ 5-minute auto-lock if you step away
- ✅ VPN if using public WiFi
- ✅ Don't leave laptop unattended (even for bathroom)

**Why:** Coffee shops are common theft locations.

---

### Scenario 2: Finishing a Client Project

**Situation:** You completed analysis for "ABC Corporation"

**Checklist:**
```bash
# 1. Generate final report ✅
python analysis/analyze_refunds.py --input abc_transactions.xlsx

# 2. Deliver to client via secure method ✅
# (Upload to their SharePoint, not email)

# 3. Archive if needed ✅
cp -r client_documents/invoices/abc_* ~/Archive/2024/ABC_Corp/

# 4. Delete from laptop ✅
rm client_documents/invoices/abc_*
rm client_documents/purchase_orders/abc_*

# 5. Set calendar reminder for permanent deletion (7 years) ✅
# 2031: Delete ~/Archive/2024/ABC_Corp/
```

---

### Scenario 3: Laptop Stolen

**Worst case scenario:** Your laptop is stolen

**If you followed security practices:**
- ✅ Laptop encrypted → Data unreadable
- ✅ Old projects archived/deleted → Limited exposure
- ✅ .env never committed → Supabase access still secure
- ✅ Client invoices not emailed → No email trail

**What to do:**
1. Report to police immediately
2. Change all passwords (Supabase, OpenAI, GitHub)
3. Notify affected clients (only active projects on laptop)
4. Review access logs in Supabase dashboard

**If you DIDN'T follow security practices:**
- ❌ Unencrypted laptop → All data readable
- ❌ 2 years of projects on laptop → 20 clients affected
- ❌ .env committed to GitHub → Need to rotate all keys
- ❌ Invoices emailed → Larger notification scope

---

## 📋 Security Setup Checklist

### One-Time Setup (Do This Now)

```
□ Enable disk encryption
  Windows: BitLocker
  Mac: FileVault

□ Set strong password
  12+ characters, mix of upper/lower/numbers/symbols

□ Enable screen auto-lock
  Settings → Lock after 5 minutes idle

□ Verify .env is in .gitignore
  git status should NOT show .env

□ Create archive folder
  mkdir ~/SecureArchive/2024

□ Set up backup
  External encrypted drive for archives

□ Enable 2FA on accounts
  GitHub, Supabase, OpenAI
```

### After Each Project

```
□ Generate final report
□ Deliver via secure method (not email)
□ Archive client documents (if legally required)
□ Delete from laptop
□ Set reminder for permanent deletion (7 years)
```

### Monthly

```
□ Review client_documents/ folder
  Delete completed projects

□ Review outputs/ folder
  Archive or delete old reports

□ Check Supabase access logs
  Look for suspicious activity

□ Update passwords (quarterly)
```

---

## 🚨 Red Flags (Stop Immediately If You See These)

### ⚠️ Warning Signs

1. **Git wants to commit .env**
   ```
   git status shows: modified: .env
   ```
   **Action:** `git restore --staged .env` (never commit!)

2. **Client asks you to email invoices**
   ```
   Email: "Can you send me those PDFs?"
   ```
   **Action:** "I'll upload them to [secure portal] instead"

3. **100+ files in client_documents/**
   ```
   ls client_documents/invoices/ | wc -l
   200
   ```
   **Action:** Archive completed projects

4. **Laptop not encrypted**
   ```
   BitLocker/FileVault shows "Off"
   ```
   **Action:** Turn on NOW (before working on client data)

5. **Using personal email for client communication**
   ```
   Discussing client financials on @gmail.com
   ```
   **Action:** Use business email only

---

## 💡 Simple Mental Model

Think of security like locking your car:

**Level 1: Lock the doors** (Basic)
- Enable encryption
- Use strong password
- Don't email sensitive files

**Level 2: Park in garage** (Better)
- Archive old projects
- Auto-lock screen
- Use VPN on public WiFi

**Level 3: Install alarm system** (Best)
- 2FA on all accounts
- Monitor access logs
- Regular security audits
- Professional liability insurance

**You need at least Level 1.** Level 2 is recommended. Level 3 is for enterprise clients.

---

## ❓ FAQs

### "Can I use Google Drive for client documents?"

**Short answer:** No (for work laptop), yes (for personal projects)

**Long answer:**
- Personal Google Drive → Not secure enough for client financial data
- Google Workspace Business → Maybe, if client approves
- SharePoint → Yes, enterprise-grade
- Local + encrypted external drive → Yes, safe

### "What if I need to work on a plane (no internet)?"

**Solution:**
```bash
# Before flight:
1. git pull (get latest code)
2. Make sure client docs are local
3. Work offline
4. git push when you land
```

Your RAG queries need internet (Supabase), but analysis can run offline.

### "How long should I keep client data?"

**Depends on your industry:**
- Tax/accounting: 7 years (IRS requirement)
- Legal: 10+ years (varies by jurisdiction)
- General consulting: 3-5 years

**Check:**
1. Your contract with client
2. Your professional liability insurance requirements
3. Your state/industry regulations

### "What about backups?"

**For code:** GitHub is your backup ✅

**For client documents:**
- Primary: Work laptop (encrypted)
- Backup: External encrypted drive (stored securely)
- Not Supabase (not designed for this use case)

---

## 🎓 Training Exercise

Test yourself:

**Scenario:** Client emails: "Can you send me all the invoices we analyzed?"

**Options:**
A. Reply with 10 PDF attachments
B. Upload to SharePoint, send link
C. Put in Dropbox, send public link
D. Zip them with password, email zip

**Answer:** B (SharePoint)
- A: ❌ Email not secure
- C: ❌ Public link can leak
- D: ❌ Password sent separately? Still in email

**Best practice:** Use client's preferred secure portal.

---

## 📚 Additional Resources

- **NIST Cybersecurity Framework:** https://www.nist.gov/cyberframework
- **Data Retention Guidelines:** Consult your CPA or lawyer
- **Professional Liability Insurance:** Covers data breaches
- **Incident Response Plan:** What to do if laptop is stolen/hacked

---

## ✅ Summary: The Essentials

Remember these 5 things:

1. 🔒 **Encrypt laptop** (BitLocker/FileVault)
2. 📧 **No client PDFs via email** (use secure portals)
3. 🚫 **Never commit .env** (already protected by .gitignore)
4. 🗑️ **Delete old projects** (archive then remove from laptop)
5. 🔑 **Strong passwords + 2FA** (on all accounts)

**Do these, and you're 95% safer than most consultants.**

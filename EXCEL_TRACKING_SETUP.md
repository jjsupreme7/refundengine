# Excel Version Tracking - Setup Guide

## ✅ What's Been Built

### 1. Database Schema (Ready to Deploy)
**Location:** `database/schema/migration_excel_versioning.sql`

**Tables:**
- `excel_file_versions` - Tracks each upload/version
- `excel_cell_changes` - Cell-level change tracking (GitHub-style diffs)
- Extensions to `excel_file_tracking` - Added versioning columns

**Functions:**
- `acquire_file_lock()` - Lock file for editing
- `release_file_lock()` - Release lock
- `create_file_version()` - Create new version with change tracking

### 2. Python Backend (Complete)
**Location:** `core/excel_versioning.py`

**Class:** `ExcelVersionManager`
- `upload_file()` - Upload Excel to Supabase Storage
- `create_version()` - Create new version with automatic diff
- `get_version_diff()` - Compare any two versions
- `calculate_file_hash()` - SHA256 hashing for change detection

### 3. Dashboard UI (Complete)
**Location:** `dashboard/pages/7_Excel_Manager.py`

**Features:**
- Upload Excel files + invoice/PO PDFs
- View recent uploads (last 10 automatically saved)
- GitHub-style diff viewer for cell changes
- Manual snapshot creation for milestones
- Activity log of all changes
- Filter by user, row, column, change type

**Components:**
- `dashboard/components/excel_diff_viewer.py` - Reusable diff viewer
  - Compact change summary
  - Detailed row-by-row diffs
  - Side-by-side comparison
  - Export to CSV
  - Color-coded changes (added/modified/deleted)

---

## 🚀 Deployment Steps

### Step 1: Deploy Database Schema

**Option A: Using psql (Recommended)**
```bash
# Install psql if needed
brew install postgresql@15  # macOS
# OR
sudo apt-get install postgresql-client  # Linux

# Set environment variable
export SUPABASE_DB_PASSWORD='your-password'

# Run deployment script
chmod +x scripts/deploy_excel_versioning.sh
./scripts/deploy_excel_versioning.sh
```

**Option B: Manual deployment (if psql not available)**
1. Go to Supabase Dashboard: https://supabase.com/dashboard
2. Navigate to: SQL Editor
3. Copy contents of `database/schema/migration_excel_versioning.sql`
4. Paste and execute in SQL Editor

### Step 2: Set Up Storage Buckets

```bash
python3 scripts/setup_excel_storage.py
```

This creates 3 Supabase Storage buckets:
- `excel-files` - Current working files
- `excel-versions` - Version history
- `excel-exports` - Generated reports

### Step 3: Test the System

```bash
python3 scripts/test_excel_versioning.py
```

This will:
- Test file upload
- Test version creation
- Test diff generation
- Test file locking
- Verify all functionality

---

## 📊 How It Works

### Workflow Overview

```
1. Upload Excel file
   ↓
2. System saves as "working file" + recent upload
   ↓
3. AI analyzes rows in batches
   ↓
4. You download, make corrections, re-upload
   ↓
5. System automatically tracks cell changes
   ↓
6. View diff: See exactly what changed (GitHub-style)
   ↓
7. Create manual snapshot at milestones
```

### What Gets Tracked

**Every upload captures:**
- Who uploaded (user email)
- When (timestamp)
- What changed (cell-by-cell diff)
- Change type (added, modified, deleted)
- Row and column affected
- Old value → New value

**Example change tracking:**
```
Row 23, Column "Product_Type": "SaaS" → "Professional Services"
Row 45, Column "Estimated_Refund": "$5,000" → "$8,500"
Row 102: Entire row deleted
```

### Recent Uploads (Auto-Saved)

- System keeps your last **10 uploads** automatically
- Acts as a safety net between manual snapshots
- Can download or restore any recent upload
- Older than 10 uploads? Create a snapshot to keep it permanently

### Snapshots (Manual Milestones)

You create these when YOU want:
- "First 2,500 rows complete"
- "Ready for partner review"
- "Final - ready for filing"

Snapshots are **permanent** and never auto-deleted.

---

## 🎯 Using the Excel Manager Dashboard

### 1. Upload Tab

1. Select your project
2. Upload Excel file (your master refund analysis file)
3. Upload invoice/PO PDFs (optional)
4. Add change summary note (optional)
5. Click "Upload Files"

### 2. Recent Uploads Tab

- See last 10 uploads
- View change summary for each
- Click "View All Changes" for GitHub-style diff
- Download any version
- Restore to previous state
- Save as permanent snapshot

**Diff Viewer Features:**
- Filter by row, column, or change type
- See old → new values side-by-side
- Color-coded changes:
  - 🟢 Green = Added
  - 🟡 Yellow = Modified
  - 🔴 Red = Deleted
- Export changes to CSV

### 3. Snapshots Tab

- Create permanent saved versions
- Name them for milestones
- Add descriptions
- Download or restore snapshots

### 4. Activity Log

- Complete history of all changes
- Filter by user, type, or date
- Full audit trail
- Shows AI analysis, user edits, snapshots

---

## 🔍 Example Workflow

### Scenario: Analyzing 5,000 invoices for WA 2024 Sales Tax

**Day 1:**
```
10:00 AM - Upload WA_2024_Sales_Tax.xlsx (5,000 rows)
10:30 AM - AI analyzes rows 1-500 → System auto-saves as recent upload
11:00 AM - Download, review, make corrections
02:00 PM - Re-upload with corrections → Auto-tracks 8 cell changes
```

**Day 2:**
```
09:00 AM - AI analyzes rows 501-1,000
11:00 AM - Re-upload corrections → Auto-tracks 15 cell changes
03:00 PM - Sarah reviews and makes changes → Auto-tracks who changed what
```

**Day 5: First Milestone**
```
05:00 PM - Create Snapshot: "First 2,500 rows complete"
          - Permanent saved version
          - Can share with others
          - Safe to continue working
```

**Day 10: All Done**
```
03:00 PM - Create Snapshot: "All 5,000 rows analyzed - Final"
          - Ready for client
          - Audit trail complete
          - Can compare to earlier snapshots
```

**Total saved versions:**
- Working file (current state)
- Last 10 recent uploads (auto-saved)
- 2 permanent snapshots (manually created)
- Complete change history for audit

---

## 🐛 Troubleshooting

### Database Deployment Issues

**Error: "psql: command not found"**
```bash
# Install PostgreSQL client
brew install postgresql@15  # macOS
```

**Error: "Connection refused"**
- Check `SUPABASE_DB_PASSWORD` is set correctly
- Verify your IP is allowed in Supabase dashboard settings
- Check Supabase project is active

### Upload Issues

**Error: "Failed to upload file"**
- Check file size (max 20MB for Excel)
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set
- Check Storage buckets are created (Step 2 above)

### Diff Viewer Issues

**Changes not showing**
- Verify `excel_cell_changes` table has data
- Check database schema was deployed correctly
- Look for errors in console

---

## 📁 File Structure

```
refund-engine/
├── database/schema/
│   └── migration_excel_versioning.sql    # Database schema
│
├── core/
│   └── excel_versioning.py                # Backend logic
│
├── dashboard/
│   ├── pages/
│   │   └── 7_Excel_Manager.py            # Main dashboard page
│   └── components/
│       └── excel_diff_viewer.py          # Diff viewer component
│
└── scripts/
    ├── deploy_excel_versioning.sh        # Deployment script
    ├── setup_excel_storage.py            # Storage bucket setup
    └── test_excel_versioning.py          # Test suite
```

---

## ✅ Deployment Checklist

- [ ] Deploy database schema (`./scripts/deploy_excel_versioning.sh`)
- [ ] Set up storage buckets (`python3 scripts/setup_excel_storage.py`)
- [ ] Run test suite (`python3 scripts/test_excel_versioning.py`)
- [ ] Start dashboard (`streamlit run dashboard/Dashboard.py --server.port 5001`)
- [ ] Navigate to "Excel Manager" page
- [ ] Upload test Excel file
- [ ] Verify version tracking works
- [ ] Test diff viewer

---

## 🎉 What You Get

✅ **GitHub-style change tracking** for Excel files
✅ **Automatic version history** (last 10 uploads)
✅ **Manual snapshots** for milestones
✅ **Cell-level diffs** (see exactly what changed)
✅ **Multi-user tracking** (see who changed what)
✅ **Complete audit trail** for tax compliance
✅ **No more "which version is current?"** confusion
✅ **Easy rollback** to any previous state

All without needing in-browser Excel editing! Just download → edit → upload, and the system tracks everything automatically.

---

**Questions? Issues?**
Check the logs in the console or Supabase dashboard for detailed error messages.

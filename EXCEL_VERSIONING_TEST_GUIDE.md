# Excel Versioning System - Testing Guide

## 📋 What We're Testing

1. Upload an Excel file (Version 1)
2. Make some edits to it
3. Re-upload the edited version (Version 2)
4. View AI-generated change summary
5. See GitHub-style diff viewer showing exactly what changed

---

## 🎯 Step-by-Step Testing Process

### **Step 1: Start the Dashboard**

Open your terminal and run:
```bash
cd /Users/jacoballen/Desktop/refund-engine
streamlit run dashboard/Dashboard.py --server.port 5001
```

This will open the dashboard in your browser at `http://localhost:5001`

---

### **Step 2: Create a Test Project (If Needed)**

1. In the dashboard, go to **"Projects"** page (sidebar)
2. Click **"Create New Project"**
3. Fill in:
   - **Name:** "Excel Versioning Test"
   - **Description:** "Testing Excel version tracking and AI summaries"
   - **State:** Washington
4. Click **"Create Project"**

---

### **Step 3: Upload Initial Excel File (Version 1)**

1. Go to the **"Excel Manager"** page (new page #7 in sidebar)
2. Click the **"Upload"** tab
3. Select your test project: **"Excel Versioning Test"**
4. Upload Excel file:
   - Click "Browse files" under "Upload Master Excel"
   - Select: `/Users/jacoballen/Desktop/refund-engine/test_data/Refund_Claim_Sheet_Test.xlsx`
5. Leave the **"🤖 Auto-generate summary with AI"** checkbox **checked**
6. Click **"📤 Upload Files"**

**What should happen:**
- ✅ "Files uploaded successfully!"
- ✅ Shows upload summary
- ✅ Shows AI-generated summary: "First upload - no changes to summarize"

This is now **Version 1** in the system.

---

### **Step 4: Download and Edit the Excel File**

Now we need to make some changes to test version tracking.

**Option A: Make changes manually (Recommended)**

1. In the **"Recent Uploads"** tab, you should see your upload
2. Click **"📥 Download"** to download the Excel file
3. Open it in Excel/Numbers
4. Make some changes:
   - **Row 1:** Change `Tax_Remitted` from `945.0` to `850.0`
   - **Row 2:** Change `Vendor_Name` from "Salesforce Inc" to "Salesforce, Inc."
   - **Row 3:** Change `Expected_Refund_Percentage` from "100%" to "85%"
   - **Row 5:** Add a note in `Test_Notes` column: "Verified with client"
5. Save the file as `Refund_Claim_Sheet_Test_v2.xlsx`

**Option B: Use the pre-modified file (Faster)**

I'll create a modified version for you:

```bash
# Run this command to create a modified version
python3 << 'EOF'
import pandas as pd

# Load original
df = pd.read_excel('/Users/jacoballen/Desktop/refund-engine/test_data/Refund_Claim_Sheet_Test.xlsx')

# Make some changes
df.loc[0, 'Tax_Remitted'] = 850.0
df.loc[1, 'Vendor_Name'] = 'Salesforce, Inc.'
df.loc[2, 'Expected_Refund_Percentage'] = '85%'
df.loc[4, 'Test_Notes'] = 'Verified with client'

# Save modified version
df.to_excel('/Users/jacoballen/Desktop/refund-engine/test_data/Refund_Claim_Sheet_Test_v2.xlsx', index=False)
print("✅ Modified version created: test_data/Refund_Claim_Sheet_Test_v2.xlsx")
EOF
```

---

### **Step 5: Upload the Modified File (Version 2)**

1. Still in **"Excel Manager"** → **"Upload"** tab
2. Select the same project: **"Excel Versioning Test"**
3. Upload the modified Excel file:
   - `/Users/jacoballen/Desktop/refund-engine/test_data/Refund_Claim_Sheet_Test_v2.xlsx`
4. Keep **"🤖 Auto-generate summary with AI"** **checked**
5. Click **"📤 Upload Files"**

**What should happen:**
- ✅ "Files uploaded successfully!"
- 🤖 **"Generating AI summary of changes..."** (takes 2-3 seconds)
- ✅ **"AI summary generated!"**
- 📝 **Shows detailed AI summary** like:

```
A total of 4 cells were changed across 4 rows.

- Financial Adjustments
  • Row 1: Decreased Tax_Remitted from 945.0 to 850.0

- Vendor Information
  • Row 2: Updated Vendor_Name from "Salesforce Inc" to "Salesforce, Inc."

- Refund Calculations
  • Row 3: Adjusted Expected_Refund_Percentage from 100% to 85%

- Documentation
  • Row 5: Added Test_Notes: "Verified with client"
```

This is now **Version 2** with full change tracking!

---

### **Step 6: View Recent Uploads & Change History**

1. Click the **"Recent Uploads"** tab
2. You should see **2 uploads**:
   - **Latest:** Your Version 2 upload with AI summary
   - **Previous:** Your Version 1 upload

3. For Version 2, you'll see:
   - "Modified 4 cells in 4 rows"
   - AI-generated summary
   - List of recent changes

4. Click **"👁️ View All Changes"** button

**What should happen:**
- ✅ GitHub-style diff viewer appears
- ✅ Shows each change in detail:
  - Row 1, Column "Tax_Remitted": `945.0` → `850.0`
  - Row 2, Column "Vendor_Name": `Salesforce Inc` → `Salesforce, Inc.`
  - Row 3, Column "Expected_Refund_Percentage": `100%` → `85%`
  - Row 5, Column "Test_Notes": `(empty)` → `Verified with client`

5. **Try the filters:**
   - Filter by specific row (e.g., "Row 1")
   - Filter by column (e.g., "Tax_Remitted")
   - Filter by change type (Modified/Added/Deleted)

6. **Try the export:**
   - Click **"📄 Export to CSV"**
   - Download change report

---

### **Step 7: Test Again with More Changes**

To really see the version tracking in action:

1. Download the latest version
2. Make 5-10 more changes:
   - Change some vendor names
   - Update some refund amounts
   - Add notes to several rows
   - Delete a row (set all values to empty)
3. Re-upload
4. See the AI summary get smarter and more detailed!

---

## ✅ What to Verify

### Upload Tab
- [ ] Can select a project
- [ ] Can upload Excel file
- [ ] AI summary checkbox is visible
- [ ] Upload succeeds and shows confirmation

### Recent Uploads Tab
- [ ] Shows all uploaded versions (chronological)
- [ ] Each upload shows:
  - [ ] Date/time and user email
  - [ ] AI-generated summary
  - [ ] Number of cells/rows changed
  - [ ] Download button
  - [ ] "View All Changes" button

### Diff Viewer
- [ ] Opens when clicking "View All Changes"
- [ ] Shows summary stats (total changes, by type)
- [ ] Lists changes row-by-row
- [ ] Shows old → new values
- [ ] Color codes changes
- [ ] Filters work (by row, column, type)
- [ ] Export to CSV works
- [ ] Side-by-side view works

### AI Summaries
- [ ] Auto-generates for Version 2+ (not Version 1)
- [ ] Groups changes by category
- [ ] Highlights significant changes
- [ ] Is concise but detailed
- [ ] Saves to version history

### Activity Log Tab
- [ ] Shows all uploads chronologically
- [ ] Shows who made changes
- [ ] Shows timestamps
- [ ] Can filter by user/type/date

---

## 🐛 Common Issues & Fixes

### "No recent uploads showing"
- Make sure you selected the correct project
- Refresh the page
- Check database table: `excel_file_versions`

### "AI summary not generating"
- Check `OPENAI_API_KEY` is set in `.env`
- Check browser console for errors
- Try unchecking AI summary and using manual

### "Changes not showing in diff viewer"
- Verify Version 2 is actually different from Version 1
- Check `excel_cell_changes` table has data
- Look for errors in terminal where Streamlit is running

### "Download button not working"
- This is expected - download functionality is placeholder
- Focus on testing diff viewer and AI summaries

---

## 📊 Expected Costs

**For this test:**
- Upload 1: $0 (no AI summary, first upload)
- Upload 2: ~$0.01 (AI summary for 4 changes)
- Upload 3+: ~$0.01-0.02 each

**Total for testing:** < $0.05

---

## 🎉 Success Criteria

You know it's working when:

1. ✅ Can upload Excel files without errors
2. ✅ Each upload shows in "Recent Uploads"
3. ✅ AI generates detailed summaries automatically
4. ✅ Diff viewer shows exactly what changed
5. ✅ Can track who made what changes and when
6. ✅ Complete audit trail for tax compliance

---

## 📸 What You Should See

**Recent Uploads List:**
```
📄 Refund_Claim_Sheet_Test_v2.xlsx - Nov 16, 2024 3:45 PM
   ✏️ Modified 4 cells in 4 rows

   📝 AI Summary:
   A total of 4 cells were changed across 4 rows.
   - Financial Adjustments: Decreased Tax_Remitted...
   - Vendor Information: Updated Vendor_Name...

   [Download] [View All Changes] [Save as Snapshot]
```

**Diff Viewer:**
```
📍 Row 1 - Microsoft Corporation

Column: Tax_Remitted
  - 945.0
  + 850.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 Row 2 - Salesforce

Column: Vendor_Name
  - Salesforce Inc
  + Salesforce, Inc.
```

---

**Ready to test? Follow these steps and let me know if you hit any issues!**

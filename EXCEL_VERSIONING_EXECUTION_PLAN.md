# 📋 Excel Versioning System - Complete Execution Plan

**Status:** Ready to Execute
**Timeline:** 4 weeks (accelerated from original 8 weeks)
**Your Current State:** ✅ Dashboard + Supabase + Auth already working

---

## 🎯 What We're Building

A **collaborative Excel versioning system** integrated into your existing Tax Refund Engine that allows:

1. ✅ **In-browser Excel editing** (no download/upload cycle)
2. ✅ **Automatic version control** (like Git for Excel)
3. ✅ **Change tracking** (see who changed what and when)
4. ✅ **File locking** (prevent concurrent editing conflicts)
5. ✅ **Visual diffs** (compare versions side-by-side)
6. ✅ **Audit trail** (complete history for compliance)

---

## 📊 Your Current Architecture (What's Already Done)

```
✅ Supabase Database (PostgreSQL + pgvector)
✅ Supabase Storage (for file uploads)
✅ Streamlit Dashboard (6 pages + authentication)
✅ Excel file tracking schema (excel_file_tracking, excel_row_tracking)
✅ Project management UI
✅ User authentication system
```

---

## 🚀 Execution Plan - 6 Phases

### **PHASE 1: Foundation** ⏱️ Days 1-3 (Week 1)

**Goal:** Set up database schema and storage infrastructure

#### Tasks:

**Day 1: Database Schema** (2-3 hours)
```bash
# 1. Deploy new versioning schema
chmod +x scripts/deploy_excel_versioning.sh
./scripts/deploy_excel_versioning.sh

# This creates:
# - excel_file_versions table (version history)
# - excel_cell_changes table (cell-level changes)
# - Helper functions (acquire_lock, release_lock, create_version)
# - Monitoring views (v_file_version_history, v_recent_activity)
```

**Day 2: Storage Setup** (1-2 hours)
```bash
# 2. Create Supabase Storage buckets
python3 scripts/setup_excel_storage.py

# This creates 3 buckets:
# - excel-files (current versions)
# - excel-versions (version history)
# - excel-exports (exports/reports)
```

**Day 3: Testing** (2-3 hours)
```bash
# 3. Run comprehensive tests
python3 scripts/test_excel_versioning.py

# This tests:
# - File upload
# - Versioning
# - Locking
# - Diff generation
```

**✅ Phase 1 Success Criteria:**
- [ ] All database tables created
- [ ] Storage buckets configured
- [ ] All tests passing
- [ ] Can upload file and create version programmatically

---

### **PHASE 2: Excel Upload & Versioning UI** ⏱️ Days 4-7 (Week 1-2)

**Goal:** Build UI for uploading Excel files and viewing versions

#### Task 2.1: Create Excel Upload Page (Day 4-5)

Create: `dashboard/pages/7_Excel_Editor.py`

```python
"""
Excel Editor Page - Upload and manage Excel files with versioning

Features:
- Drag-and-drop file upload
- View uploaded files
- Version history
- Download specific versions
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.excel_versioning import ExcelVersionManager
from core.auth import require_authentication

st.set_page_config(page_title="Excel Editor - TaxDesk", page_icon="📊", layout="wide")

if not require_authentication():
    st.stop()

# Header
st.title("📊 Excel File Manager")
st.markdown("Upload and manage Excel files with automatic versioning")

# File uploader
uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=['xlsx', 'xls'],
    help="Upload your tax refund analysis Excel file (max 50MB)"
)

if uploaded_file is not None:
    # Save to temp file
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        temp_path = tmp_file.name

    # Upload to Supabase
    manager = ExcelVersionManager()

    with st.spinner("Uploading file..."):
        try:
            file_id = manager.upload_file(
                file_path=temp_path,
                project_id=st.session_state.get('current_project', 'default'),
                user_email=st.session_state.get('user_email', 'user@example.com'),
                file_name=uploaded_file.name
            )

            st.success(f"✅ File uploaded successfully! ID: {file_id}")
            st.session_state.current_file_id = file_id

        except Exception as e:
            st.error(f"❌ Upload failed: {e}")

# View uploaded files (list from database)
st.markdown("---")
st.markdown("### 📂 Your Files")

# TODO: Query database for user's files
# For now, show placeholder
st.info("Your uploaded Excel files will appear here")

# Version history (if file selected)
if st.session_state.get('current_file_id'):
    st.markdown("---")
    st.markdown("### 📚 Version History")

    manager = ExcelVersionManager()
    versions = manager.get_version_history(st.session_state.current_file_id)

    for v in versions:
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"**Version {v['version_number']}**: {v['change_summary']}")
            st.caption(f"By {v['created_by']} on {v['created_at']}")

        with col2:
            st.metric("Rows", v['row_count'])

        with col3:
            if st.button(f"Download v{v['version_number']}", key=f"dl_{v['id']}"):
                # Download version
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                    manager.download_version(
                        st.session_state.current_file_id,
                        v['version_number'],
                        tmp.name
                    )

                    with open(tmp.name, 'rb') as f:
                        st.download_button(
                            "📥 Download",
                            f,
                            file_name=f"version_{v['version_number']}.xlsx"
                        )
```

**✅ Phase 2 Success Criteria:**
- [ ] Can upload Excel file via UI
- [ ] File appears in database
- [ ] Version history displays correctly
- [ ] Can download specific versions

---

### **PHASE 3: In-Browser Excel Editor** ⏱️ Days 8-14 (Week 2-3)

**Goal:** Enable editing Excel files in the browser

**Recommended Approach:** Use `streamlit-aggrid` (simpler) or build custom component with SheetJS

#### Option A: Quick Start with streamlit-aggrid (2-3 days)

```bash
# Install
pip install streamlit-aggrid
```

Add to `dashboard/pages/7_Excel_Editor.py`:

```python
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd

# Load Excel file
if st.session_state.get('current_file_id'):
    manager = ExcelVersionManager()

    # Download current version to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        manager.download_version(
            st.session_state.current_file_id,
            version_number=1,  # Get latest version
            output_path=tmp.name
        )

        df = pd.read_excel(tmp.name)

    # Configure grid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, groupable=True)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    grid_options = gb.build()

    # Display editable grid
    st.markdown("### ✏️ Edit Excel File")

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        theme='streamlit',
        height=600,
        reload_data=False
    )

    # Get edited data
    edited_df = grid_response['data']

    # Save button
    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        if st.button("💾 Save as New Version", type="primary"):
            # Save edited dataframe to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                edited_df.to_excel(tmp.name, index=False)

                # Create new version
                change_summary = st.text_input(
                    "Describe your changes:",
                    placeholder="Updated 5 refund amounts"
                )

                if change_summary:
                    version_id = manager.create_version(
                        file_id=st.session_state.current_file_id,
                        file_path=tmp.name,
                        user_email=st.session_state.user_email,
                        change_summary=change_summary
                    )

                    st.success(f"✅ Saved as version {version_id}")
                    st.rerun()
```

#### Option B: Advanced with SheetJS (Custom Component) (5-7 days)

Create a custom Streamlit component using React + SheetJS for full Excel feature support (formulas, formatting, etc.)

**For your use case, recommend Option A** - streamlit-aggrid is production-ready and sufficient for editing refund data.

**✅ Phase 3 Success Criteria:**
- [ ] Can view Excel file in browser
- [ ] Can edit cells
- [ ] Can save changes as new version
- [ ] Formulas are preserved (if using openpyxl backend)

---

### **PHASE 4: Change Tracking & Diff Visualization** ⏱️ Days 15-21 (Week 3-4)

**Goal:** Show visual diffs and track granular changes

#### Task 4.1: Create Version Comparison Page

Add to `dashboard/pages/7_Excel_Editor.py`:

```python
# Version comparison section
st.markdown("---")
st.markdown("### 🔍 Compare Versions")

col1, col2 = st.columns(2)

with col1:
    version_1 = st.selectbox("Version 1 (older)", [v['version_number'] for v in versions])

with col2:
    version_2 = st.selectbox("Version 2 (newer)", [v['version_number'] for v in versions])

if st.button("🔍 Generate Diff"):
    manager = ExcelVersionManager()

    critical_columns = [
        'Estimated_Refund',
        'Review_Status',
        'Corrected_Product_Type'
    ]

    diff = manager.get_version_diff(
        file_id=st.session_state.current_file_id,
        version_1=version_1,
        version_2=version_2,
        critical_columns=critical_columns
    )

    # Display diff summary
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Rows Added", diff['rows_added'], delta=diff['rows_added'])

    with col2:
        st.metric("Rows Deleted", diff['rows_deleted'], delta=-diff['rows_deleted'], delta_color="inverse")

    with col3:
        st.metric("Cells Changed", len(diff['cells_changed']))

    # Show critical changes
    if diff['critical_changes']:
        st.markdown("#### ⚠️ Critical Changes")

        critical_df = pd.DataFrame(diff['critical_changes'])
        st.dataframe(
            critical_df,
            column_config={
                "row_index": "Row",
                "column": "Column",
                "old_value": "Old Value",
                "new_value": "New Value"
            },
            hide_index=True
        )

    # Show all changes
    st.markdown("#### 📋 All Changes")

    all_changes_df = pd.DataFrame(diff['cells_changed'])

    # Highlight critical changes
    def highlight_critical(row):
        if row['is_critical']:
            return ['background-color: #fff3cd'] * len(row)
        return [''] * len(row)

    styled_df = all_changes_df.style.apply(highlight_critical, axis=1)

    st.dataframe(styled_df, height=400)
```

#### Task 4.2: Create Activity Feed

Add to `dashboard/Dashboard.py`:

```python
# Recent Activity Feed
st.markdown("### 📋 Recent Activity")

# Query activity view
from core.excel_versioning import ExcelVersionManager

manager = ExcelVersionManager()
activity = manager.supabase.table('v_recent_activity').select('*').limit(10).execute()

for item in activity.data:
    st.markdown(f"""
    <div class="section-card">
        <p><strong>{item['user_email']}</strong> {item['description']}</p>
        <p style="color: #718096; font-size: 0.875rem;">{item['activity_time']}</p>
    </div>
    """, unsafe_allow_html=True)
```

**✅ Phase 4 Success Criteria:**
- [ ] Can compare any two versions
- [ ] Diff shows added/modified/deleted rows
- [ ] Critical fields are highlighted
- [ ] Activity feed shows recent changes

---

### **PHASE 5: Analytics & Visualization** ⏱️ Days 22-25 (Week 4)

**Goal:** Create visual analytics for file changes

#### Task 5.1: Version Timeline Visualization

```python
import plotly.express as px
import plotly.graph_objects as go

# Version timeline
versions_df = pd.DataFrame(versions)
versions_df['created_at'] = pd.to_datetime(versions_df['created_at'])

fig = px.timeline(
    versions_df,
    x_start='created_at',
    x_end='created_at',
    y='version_number',
    color='created_by',
    hover_data=['change_summary', 'rows_added', 'rows_modified']
)

st.plotly_chart(fig, use_container_width=True)

# Change frequency chart
fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=versions_df['created_at'],
    y=versions_df['rows_added'],
    mode='lines+markers',
    name='Rows Added',
    line=dict(color='green')
))

fig2.add_trace(go.Scatter(
    x=versions_df['created_at'],
    y=versions_df['rows_modified'],
    mode='lines+markers',
    name='Rows Modified',
    line=dict(color='orange')
))

st.plotly_chart(fig2, use_container_width=True)
```

#### Task 5.2: Collaboration Metrics

```python
# User activity metrics
st.markdown("### 👥 Collaboration Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    unique_editors = len(versions_df['created_by'].unique())
    st.metric("Contributors", unique_editors)

with col2:
    total_versions = len(versions_df)
    st.metric("Total Versions", total_versions)

with col3:
    avg_changes = versions_df['rows_modified'].mean()
    st.metric("Avg Changes/Version", f"{avg_changes:.1f}")

# User leaderboard
user_stats = versions_df.groupby('created_by').agg({
    'version_number': 'count',
    'rows_added': 'sum',
    'rows_modified': 'sum'
}).reset_index()

user_stats.columns = ['User', 'Versions', 'Rows Added', 'Rows Modified']

st.dataframe(user_stats, use_container_width=True)
```

**✅ Phase 5 Success Criteria:**
- [ ] Timeline visualization shows version history
- [ ] Charts display change patterns
- [ ] Collaboration metrics calculated
- [ ] User activity leaderboard

---

### **PHASE 6: Notifications & Polish** ⏱️ Days 26-28 (Week 4+)

**Goal:** Add notification system and final polish

#### Task 6.1: In-App Notifications

Create: `core/notifications.py`

```python
"""
Notification system for Excel changes
"""

from typing import List, Dict
from datetime import datetime


class NotificationManager:
    """Manage user notifications for Excel changes"""

    def __init__(self, supabase):
        self.supabase = supabase

    def create_notification(
        self,
        user_email: str,
        notification_type: str,
        title: str,
        message: str,
        metadata: Dict = None
    ):
        """Create a new notification"""

        self.supabase.table('notifications').insert({
            'user_email': user_email,
            'type': notification_type,
            'title': title,
            'message': message,
            'metadata': metadata or {},
            'read': False,
            'created_at': datetime.utcnow().isoformat()
        }).execute()

    def get_unread_notifications(self, user_email: str) -> List[Dict]:
        """Get unread notifications for user"""

        result = self.supabase.table('notifications').select('*').eq('user_email', user_email).eq('read', False).order('created_at', desc=True).execute()

        return result.data

    def mark_as_read(self, notification_id: str):
        """Mark notification as read"""

        self.supabase.table('notifications').update({'read': True}).eq('id', notification_id).execute()
```

#### Task 6.2: Notification Bell in Dashboard

Add to `dashboard/Dashboard.py`:

```python
# Notification bell in header
from core.notifications import NotificationManager

notif_manager = NotificationManager(supabase)
unread = notif_manager.get_unread_notifications(st.session_state.user_email)

# Show bell icon with count
if unread:
    st.sidebar.markdown(f"🔔 **{len(unread)} New Notifications**")

    with st.sidebar.expander("View Notifications"):
        for notif in unread:
            st.markdown(f"**{notif['title']}**")
            st.caption(notif['message'])

            if st.button(f"Mark Read", key=f"read_{notif['id']}"):
                notif_manager.mark_as_read(notif['id'])
                st.rerun()
```

#### Task 6.3: Create notifications table

```sql
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email TEXT NOT NULL,
    type TEXT NOT NULL, -- 'version_created', 'file_locked', 'comment_added'
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_email ON notifications(user_email);
CREATE INDEX idx_notifications_read ON notifications(read) WHERE read = FALSE;
```

**✅ Phase 6 Success Criteria:**
- [ ] Notifications system working
- [ ] Bell icon shows unread count
- [ ] Users notified of version changes
- [ ] UI polished and professional

---

## 📅 **RECOMMENDED EXECUTION SCHEDULE**

### Week 1: Foundation + Upload
- **Mon-Tue:** Phase 1 (Database + Storage)
- **Wed-Thu:** Phase 2 (Upload UI)
- **Fri:** Testing and refinement

### Week 2: Editor
- **Mon-Wed:** Phase 3 (In-browser editing with streamlit-aggrid)
- **Thu-Fri:** Testing and bug fixes

### Week 3: Change Tracking
- **Mon-Wed:** Phase 4 (Diff visualization)
- **Thu-Fri:** Activity feed and testing

### Week 4: Analytics + Polish
- **Mon-Tue:** Phase 5 (Charts and analytics)
- **Wed-Thu:** Phase 6 (Notifications)
- **Fri:** Final testing and deployment

---

## 🎯 **START HERE - Your First Steps (Next 2 Hours)**

### Step 1: Deploy Phase 1 (30 min)

```bash
# Make script executable
chmod +x scripts/deploy_excel_versioning.sh

# Deploy (make sure .env is loaded)
export SUPABASE_URL="your-url"
export SUPABASE_SERVICE_ROLE_KEY="your-key"
export SUPABASE_DB_PASSWORD="your-password"

./scripts/deploy_excel_versioning.sh
```

### Step 2: Run Tests (15 min)

```bash
python3 scripts/test_excel_versioning.py
```

### Step 3: Add Excel Editor Page (1 hour)

Create `dashboard/pages/7_Excel_Editor.py` with the upload UI code from Phase 2.

### Step 4: Test Upload in Dashboard (15 min)

```bash
streamlit run dashboard/Dashboard.py --server.port 5001
```

Navigate to "7_Excel_Editor" page and upload a test Excel file.

---

## ❓ **FAQ - Your Questions Answered**

### Q1: Concurrent Editing - Which approach?
**A:** File locking (Option 1) - Best for financial data integrity

### Q2: Auto-save vs Manual?
**A:** Hybrid - Auto-save drafts every 60s, manual save creates versions

### Q3: File size limit?
**A:** 20MB soft limit (warning), 50MB hard limit (block)

### Q4: Critical Excel features?
**A:** Formulas ✅, Formatting ✅, Pivot tables ❌ (not critical)

### Q5: Export audit trail?
**A:** Yes! Export to Excel, PDF, and JSON

### Q6: Change tracking granularity?
**A:** Summary-level for most, detailed for: `Estimated_Refund`, `Review_Status`, `Corrected_Product_Type`

---

## 🔧 **Troubleshooting**

### Issue: "Cannot connect to Supabase"
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY

# Re-load .env
source .env
```

### Issue: "Storage bucket creation failed"
- Go to Supabase Dashboard → Storage
- Manually create buckets: `excel-files`, `excel-versions`, `excel-exports`

### Issue: "File upload fails"
- Check file size < 50MB
- Verify storage policies are set
- Check service role key has storage permissions

---

## 📚 **Resources**

- **Supabase Storage Docs:** https://supabase.com/docs/guides/storage
- **streamlit-aggrid:** https://github.com/PablocFonseca/streamlit-aggrid
- **openpyxl Docs:** https://openpyxl.readthedocs.io/

---

## ✅ **Success Checklist**

Use this to track your progress:

**Phase 1: Foundation**
- [ ] Database schema deployed
- [ ] Storage buckets created
- [ ] Tests passing

**Phase 2: Upload**
- [ ] Excel Editor page created
- [ ] File upload working
- [ ] Version history displays

**Phase 3: Editor**
- [ ] In-browser editing working
- [ ] Can save changes as new version
- [ ] File locking implemented

**Phase 4: Change Tracking**
- [ ] Version comparison working
- [ ] Diffs show changes
- [ ] Activity feed displays

**Phase 5: Analytics**
- [ ] Version timeline chart
- [ ] Collaboration metrics
- [ ] Change frequency charts

**Phase 6: Notifications**
- [ ] Notification system working
- [ ] Bell icon in dashboard
- [ ] Email notifications (optional)

---

## 🚀 **Ready to Start?**

Begin with Phase 1, Step 1:

```bash
cd /home/user/refundengine
./scripts/deploy_excel_versioning.sh
```

**Estimated time to working prototype:** 4 weeks
**Estimated time to MVP:** 2 weeks (Phases 1-3 only)

Good luck! 🎉

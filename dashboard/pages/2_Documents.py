"""
Documents Page - Upload and manage documents

Upload invoices, contracts, and supporting documentation for analysis.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.utils.data_loader import get_documents_from_db, get_projects_from_db

# File upload security settings
MAX_FILE_SIZE_MB = 10
MAX_TOTAL_SIZE_MB = 50
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.csv'}
DANGEROUS_EXTENSIONS = {'.exe', '.bat', '.sh', '.cmd', '.ps1', '.jar', '.app', '.deb', '.rpm'}

# Page configuration
st.set_page_config(
    page_title="Documents - TaxDesk",
    page_icon="📄",
    layout="wide"
)

# AUTHENTICATION
from core.auth import require_authentication
if not require_authentication():
    st.stop()

# Header
st.markdown('<div class="main-header">📄 Documents</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Upload and manage invoices, contracts, and supporting documents</div>', unsafe_allow_html=True)

# Action buttons
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("📤 Upload Documents", type="primary", use_container_width=True):
        st.session_state.show_upload = True

with col2:
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.success("Document status refreshed")

st.markdown("---")

# Upload form
if st.session_state.get('show_upload', False):
    with st.expander("📤 Upload New Documents", expanded=True):
        projects = get_projects_from_db()
        project_options = {p['id']: p['name'] for p in projects}

        selected_project = st.selectbox(
            "Select Project*",
            options=list(project_options.keys()),
            format_func=lambda x: project_options[x]
        )

        doc_type = st.selectbox(
            "Document Type*",
            ["Invoice", "Contract/SOW", "Purchase Order", "Receipt", "Statement", "Other"]
        )

        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            type=['pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'csv'],
            help=f"Max {MAX_FILE_SIZE_MB}MB per file, {MAX_TOTAL_SIZE_MB}MB total"
        )

        # File validation
        validation_errors = []
        valid_files = []

        if uploaded_files:
            total_size = 0
            for file in uploaded_files:
                # Check file size
                file_size_mb = file.size / (1024 * 1024)
                total_size += file_size_mb

                if file_size_mb > MAX_FILE_SIZE_MB:
                    validation_errors.append(f"❌ {file.name}: File too large ({file_size_mb:.1f}MB, max {MAX_FILE_SIZE_MB}MB)")
                    continue

                # Check file extension
                import os
                file_ext = os.path.splitext(file.name)[1].lower()

                if file_ext in DANGEROUS_EXTENSIONS:
                    validation_errors.append(f"❌ {file.name}: Dangerous file type not allowed ({file_ext})")
                    continue

                if file_ext not in ALLOWED_EXTENSIONS:
                    validation_errors.append(f"❌ {file.name}: File type not allowed ({file_ext})")
                    continue

                # File passed validation
                valid_files.append(file)

            # Check total size
            if total_size > MAX_TOTAL_SIZE_MB:
                st.error(f"❌ Total file size ({total_size:.1f}MB) exceeds limit of {MAX_TOTAL_SIZE_MB}MB")
                valid_files = []

            # Display validation results
            if validation_errors:
                for error in validation_errors:
                    st.warning(error)

            if valid_files:
                st.success(f"✅ {len(valid_files)} file(s) ready for upload")
                for file in valid_files:
                    st.write(f"- {file.name} ({file.size:,} bytes)")

        notes = st.text_area("Notes (Optional)", placeholder="Any additional context about these documents...")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Upload & Process", type="primary", use_container_width=True, disabled=not valid_files):
                if valid_files:
                    st.success(f"✅ Uploaded {len(valid_files)} documents successfully!")
                    st.info("Documents are being processed. Check back soon for analysis results.")
                    st.session_state.show_upload = False
                    st.rerun()

        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_upload = False
                st.rerun()

    st.markdown("---")

# Load documents
documents = get_documents_from_db()

# Filter section
st.markdown("### 🔍 Filters")
col1, col2, col3, col4 = st.columns(4)

with col1:
    filter_status = st.selectbox(
        "Status",
        ["All", "Uploaded", "OCR Processing", "Parsed", "Analyzed", "Needs Review"]
    )

with col2:
    filter_type = st.selectbox(
        "Type",
        ["All", "Invoice", "Contract/SOW", "Purchase Order", "Receipt", "Statement"]
    )

with col3:
    projects = get_projects_from_db()
    filter_project = st.selectbox(
        "Project",
        ["All"] + [p['name'] for p in projects]
    )

with col4:
    st.write("")  # Spacing
    if st.button("🗑️ Clear Filters", use_container_width=True):
        st.rerun()

st.markdown("---")

# Display documents
st.markdown(f"### 📋 All Documents ({len(documents)})")

if not documents:
    st.info("No documents uploaded yet. Upload your first document to get started!")
else:
    # Create a table-like display
    for doc in documents:
        status_class = {
            'Parsed': 'success',
            'Analyzed': 'success',
            'OCR Processing': 'warning',
            'Uploaded': 'info',
            'Needs Review': 'danger',
            'Error': 'danger'
        }.get(doc['status'], 'neutral')

        st.markdown(f"""
        <div class="section-card">
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 1rem; align-items: center;">
                <div>
                    <div style="font-weight: 600; color: #1a202c;">📄 {doc['id']}</div>
                    <div style="font-size: 0.875rem; color: #718096; margin-top: 0.25rem;">
                        {doc.get('vendor', 'N/A')} | {doc['type']}
                    </div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #718096; text-transform: uppercase;">Date</div>
                    <div style="font-weight: 500; color: #4a5568;">{doc.get('date', 'N/A')}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #718096; text-transform: uppercase;">Invoice #</div>
                    <div style="font-weight: 500; color: #4a5568;">{doc.get('invoice_number', 'N/A')}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #718096; text-transform: uppercase;">Status</div>
                    <span class="badge {status_class}">{doc['status']}</span>
                </div>
                <div style="text-align: right;">
                    <button style="padding: 0.5rem 1rem; background: #3182ce; color: white; border: none; border-radius: 0.375rem; cursor: pointer; font-size: 0.875rem;">
                        View →
                    </button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

        # Initialize session state for this document
        view_key = f"viewing_{doc['id']}"
        if view_key not in st.session_state:
            st.session_state[view_key] = False

        with col1:
            if st.button("👁️ View", key=f"view_{doc['id']}", use_container_width=True):
                st.session_state[view_key] = not st.session_state[view_key]
                st.rerun()

        with col2:
            if st.button("🔄 Reprocess", key=f"reprocess_{doc['id']}", use_container_width=True):
                st.success(f"Reprocessing {doc['id']}")

        with col3:
            if st.button("🗑️ Delete", key=f"delete_{doc['id']}", use_container_width=True):
                st.warning(f"Delete {doc['id']}? (Not implemented)")

        # Show document details if viewing
        if st.session_state.get(view_key, False):
            with st.expander(f"📄 Document Details: {doc['id']}", expanded=True):
                col_detail1, col_detail2 = st.columns([2, 1])

                with col_detail1:
                    st.markdown("#### 📋 Document Information")
                    st.markdown(f"**File Name:** {doc['id']}")
                    st.markdown(f"**File Type:** {doc['type']} (`.{doc.get('file_extension', 'unknown').lower()}`)")
                    st.markdown(f"**Vendor:** {doc['vendor']}")
                    st.markdown(f"**Invoice Number:** {doc['invoice_number']}")
                    if doc.get('purchase_order') != 'N/A':
                        st.markdown(f"**PO Number:** {doc['purchase_order']}")
                    st.markdown(f"**Status:** {doc['status']}")

                    if doc.get('description') and doc['description'] != 'N/A':
                        st.markdown("**Description:**")
                        st.info(doc['description'])

                with col_detail2:
                    st.markdown("#### 💰 Financial Details")
                    if doc.get('amount'):
                        st.metric("Amount", f"${doc['amount']:,.2f}")
                    if doc.get('tax_amount'):
                        st.metric("Tax", f"${doc['tax_amount']:,.2f}")

                st.markdown("---")
                st.markdown("#### 📎 File Preview")

                # Check if file actually exists
                from pathlib import Path
                file_path = Path('test_data/invoices') / doc['id']

                file_ext = doc.get('file_extension', '').upper()

                if file_path.exists():
                    if file_ext == 'PDF':
                        # Display PDF
                        with open(file_path, 'rb') as f:
                            pdf_bytes = f.read()

                        # Provide download button
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_bytes,
                            file_name=doc['id'],
                            mime="application/pdf",
                            use_container_width=True
                        )

                        # Show PDF using base64 encoding in iframe
                        import base64
                        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)

                    elif file_ext in ['XLSX', 'XLS']:
                        # Display Excel data
                        import pandas as pd
                        excel_df = pd.read_excel(file_path)
                        st.dataframe(excel_df, use_container_width=True)

                        # Download button
                        with open(file_path, 'rb') as f:
                            excel_bytes = f.read()
                        st.download_button(
                            label="📥 Download Excel",
                            data=excel_bytes,
                            file_name=doc['id'],
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

                    elif file_ext in ['JPG', 'JPEG', 'PNG']:
                        # Display image
                        try:
                            from PIL import Image
                            img = Image.open(file_path)
                            st.image(img, use_column_width=True)

                            # Download button
                            with open(file_path, 'rb') as f:
                                image_bytes = f.read()
                            st.download_button(
                                label="📥 Download Image",
                                data=image_bytes,
                                file_name=doc['id'],
                                mime=f"image/{file_ext.lower()}",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"❌ Unable to display image: {str(e)}")
                            st.info("💡 This appears to be a placeholder file. In production, actual scanned invoice images would be stored here.")

                            # Show a placeholder message
                            st.markdown("""
                            <div style="background: #2d3748; padding: 4rem; text-align: center; border-radius: 0.5rem;">
                                <div style="font-size: 4rem; margin-bottom: 1rem;">🖼️</div>
                                <div style="color: #a0aec0; font-size: 1.2rem;">Scanned Invoice Image</div>
                                <div style="color: #718096; margin-top: 0.5rem;">{}</div>
                            </div>
                            """.format(doc['id']), unsafe_allow_html=True)
                    else:
                        st.info(f"📁 {file_ext} file preview not supported")
                else:
                    st.warning(f"⚠️ File not found: {doc['id']}")
                    st.info("The file may not have been uploaded yet or the path is incorrect.")

                # Purchase Order Preview Section
                if doc.get('purchase_order_file') and pd.notna(doc['purchase_order_file']):
                    st.markdown("---")
                    st.markdown("#### 📋 Related Purchase Order")

                    po_file_path = Path('test_data/purchase_orders') / doc['purchase_order_file']

                    if po_file_path.exists():
                        st.markdown(f"**PO Number:** {doc.get('purchase_order', 'N/A')}")
                        st.markdown(f"**PO File:** {doc['purchase_order_file']}")

                        # Show PO preview in expandable section
                        with st.expander("📄 View Purchase Order", expanded=False):
                            with open(po_file_path, 'rb') as f:
                                po_bytes = f.read()

                            # Download button
                            st.download_button(
                                label="📥 Download PO",
                                data=po_bytes,
                                file_name=doc['purchase_order_file'],
                                mime="application/pdf",
                                use_container_width=True,
                                key=f"download_po_{doc['id']}"
                            )

                            # Display PO PDF
                            import base64
                            base64_po = base64.b64encode(po_bytes).decode('utf-8')
                            po_display = f'<iframe src="data:application/pdf;base64,{base64_po}" width="100%" height="600" type="application/pdf"></iframe>'
                            st.markdown(po_display, unsafe_allow_html=True)
                    else:
                        st.info(f"📋 PO File: {doc['purchase_order_file']} (not found)")

                if st.button("❌ Close", key=f"close_{doc['id']}", use_container_width=False):
                    st.session_state[view_key] = False
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("📄 Document Management | TaxDesk Platform")

# TaxDesk Dashboard

A comprehensive multi-page Streamlit dashboard for tax refund analysis and management.

## Features

### 📊 Dashboard (Main Page)
- **Overview metrics**: Open projects, documents awaiting review, exceptions, draft claims
- **Project spotlight**: Quick actions for active projects
- **Recent activity**: Timeline of recent system events
- **Summary cards**: Visual metrics with drill-down links

### 📁 Projects Page
- **Project management**: Create, view, and manage tax refund projects
- **Project details**: Deep dive into individual project analytics
- **Status tracking**: Monitor project progress and estimated refunds
- **Activity timeline**: View project history and changes

### 📄 Documents Page
- **Upload documents**: Support for PDFs, images, Excel files
- **OCR processing**: Automatic text extraction from scanned documents
- **Status tracking**: Monitor document parsing and analysis progress
- **Filtering**: Search and filter by status, type, project, vendor

### 🔍 Review Queue Page
- **Exception management**: Review transactions flagged for manual analysis
- **Confidence filtering**: Filter by AI confidence scores
- **Bulk actions**: Approve or reject multiple items at once
- **Detailed analysis**: View AI reasoning and legal context
- **Analyst workflow**: Add notes, adjust amounts, make decisions

### 📋 Claims Page
- **Claim drafting**: Create and manage refund claims
- **Transaction inclusion**: Select approved transactions for claims
- **Documentation**: Attach supporting documents and evidence
- **Export functionality**: Generate claim reports and summaries
- **Status tracking**: Monitor draft, submitted, and approved claims

### 📚 Rules & Guidance Page
- **Browse tax rules**: Search through RCW, WAC, and guidance documents
- **Category filtering**: Filter by statute, regulation, legislation, guidance
- **Quick access**: Shortcut links to ESSB 5814, digital services, exemptions
- **Citation management**: Easy reference and copy citations

## Architecture

```
dashboard/
├── Dashboard.py              # Main entry point (home page)
├── pages/                    # Multi-page app pages
│   ├── 1_Projects.py        # Projects management
│   ├── 2_Documents.py       # Document upload/management
│   ├── 3_Review_Queue.py    # Exception review workflow
│   ├── 4_Claims.py          # Claims drafting/submission
│   └── 5_Rules.py           # Tax rules browser
└── utils/                    # Shared utilities
    ├── data_loader.py       # Data loading functions
    └── __init__.py
```

## Running the Dashboard

### Quick Start
```bash
./scripts/launch_taxdesk_dashboard.sh
```

### Manual Start
```bash
streamlit run dashboard/Dashboard.py --server.port 5001
```

Then open your browser to: http://localhost:5001

## Navigation

The dashboard uses Streamlit's native multi-page app functionality:
- Pages appear automatically in the sidebar
- Files are sorted alphabetically (hence the number prefixes)
- Each page is a standalone Python file in the `pages/` directory

## Data Sources

The dashboard connects to multiple data sources:

1. **Excel Files**: Analyzed transaction data from `test_data/Master_Claim_Sheet_ANALYZED.xlsx`
2. **Supabase Database**: Projects, documents, knowledge base (when available)
3. **Mock Data**: Fallback data for demonstration purposes

## Customization

### Adding New Pages
Create a new `.py` file in `dashboard/pages/` with the naming convention:
```
<number>_<PageName>.py
```

Example: `6_Analytics.py`

### Custom Styling
The main `Dashboard.py` file contains custom CSS in the `st.markdown()` call. Modify the CSS variables and classes there to change the theme.

### Data Integration
Modify `dashboard/utils/data_loader.py` to connect to your actual data sources:
- Replace mock data functions with real database queries
- Add new data loading functions as needed
- Update connection parameters

## Features Inspired By

This dashboard was inspired by modern tax software UIs and includes:
- Clean, professional design
- Card-based layouts
- Status badges and visual indicators
- Intuitive navigation
- Responsive multi-column layouts
- Action buttons and workflows
- Expandable detail views

## Future Enhancements

Potential additions:
- [ ] Real-time collaboration features
- [ ] Advanced analytics and charts (Power BI integration)
- [ ] Email notifications
- [ ] Audit trail and change history
- [ ] User roles and permissions
- [ ] API integrations with state tax portals
- [ ] Automated claim submission
- [ ] Machine learning model feedback loop

## Dependencies

- `streamlit>=1.28.0`
- `pandas`
- `openpyxl` (for Excel file support)
- `python-dotenv`
- Supabase client (optional, for database features)

## Notes

- The dashboard is designed to work with or without a database connection
- Mock data is provided for demonstration purposes
- All pages are responsive and work on different screen sizes
- The design follows the TaxDesk mockup provided by the user

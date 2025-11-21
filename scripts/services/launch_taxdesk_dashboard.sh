#!/bin/bash
# Launch TaxDesk Multi-Page Dashboard
#
# This script starts the comprehensive TaxDesk dashboard with multiple pages:
# - Dashboard (overview)
# - Projects
# - Documents
# - Review Queue
# - Claims
# - Rules & Guidance

echo "======================================================================"
echo "🚀 LAUNCHING TAXDESK DASHBOARD"
echo "======================================================================"
echo ""
echo "📊 Multi-page dashboard with:"
echo "   - Dashboard overview"
echo "   - Projects management"
echo "   - Document upload & processing"
echo "   - Review queue for flagged transactions"
echo "   - Claims drafting & submission"
echo "   - Tax rules & guidance browser"
echo ""
echo "🌐 Opening at: http://localhost:5001"
echo ""
echo "📝 Press CTRL+C to stop the server"
echo ""

cd "$(dirname "$0")/.."
streamlit run dashboard/Dashboard.py --server.port 5001

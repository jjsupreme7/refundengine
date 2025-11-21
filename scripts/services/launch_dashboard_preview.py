#!/usr/bin/env python3
"""
Launch a simple dashboard preview to view analyzed test data.

This creates a Flask web app showing:
- Analysis summary statistics
- Review queue (< 90% confidence)
- All analyzed transactions
- Vendor breakdown
"""

from pathlib import Path

import pandas as pd
from flask import Flask, render_template_string

app = Flask(__name__)

# Load analyzed data
EXCEL_PATH = Path("test_data/Master_Claim_Sheet_ANALYZED.xlsx")
df = pd.read_excel(EXCEL_PATH)

# Dashboard HTML template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Tax Refund Analysis Dashboard - Preview</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            color: #1a202c;
            margin-bottom: 10px;
            font-size: 32px;
        }
        .subtitle {
            color: #718096;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            color: #718096;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 8px;
            text-transform: uppercase;
        }
        .stat-card .value {
            color: #1a202c;
            font-size: 32px;
            font-weight: 700;
        }
        .stat-card .value.green { color: #38a169; }
        .stat-card .value.red { color: #e53e3e; }
        .stat-card .value.blue { color: #3182ce; }
        .stat-card .sub {
            color: #a0aec0;
            font-size: 12px;
            margin-top: 5px;
        }
        .section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .section h2 {
            color: #1a202c;
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th {
            background: #f7fafc;
            color: #4a5568;
            font-weight: 600;
            text-align: left;
            padding: 12px;
            border-bottom: 2px solid #e2e8f0;
            font-size: 12px;
            text-transform: uppercase;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
            color: #2d3748;
        }
        tr:hover {
            background: #f7fafc;
        }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }
        .badge.high { background: #c6f6d5; color: #22543d; }
        .badge.medium { background: #fef5e7; color: #975a16; }
        .badge.low { background: #fed7d7; color: #742a2a; }
        .badge.flagged { background: #feebc8; color: #7c2d12; }
        .vendor-chip {
            display: inline-block;
            background: #ebf4ff;
            color: #2c5282;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
        }
        .amount { font-family: 'Monaco', 'Courier New', monospace; }
        .decision-add { color: #38a169; font-weight: 600; }
        .decision-review { color: #d69e2e; font-weight: 600; }
        .decision-no { color: #718096; }
        .truncate {
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Tax Refund Analysis Dashboard</h1>
        <p class="subtitle">Preview of analyzed transactions from Master_Claim_Sheet_ANALYZED.xlsx</p>

        <!-- Summary Statistics -->
        <div class="stats">
            <div class="stat-card">
                <h3>Total Transactions</h3>
                <div class="value">{{ total_rows }}</div>
                <div class="sub">Across {{ unique_invoices }} invoices</div>
            </div>
            <div class="stat-card">
                <h3>Est. Total Refund</h3>
                <div class="value green">${{ "{:,.2f}".format(total_refund) }}</div>
                <div class="sub">{{ refund_rows }} refundable items</div>
            </div>
            <div class="stat-card">
                <h3>Avg Confidence</h3>
                <div class="value blue">{{ "{:.1f}".format(avg_confidence) }}%</div>
                <div class="sub">AI confidence score</div>
            </div>
            <div class="stat-card">
                <h3>Review Queue</h3>
                <div class="value red">{{ flagged_count }}</div>
                <div class="sub">{{ "{:.1f}".format(flagged_pct) }}% flagged (< 90%)</div>
            </div>
        </div>

        <!-- Review Queue -->
        <div class="section">
            <h2>🚨 Review Queue (< 90% Confidence)</h2>
            {% if review_queue|length > 0 %}
            <table>
                <thead>
                    <tr>
                        <th>Vendor</th>
                        <th>Description</th>
                        <th>Amount</th>
                        <th>Tax</th>
                        <th>Decision</th>
                        <th>Confidence</th>
                        <th>Refund</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in review_queue %}
                    <tr>
                        <td><span class="vendor-chip">{{ row.Vendor_Name }}</span></td>
                        <td class="truncate" title="{{ row.Line_Item_Description }}">{{ row.Line_Item_Description }}</td>
                        <td class="amount">${{ "{:,.2f}".format(row.Total_Amount) }}</td>
                        <td class="amount">${{ "{:,.2f}".format(row.Tax_Amount) }}</td>
                        <td>
                            {% if 'Add to Claim' in row.Final_Decision %}
                            <span class="decision-add">{{ row.Final_Decision }}</span>
                            {% elif 'Needs Review' in row.Final_Decision %}
                            <span class="decision-review">{{ row.Final_Decision }}</span>
                            {% else %}
                            <span class="decision-no">{{ row.Final_Decision }}</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if row.AI_Confidence < 70 %}
                            <span class="badge low">{{ "{:.0f}".format(row.AI_Confidence) }}%</span>
                            {% elif row.AI_Confidence < 85 %}
                            <span class="badge medium">{{ "{:.0f}".format(row.AI_Confidence) }}%</span>
                            {% else %}
                            <span class="badge flagged">{{ "{:.0f}".format(row.AI_Confidence) }}%</span>
                            {% endif %}
                        </td>
                        <td class="amount">${{ "{:,.2f}".format(row.Estimated_Refund) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="color: #718096; text-align: center; padding: 40px;">No transactions flagged for review</p>
            {% endif %}
        </div>

        <!-- All Transactions -->
        <div class="section">
            <h2>📋 All Analyzed Transactions</h2>
            <table>
                <thead>
                    <tr>
                        <th>Vendor</th>
                        <th>Invoice #</th>
                        <th>Description</th>
                        <th>Amount</th>
                        <th>Tax</th>
                        <th>Decision</th>
                        <th>Confidence</th>
                        <th>Category</th>
                        <th>Refund</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in all_transactions %}
                    <tr>
                        <td><span class="vendor-chip">{{ row.Vendor_Name }}</span></td>
                        <td style="font-size: 11px; color: #718096;">{{ row.Invoice_Number }}</td>
                        <td class="truncate" title="{{ row.Line_Item_Description }}">{{ row.Line_Item_Description }}</td>
                        <td class="amount">${{ "{:,.2f}".format(row.Total_Amount) }}</td>
                        <td class="amount">${{ "{:,.2f}".format(row.Tax_Amount) }}</td>
                        <td>
                            {% if 'Add to Claim' in row.Final_Decision %}
                            <span class="decision-add">✓ Add to Claim</span>
                            {% elif 'Needs Review' in row.Final_Decision %}
                            <span class="decision-review">⚠ {{ row.Final_Decision }}</span>
                            {% else %}
                            <span class="decision-no">{{ row.Final_Decision }}</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if row.AI_Confidence >= 90 %}
                            <span class="badge high">{{ "{:.0f}".format(row.AI_Confidence) }}%</span>
                            {% elif row.AI_Confidence >= 70 %}
                            <span class="badge medium">{{ "{:.0f}".format(row.AI_Confidence) }}%</span>
                            {% else %}
                            <span class="badge low">{{ "{:.0f}".format(row.AI_Confidence) }}%</span>
                            {% endif %}
                        </td>
                        <td style="font-size: 11px; color: #718096;">{{ row.Tax_Category }}</td>
                        <td class="amount">${{ "{:,.2f}".format(row.Estimated_Refund) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Footer -->
        <div style="text-align: center; padding: 20px; color: #a0aec0; font-size: 12px;">
            <p>Generated from: {{ excel_file }}</p>
            <p style="margin-top: 5px;">Tax Refund Analysis Engine - Preview Dashboard</p>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def dashboard():
    """Main dashboard view."""

    # Calculate statistics
    total_rows = len(df)
    unique_invoices = df["Invoice_Number"].nunique()
    total_refund = df["Estimated_Refund"].sum()
    avg_confidence = df["AI_Confidence"].mean()
    flagged = df[df["AI_Confidence"] < 90]
    flagged_count = len(flagged)
    flagged_pct = (flagged_count / total_rows * 100) if total_rows > 0 else 0
    refund_rows = len(df[df["Estimated_Refund"] > 0])

    # Prepare data for template
    review_queue = flagged.to_dict("records")
    all_transactions = df.to_dict("records")

    return render_template_string(
        DASHBOARD_TEMPLATE,
        total_rows=total_rows,
        unique_invoices=unique_invoices,
        total_refund=total_refund,
        avg_confidence=avg_confidence,
        flagged_count=flagged_count,
        flagged_pct=flagged_pct,
        refund_rows=refund_rows,
        review_queue=review_queue,
        all_transactions=all_transactions,
        excel_file=EXCEL_PATH.name,
    )


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🚀 LAUNCHING DASHBOARD PREVIEW")
    print("=" * 80)
    print(f"\n📊 Loaded {len(df)} transactions from {EXCEL_PATH.name}")
    print("\n🌐 Opening dashboard at: http://localhost:5001")
    print("\n📝 Press CTRL+C to stop the server\n")

    app.run(debug=True, port=5001, use_reloader=False)

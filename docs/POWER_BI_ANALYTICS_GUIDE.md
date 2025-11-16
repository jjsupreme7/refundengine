# Power BI Analytics for Refund Engine

## Overview

This guide provides a complete Power BI implementation for tracking and analyzing the tax refund workflow end-to-end.

---

## 🎯 Key Performance Indicators (KPIs)

### Executive KPIs
1. **Total Estimated Refund** - Aggregate refund opportunity
2. **Refund Conversion Rate** - (Filed Claims / Total Opportunities)
3. **Average Claim Value** - Mean refund per claim
4. **Time to Claim** - Days from document upload to claim filed

### Operational KPIs
5. **AI Accuracy Rate** - (Accepted AI Decisions / Total Decisions)
6. **Exception Rate** - (Flagged for Review / Total Line Items)
7. **Average Confidence Score** - Mean AI confidence across analyses
8. **Documents Processed per Day** - Processing throughput

### Analyst Productivity KPIs
9. **Reviews per Analyst** - Daily/weekly review count
10. **Average Review Time** - Minutes per line item
11. **Override Rate** - (Manual Overrides / Total Reviews)

---

## 📊 Data Model

### Star Schema Design

```
        DimDate
           |
           |
      FactInvoiceLines -------- DimVendors
           |      |
           |      |------------ DimCategories
           |      |
           |      |------------ DimProjects
           |
      FactReviews ------------- DimAnalysts
           |
           |
      FactClaims
```

---

## 📋 Table Definitions

### Fact Tables

#### 1. FactInvoiceLines
**Purpose**: Core transactional fact table

| Column | Type | Description |
|--------|------|-------------|
| InvoiceLineID | PK | Unique line item identifier |
| InvoiceID | FK | Parent invoice |
| ProjectID | FK | Related project |
| VendorID | FK | Vendor lookup |
| CategoryID | FK | Tax category lookup |
| DateID | FK | Transaction date |
| LineItemAmount | Decimal(12,2) | Pre-tax amount |
| TaxCharged | Decimal(12,2) | Sales tax charged |
| EstimatedRefund | Decimal(12,2) | Calculated refund |
| RefundPercentage | Decimal(5,2) | % of tax to refund |
| ConfidenceScore | Decimal(5,2) | AI confidence (0-100) |
| Taxability | Varchar(50) | taxable, exempt, partial, needs review |
| RefundBasis | Varchar(100) | MPU, Out of State, Non-Taxable, etc. |
| ReviewStatus | Varchar(20) | ok, exception |
| ProcessedDate | Date | When AI analyzed |

**Source Query** (Supabase):
```sql
SELECT
    ar.id AS InvoiceLineID,
    ar.invoice_number AS InvoiceID,
    'WA-UT-2022_2024' AS ProjectID,  -- Lookup via project mapping
    kd.id AS VendorID,
    ar.ai_product_type AS CategoryID,
    ar.created_at::date AS DateID,
    ar.amount AS LineItemAmount,
    ar.tax_amount AS TaxCharged,
    ar.ai_estimated_refund AS EstimatedRefund,
    ar.ai_refund_percentage AS RefundPercentage,
    ar.ai_confidence AS ConfidenceScore,
    CASE
        WHEN ar.ai_refund_percentage > 0 THEN 'exempt'
        ELSE 'taxable'
    END AS Taxability,
    ar.ai_refund_basis AS RefundBasis,
    ar.analysis_status AS ReviewStatus,
    ar.created_at AS ProcessedDate
FROM analysis_results ar
LEFT JOIN knowledge_documents kd
    ON ar.vendor_name = kd.vendor_name
    AND kd.document_type = 'vendor_background'
```

#### 2. FactReviews
**Purpose**: Track human review activity

| Column | Type | Description |
|--------|------|-------------|
| ReviewID | PK | Unique review ID |
| InvoiceLineID | FK | Line item reviewed |
| AnalystID | FK | Analyst who reviewed |
| ReviewDate | Date | Review timestamp |
| OriginalDetermination | Varchar(50) | AI's original call |
| FinalDetermination | Varchar(50) | After human review |
| WasOverridden | Boolean | Did analyst change it? |
| TimeToReviewSeconds | Int | Seconds spent reviewing |
| ConfidenceChange | Decimal(5,2) | Change in confidence |

**Source Query**:
```sql
SELECT
    rev.id AS ReviewID,
    rev.analysis_id AS InvoiceLineID,
    'analyst_1' AS AnalystID,  -- Add user tracking
    rev.reviewed_at AS ReviewDate,
    ar.ai_refund_basis AS OriginalDetermination,
    rev.corrected_refund_basis AS FinalDetermination,
    CASE
        WHEN rev.corrected_refund_basis IS NOT NULL
            AND rev.corrected_refund_basis != ar.ai_refund_basis
        THEN TRUE
        ELSE FALSE
    END AS WasOverridden,
    EXTRACT(EPOCH FROM (rev.reviewed_at - ar.created_at)) AS TimeToReviewSeconds,
    COALESCE(rev.corrected_refund_percentage, ar.ai_refund_percentage) - ar.ai_refund_percentage AS ConfidenceChange
FROM analysis_reviews rev
JOIN analysis_results ar ON rev.analysis_id = ar.id
```

#### 3. FactClaims
**Purpose**: Track filed claims

| Column | Type | Description |
|--------|------|-------------|
| ClaimID | PK | Unique claim ID |
| ProjectID | FK | Related project |
| FiledDate | Date | Date claim filed |
| ClaimPeriodStart | Date | Period start |
| ClaimPeriodEnd | Date | Period end |
| TotalLineItems | Int | Number of line items |
| TotalRefund | Decimal(12,2) | Claim amount |
| Status | Varchar(20) | Draft, Filed, Pending, Paid |
| ApprovedAmount | Decimal(12,2) | Amount approved |
| PaidDate | Date | Payment received date |

**Note**: This table doesn't exist yet - needs to be created

### Dimension Tables

#### 1. DimProjects

| Column | Type | Description |
|--------|------|-------------|
| ProjectID | PK | Unique project ID |
| ProjectName | Varchar(200) | Full project name |
| Period | Varchar(50) | Tax period (e.g., "2022-2024") |
| ClientName | Varchar(200) | Client organization |
| Status | Varchar(20) | Analyzing, Reviewing, Complete, Filed |
| EstRefund | Decimal(12,2) | Estimated refund |
| CreatedDate | Date | Project start date |

#### 2. DimVendors

| Column | Type | Description |
|--------|------|-------------|
| VendorID | PK | Unique vendor ID |
| VendorName | Varchar(200) | Vendor name |
| Industry | Varchar(100) | Primary industry |
| BusinessModel | Varchar(100) | B2B SaaS, Manufacturing, etc. |
| VendorCategory | Varchar(50) | manufacturer, distributor, service_provider |
| ConfidenceScore | Decimal(5,2) | Metadata confidence |

**Source Query**:
```sql
SELECT
    id AS VendorID,
    vendor_name AS VendorName,
    industry AS Industry,
    business_model AS BusinessModel,
    vendor_category AS VendorCategory,
    confidence_score AS ConfidenceScore
FROM knowledge_documents
WHERE document_type = 'vendor_background'
```

#### 3. DimCategories

| Column | Type | Description |
|--------|------|-------------|
| CategoryID | PK | Category code |
| CategoryName | Varchar(100) | Display name |
| TaxCategoryGroup | Varchar(50) | Services, Goods, Mixed |
| IsRefundable | Boolean | Typical refund opportunity |

**Example Data**:
```
CategoryID | CategoryName           | TaxCategoryGroup | IsRefundable
-----------+------------------------+------------------+-------------
DAS        | Digital Automated Svc  | Services         | TRUE
CUSTOM_SW  | Custom Software        | Services         | TRUE
EQUIPMENT  | Tangible Goods         | Goods            | FALSE
PROF_SVC   | Professional Services  | Services         | TRUE
TELECOM    | Telecommunications     | Services         | FALSE
```

#### 4. DimAnalysts

| Column | Type | Description |
|--------|------|-------------|
| AnalystID | PK | Unique analyst ID |
| Name | Varchar(100) | Full name |
| Role | Varchar(50) | client, analyst, admin |
| StartDate | Date | When started |

#### 5. DimDate

Standard date dimension with:
- Date, Year, Quarter, Month, Week, Day
- Fiscal periods
- Holiday flags
- Weekend flags

---

## 📈 DAX Measures

### Core Measures

```dax
// Total Refund Amount
TotalRefundAmount =
    SUM(FactInvoiceLines[EstimatedRefund])

// Average Confidence Score
AvgConfidence =
    AVERAGE(FactInvoiceLines[ConfidenceScore])

// Exception Rate
ExceptionRate =
    DIVIDE(
        CALCULATE(
            COUNTROWS(FactInvoiceLines),
            FactInvoiceLines[ReviewStatus] = "exception"
        ),
        COUNTROWS(FactInvoiceLines)
    )

// AI Accuracy (Acceptance Rate)
AIAccuracy =
    VAR TotalReviews = COUNTROWS(FactReviews)
    VAR AcceptedReviews =
        CALCULATE(
            COUNTROWS(FactReviews),
            FactReviews[WasOverridden] = FALSE
        )
    RETURN
    DIVIDE(AcceptedReviews, TotalReviews)

// Override Rate
OverrideRate =
    DIVIDE(
        CALCULATE(
            COUNTROWS(FactReviews),
            FactReviews[WasOverridden] = TRUE
        ),
        COUNTROWS(FactReviews)
    )

// Average Time to Review (minutes)
AvgReviewTimeMinutes =
    DIVIDE(
        AVERAGE(FactReviews[TimeToReviewSeconds]),
        60
    )

// Refund by Category
RefundByCategory =
    CALCULATE(
        [TotalRefundAmount],
        ALLEXCEPT(DimCategories, DimCategories[CategoryName])
    )

// Refund Conversion Rate
RefundConversionRate =
    DIVIDE(
        CALCULATE(
            COUNTROWS(FactClaims),
            FactClaims[Status] = "Filed"
        ),
        CALCULATE(
            DISTINCTCOUNT(FactInvoiceLines[ProjectID])
        )
    )

// Month Over Month Growth
RefundMoM =
    VAR CurrentMonth = [TotalRefundAmount]
    VAR PrevMonth =
        CALCULATE(
            [TotalRefundAmount],
            DATEADD(DimDate[Date], -1, MONTH)
        )
    RETURN
    DIVIDE(CurrentMonth - PrevMonth, PrevMonth)

// High Confidence Items (>85%)
HighConfidenceCount =
    CALCULATE(
        COUNTROWS(FactInvoiceLines),
        FactInvoiceLines[ConfidenceScore] > 85
    )

// Refund Opportunity Funnel
OpportunityFunnel =
    VAR Opportunities = COUNTROWS(FactInvoiceLines)
    VAR Reviewed =
        CALCULATE(
            COUNTROWS(FactReviews)
        )
    VAR Filed =
        CALCULATE(
            COUNTROWS(FactClaims),
            FactClaims[Status] IN {"Filed", "Paid"}
        )
    RETURN
    "Opportunities: " & Opportunities & " | Reviewed: " & Reviewed & " | Filed: " & Filed
```

---

## 🎨 Dashboard Pages

### Page 1: Executive Overview

**Purpose**: High-level metrics for stakeholders

**Visualizations**:

1. **KPI Cards** (Top Row)
   - Total Estimated Refund (large card)
   - Refund Conversion Rate (%)
   - Active Projects (count)
   - Average Claim Value

2. **Refund Trend** (Line Chart)
   - X-axis: Month
   - Y-axis: Total Estimated Refund
   - Legend: Project
   - Tooltip: Count of line items

3. **Refund by Tax Category** (Donut Chart)
   - Values: Total Estimated Refund
   - Legend: Category Name
   - Data labels: Percentage

4. **Top 10 Vendors** (Bar Chart - Horizontal)
   - X-axis: Total Estimated Refund
   - Y-axis: Vendor Name
   - Sort: Descending by refund

5. **Project Status** (Stacked Bar Chart)
   - X-axis: Project Name
   - Y-axis: Count of Line Items
   - Legend: Review Status (ok vs exception)

6. **Refund Funnel** (Funnel Chart)
   - Stages: Opportunities → Reviewed → Filed → Paid
   - Values: Count of unique items

### Page 2: AI Performance Analytics

**Purpose**: Track AI accuracy and improvement

**Visualizations**:

1. **Performance KPIs** (Cards)
   - AI Accuracy Rate (%)
   - Average Confidence Score
   - Exception Rate (%)
   - Override Rate (%)

2. **Confidence Distribution** (Histogram)
   - X-axis: Confidence bins (0-20, 20-40, ..., 80-100)
   - Y-axis: Count of line items
   - Color: Review Status

3. **AI Accuracy Trend** (Line Chart)
   - X-axis: Month
   - Y-axis: AI Accuracy %
   - Benchmark line: 85% target

4. **Exceptions by Category** (Clustered Bar Chart)
   - X-axis: Category
   - Y-axis: Count
   - Bars: Total line items vs Exceptions

5. **Override Reasons** (Tree Map)
   - Values: Count of overrides
   - Groups: Original Determination → Final Determination
   - Color: Count

6. **Confidence vs Accuracy Scatter** (Scatter Plot)
   - X-axis: Confidence Score
   - Y-axis: Was Overridden (1 = yes, 0 = no)
   - Trend line
   - Tooltip: Vendor, Category

### Page 3: Analyst Productivity

**Purpose**: Monitor team performance

**Visualizations**:

1. **Productivity KPIs** (Cards)
   - Total Reviews This Week
   - Avg Review Time (minutes)
   - Reviews per Analyst per Day
   - Backlog Size (exceptions pending)

2. **Daily Review Volume** (Area Chart)
   - X-axis: Date
   - Y-axis: Count of reviews
   - Stacked: By analyst

3. **Review Time Distribution** (Box Plot)
   - X-axis: Analyst
   - Y-axis: Review time (seconds)
   - Quartiles shown

4. **Analyst Comparison** (Table)
   - Columns:
     - Analyst Name
     - Total Reviews
     - Avg Review Time
     - Override Rate %
     - Accuracy Score

5. **Review Backlog** (Gauge)
   - Value: Count of pending exceptions
   - Target: < 50
   - Red zone: > 100

6. **Hourly Review Pattern** (Column Chart)
   - X-axis: Hour of day (0-23)
   - Y-axis: Count of reviews
   - Identify peak hours

### Page 4: Vendor Intelligence

**Purpose**: Understand vendor patterns

**Visualizations**:

1. **Vendor KPIs** (Cards)
   - Total Vendors Analyzed
   - Avg Vendor Confidence Score
   - Vendors with Refund Opportunities
   - Top Vendor Refund Amount

2. **Refund Heatmap** (Matrix)
   - Rows: Vendor
   - Columns: Category
   - Values: Total Refund
   - Conditional formatting: Color scale

3. **Industry Breakdown** (Pie Chart)
   - Values: Total Refund
   - Legend: Industry
   - Filter: Show top 5

4. **Business Model Analysis** (Clustered Column Chart)
   - X-axis: Business Model
   - Y-axis: Total Refund
   - Series: Taxability

5. **Vendor Confidence Trends** (Line Chart)
   - X-axis: Vendor (sorted by transaction count)
   - Y-axis: Avg Confidence Score
   - Color: Industry

6. **Vendor Details Table** (Table with drill-through)
   - Columns:
     - Vendor Name
     - Industry
     - Transaction Count
     - Total Refund
     - Avg Confidence
     - Override Rate
   - Sort: By total refund descending

### Page 5: Refund Basis Analysis

**Purpose**: Understand why refunds occur

**Visualizations**:

1. **Refund Basis KPIs** (Cards)
   - MPU Refunds (total)
   - Out-of-State Refunds (total)
   - Non-Taxable Refunds (total)
   - Wrong Rate Refunds (total)

2. **Refund Basis Breakdown** (100% Stacked Bar Chart)
   - X-axis: Project
   - Y-axis: % of total refund
   - Legend: Refund Basis
   - Data labels: Percentage

3. **Basis by Category** (Clustered Bar Chart)
   - X-axis: Category
   - Y-axis: Count of line items
   - Bars: Grouped by Refund Basis

4. **Geographic Analysis** (Map - if locations available)
   - Bubbles: Total refund by state
   - Color: Refund basis (MPU, Out-of-state, etc.)

5. **Legal Citations** (Word Cloud - Custom Visual)
   - Words: RCW/WAC citations
   - Size: Frequency of use

6. **Refund Confidence by Basis** (Scatter Plot)
   - X-axis: Refund Basis
   - Y-axis: Confidence Score
   - Bubbles: Size = Refund Amount
   - Tooltip: Count, Avg Confidence

---

## 🔄 Data Refresh Strategy

### Option 1: Direct Query (Real-time)
- Connect Power BI directly to Supabase PostgreSQL
- Live data, no refresh needed
- May be slower with large datasets

### Option 2: Scheduled Import (Daily)
- Import data into Power BI model
- Refresh daily at 6:00 AM
- Faster reports, but data may be stale

### Option 3: Hybrid Approach
- Import dimension tables (vendors, categories) - weekly refresh
- Direct query fact tables (invoice lines, reviews) - real-time
- Best balance of performance and freshness

**Recommended**: Option 3 (Hybrid)

---

## 🔒 Row-Level Security (RLS)

### Security Roles

#### 1. Client Role
**Rule**: Only see their own project data

```dax
[ProjectID] = USERPRINCIPALNAME()
```

#### 2. Analyst Role
**Rule**: See all data

```dax
1 = 1  // No filter
```

#### 3. Vendor-Specific Access (if needed)
**Rule**: Only see specific vendors

```dax
[VendorID] IN VALUES(VendorAccess[VendorID])
```

---

## 🚀 Implementation Steps

### Phase 1: Setup (1 day)

1. **Install Power BI Desktop**
2. **Create Supabase Connection**:
   - Get Data → PostgreSQL
   - Server: `aws-0-us-west-1.pooler.supabase.com:6543`
   - Database: `postgres`
   - DirectQuery mode

3. **Import Dimension Tables**:
   - DimProjects (when created)
   - DimVendors
   - DimCategories
   - DimAnalysts
   - DimDate (generate in Power Query)

### Phase 2: Data Model (1 day)

1. **Load Fact Tables**:
   - FactInvoiceLines
   - FactReviews
   - FactClaims (when created)

2. **Create Relationships**:
   ```
   FactInvoiceLines[VendorID] → DimVendors[VendorID]
   FactInvoiceLines[CategoryID] → DimCategories[CategoryID]
   FactInvoiceLines[ProjectID] → DimProjects[ProjectID]
   FactInvoiceLines[DateID] → DimDate[Date]
   FactReviews[InvoiceLineID] → FactInvoiceLines[InvoiceLineID]
   ```

3. **Create Calculated Columns** (if needed)

4. **Create Measures** (all DAX formulas above)

### Phase 3: Dashboard Development (2-3 days)

1. **Build Page 1** (Executive Overview)
2. **Build Page 2** (AI Performance)
3. **Build Page 3** (Analyst Productivity)
4. **Build Page 4** (Vendor Intelligence)
5. **Build Page 5** (Refund Basis Analysis)

### Phase 4: Testing & Refinement (1 day)

1. **Test with Sample Data**
2. **Verify Calculations**
3. **Apply Themes/Branding**
4. **Add Tooltips and Interactions**

### Phase 5: Publish & Deploy (1 day)

1. **Publish to Power BI Service**
2. **Configure Refresh Schedule**
3. **Set Up Row-Level Security**
4. **Share with Stakeholders**

---

## 📊 Sample Power Query (M) Code

### Custom Date Dimension

```m
let
    StartDate = #date(2022, 1, 1),
    EndDate = #date(2025, 12, 31),
    NumberOfDays = Duration.Days(EndDate - StartDate) + 1,
    Dates = List.Dates(StartDate, NumberOfDays, #duration(1,0,0,0)),
    #"Converted to Table" = Table.FromList(Dates, Splitter.SplitByNothing(), {"Date"}),
    #"Changed Type" = Table.TransformColumnTypes(#"Converted to Table",{{"Date", type date}}),
    #"Added Year" = Table.AddColumn(#"Changed Type", "Year", each Date.Year([Date])),
    #"Added Quarter" = Table.AddColumn(#"Added Year", "Quarter", each "Q" & Text.From(Date.QuarterOfYear([Date]))),
    #"Added Month" = Table.AddColumn(#"Added Quarter", "Month", each Date.MonthName([Date])),
    #"Added Month Number" = Table.AddColumn(#"Added Month", "MonthNum", each Date.Month([Date])),
    #"Added Week" = Table.AddColumn(#"Added Month Number", "Week", each Date.WeekOfYear([Date])),
    #"Added Day Name" = Table.AddColumn(#"Added Week", "DayName", each Date.DayOfWeekName([Date])),
    #"Added Day Number" = Table.AddColumn(#"Added Day Name", "DayNum", each Date.DayOfWeek([Date])),
    #"Added Is Weekend" = Table.AddColumn(#"Added Day Number", "IsWeekend", each if [DayNum] >= 5 then true else false)
in
    #"Added Is Weekend"
```

---

## 🎯 Success Metrics

Track these to measure Power BI adoption:

1. **Usage Metrics**:
   - Daily active users
   - Page views per user
   - Average session duration

2. **Business Impact**:
   - Decisions made using dashboard
   - Time saved vs manual reporting
   - Insights discovered

3. **Data Quality**:
   - Refresh success rate (target: 99%)
   - Data freshness (< 24 hours)
   - Error rate (< 1%)

---

## Summary

This Power BI analytics system provides:
- **360° view** of refund workflow
- **Real-time** operational insights
- **AI performance** tracking
- **Analyst productivity** monitoring
- **Vendor intelligence** patterns
- **Executive reporting** for stakeholders

Combined with your dashboard UI, this creates a **comprehensive analytics platform** for tax refund management.

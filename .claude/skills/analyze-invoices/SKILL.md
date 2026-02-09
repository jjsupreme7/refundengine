# Analyze Invoices Skill

Analyze WA Sales Tax or Use Tax invoices with full research, contextual thinking, and proper citations.

## When This Skill Is Triggered
- User says "/analyze-invoices" or "analyze invoices"
- User asks to analyze Sales Tax 2024, Use Tax 2023, or Use Tax 2024
- User provides vendor names or filters for analysis

## Applicable Law Period (IMPORTANT)

**All transactions in these datasets occurred BEFORE ESSB 5814 (effective October 1, 2025).**

| Data Set | Transaction Period | Applicable Law |
|----------|-------------------|----------------|
| Sales Tax 2024 | 2024 | Pre-ESSB 5814 |
| Use Tax 2023 | 2023 | Pre-ESSB 5814 |
| Use Tax 2024 | 2024 | Pre-ESSB 5814 |

**Apply the law in effect at the time of the transaction**, not current law. Key pre-ESSB 5814 citations:

| Topic | Citation | Notes |
|-------|----------|-------|
| Multi-Point Use (Digital) | RCW 82.08.0208(4) / 82.12.0208(7) | Allocation for DAS used in multiple locations |
| Digital Automated Services | WAC 458-20-15502 | Definition and sourcing rules |
| Professional Services | RCW 82.04.050(6)(a); RCW 82.04.192(3)(b)(i) | Human effort exclusion |
| Construction Sourcing | WAC 458-20-170 | Sourced to job site location |
| Out-of-State Delivery | RCW 82.08.0264 / 82.12.0264 | Goods delivered outside WA |
| Custom Software | RCW 82.04.050(6)(a)(i)-(ii) | Excluded from retail sale definition |

**DO NOT apply ESSB 5814 rules to these historical transactions.** The new law only applies to transactions on or after October 1, 2025.

## How to Parse User Request

**Plain English Examples:**
- "analyze B & C TOWER rows over $500" → Filter: vendor contains "B & C TOWER", min_amount > 500
- "analyze In WA quadrant" → Filter: quadrant = "In WA"
- "analyze these vendors: [list]" → Filter: vendor in [list]
- "analyze Use Tax 2024 for ACME Corp" → File: Use Tax 2024, vendor = "ACME Corp"

## Standard Filters (Apply Automatically)

### Sales Tax 2024 (Real Run sheet from Final 2024 Denodo Review.xlsx)
1. Paid? = "PAID"
2. Recon Analysis = empty (not yet analyzed)
3. Inv 1 = not empty (has invoice)
4. Apply user's additional filters (quadrant, vendor, amount, rate)

### Use Tax 2023 & 2024
1. INDICATOR = "Remit" (exact match, not "Do Not Remit")
2. KOM Analysis & Notes = empty (not yet analyzed)
3. Apply user's additional filters (vendor list, amount)

## Core Philosophy: Contextual Thinking, Not Checklists

**DO NOT** mechanically check the same things for every invoice. **DO** think about what's in front of you and what could apply.

## First Principles Framework (Start Here Every Time)

### Step 0: The Skeptical Question
Before analyzing exemptions, ask: **"Should tax have been charged AT ALL?"**

Most transactions are taxed by default because vendors are cautious. Your job is to question whether the tax was legally required in the first place.

**Key questions:**
1. Does this meet the definition of a "retail sale" under RCW 82.04.050?
2. Is there a definitional EXCLUSION that means this was never taxable?
3. Does WA even have jurisdiction over this transaction?

### Step 1: Is This a Retail Sale?
**Check definitional exclusions FIRST - these mean no tax is due at all:**

| If the transaction is... | It's NOT a retail sale because... | Citation |
|--------------------------|-----------------------------------|----------|
| Custom software development | Explicitly excluded | RCW 82.04.050(6)(a)(i)-(ii) |
| Professional services (human effort) | Service, not sale of TPP/digital | RCW 82.04.050(6)(a); 82.04.192(3)(b)(i) |
| Web hosting/storage | Explicitly excluded from DAS | RCW 82.04.192(3)(b)(xiv) |
| Data processing services | Explicitly excluded from DAS | RCW 82.04.192(3)(b)(xv) |
| Telecommunications services | Explicitly excluded from DAS | RCW 82.04.192(3)(b)(vi) |
| IT services/hosting (pre-Oct 2025) | Infrastructure, not DAS | WAC 458-20-15503 |

### Step 2: Does WA Have Jurisdiction?
Even if taxable, WA may not have the right to tax it:

| Transaction Type | Sourced To | WA Taxable If... |
|------------------|-----------|------------------|
| Tangible goods | Delivery location | Delivered TO WA |
| Services | Where performed | Performed IN WA |
| Construction | Job site | Job site IN WA |
| DAS/SaaS | Customer location | But MPU applies for multi-state use |

### Step 3: Comprehensive Exemption Scan (12 Key Exemptions)
Only after confirming it's (1) a retail sale and (2) WA-sourced, scan for exemptions.

**TIER 1: HIGH-VALUE EXEMPTIONS (Check Every Time)**

| # | Exemption | Citation | What to Look For |
|---|-----------|----------|------------------|
| 1 | **Multi-Point Use** | RCW 82.08.0208(4) / 82.12.0208(7) | Cloud/SaaS used by employees in multiple states |
| 2 | **Out-of-State Delivery** | RCW 82.08.0264 / 82.12.0264 | Ship-to address outside WA |
| 3 | **Custom Software** | RCW 82.04.050(6)(a)(i)-(ii) | Custom dev, CR numbers, project IDs |
| 4 | **Professional Services** | RCW 82.04.050(6)(a); 82.04.192(3)(b)(i) | Consulting, advisory, engineering |
| 5 | **Construction OOS** | WAC 458-20-170 | Tower sites, installation with Site ID outside WA |

**TIER 2: DAS EXCLUSIONS (Often Overlooked!)**

| # | Exclusion | Citation | What to Look For |
|---|-----------|----------|------------------|
| 6 | **Storage/Hosting** | RCW 82.04.192(3)(b)(xiv) | AWS hosting, Azure storage, cloud backup - NOT SaaS apps |
| 7 | **Data Processing** | RCW 82.04.192(3)(b)(xv) | Batch processing, ETL, data transformation |
| 8 | **Telecom Services** | RCW 82.04.192(3)(b)(vi) | Telecommunications and ancillary services |

**TIER 3: T-MOBILE SPECIFIC OPPORTUNITIES**

| # | Exemption | Citation | What to Look For |
|---|-----------|----------|------------------|
| 9 | **Data Center** | RCW 82.08.986 / 82.12.986 | Servers, cooling, power equipment for qualifying data centers |
| 10 | **Resale** | RCW 82.08.0251 / 82.12.0251 | Phones, devices, accessories bought to sell to customers |
| 11 | **Interstate Commerce** | RCW 82.08.0261(1) | Equipment used in interstate/foreign commerce |

**TIER 4: CONFIRM NOT APPLICABLE**

| # | Exemption | Citation | Why T-Mobile Cannot Use |
|---|-----------|----------|------------------------|
| 12 | **M&E Exemption** | RCW 82.08.02565 | **EXCLUDED** - Telecom is public utility |

## Business Context Requirement

**Every AI_Reasoning MUST start with a CONTEXT line:**

Format: `CONTEXT: [What it is] [Why T-Mobile uses it]`

This brief 2-3 sentence explanation helps reviewers immediately understand what they're looking at.

**Examples:**

| Vendor | Product | CONTEXT Line |
|--------|---------|--------------|
| Redis Inc | Redis Enterprise | Redis Enterprise is an in-memory database for real-time data processing. T-Mobile uses it for network analytics and low-latency customer systems. |
| Snowflake | Cloud Data Platform | Snowflake is a cloud data warehouse. T-Mobile uses it to analyze customer usage patterns and network performance across millions of subscribers. |
| Ericsson | 5G Core Software | Ericsson provides 5G network core software (AMF, SMF, UPF). T-Mobile uses it to route voice/data for 100M+ subscribers nationwide. |
| Palo Alto Networks | Prisma Cloud | Prisma Cloud is a cloud security platform. T-Mobile uses it to secure their multi-cloud infrastructure and detect threats. |
| ServiceNow | ITSM Platform | ServiceNow is an IT service management platform. T-Mobile uses it to manage IT incidents, change requests, and asset tracking across their enterprise. |
| Splunk | Log Analytics | Splunk is a log analytics and security platform. T-Mobile uses it to monitor network events and detect security anomalies in real-time. |

**Why this matters:**
- Reviewers immediately understand what they're looking at
- Business context often informs the tax treatment (MPU for nationwide tools, OOS for site-specific work)
- Creates institutional knowledge about T-Mobile's vendor ecosystem

### Step 4: Creative Thinking Prompts
For each transaction, ask:
- "What's unique about this purchase that might affect taxability?"
- "How does T-Mobile use this - could that change the analysis?"
- "Is this part of a larger transaction that should be analyzed differently?"
- "Could this qualify for an exemption I haven't considered?"

### Step 5: Confidence & Counter-Argument
Before finalizing:
- "How strong is this argument on a scale of 1-10?"
- "What would DOR likely argue in response?"
- "What documentation would be needed to support this claim?"

## Deep Product Characterization (CRITICAL)

**The most important step is understanding WHAT was actually purchased.** Invoice descriptions are often cryptic - you must decode them.

### Examples of Proper Characterization

| Invoice Says | Actually Is | Tax Treatment |
|--------------|-------------|---------------|
| "Key injection services" | **SERVICE** - Programming/configuring encryption keys into hardware | Not a retail sale (service, not TPP) |
| "Amazon web hosting" | **IT/Hosting Service** | Pre-Oct 2025: NOT taxable as retail sale |
| "CR f21802-01 lab exit" | **Custom Software Development** | Excluded from retail sale per RCW 82.04.050(6)(a) |
| "Advanced Exchange Warranty" | **Warranty/Service Contract** | Sourced to where equipment is located |
| "MantaRay SON" | **Network optimization SaaS** | DAS - taxable but MPU applies |
| "BSF" (Nokia) | **5G core network software** | DAS - taxable but MPU applies |
| "AMF" (5G term) | **Access and Mobility Management Function** - 5G core software | DAS - taxable but MPU applies |

### Pre-ESSB 5814 Key Distinctions

**These transactions occurred in 2023-2024. Apply the law in effect at that time:**

| Category | Pre-Oct 2025 Treatment | Why |
|----------|----------------------|-----|
| **IT Services / Hosting** | NOT taxable as retail sales | Not "digital automated services" - primarily infrastructure/hosting |
| **Custom Software Development** | NOT taxable - excluded from retail sale | RCW 82.04.050(6)(a)(i)-(ii) explicitly excludes |
| **Digital Automated Services (DAS/SaaS)** | TAXABLE in WA | But MPU applies - apportion to WA usage |
| **Professional Services / Consulting** | NOT taxable | Human effort exclusion - not automation |

### How to Decode Cryptic Descriptions

1. **Web search the vendor** to understand what they sell
2. **Web search the specific product name** (e.g., "Nokia MantaRay SON")
3. **Consider T-Mobile context** - they're a telecom, so:
   - Network equipment vendors (Ericsson, Nokia) → RAN software, 5G core
   - IT services → enterprise software, hosting, DevOps
   - Tower companies → construction/installation services
4. **Decode telecom jargon**:
   - AMF, SMF, UPF = 5G core network functions (software)
   - RAN = Radio Access Network
   - SON = Self-Organizing Network (software)
   - IMS = IP Multimedia Subsystem (VoIP software)

### Stick to Clear Arguments

**Strong arguments (use these):**
- Custom software development → excluded from retail sale definition
- IT services/hosting → not a retail sale (pre-ESSB 5814)
- Out-of-state delivery → RCW 82.08.0264 / 82.12.0264
- Out-of-state services → sourced to where performed (WAC 458-20-170, WAC 458-20-193)
- Multi-Point Use → RCW 82.08.0208(4) / 82.12.0208(7) for DAS used nationwide

**Weak arguments (avoid or use carefully):**
- "Software maintenance is not taxable" → Too broad, depends on what's actually being done
- "Professional services" for software implementation → May be challenged if deliverable is software
- Stretching M&E exemption → T-Mobile is excluded as public utility

### Services Sourcing Rules

**Services are generally sourced to WHERE PERFORMED, not where the recipient is:**

- **WAC 458-20-170** - Construction services sourced to job site
- **WAC 458-20-193** - Services of persons sourced to where performed

**Example:**
- Colorado-based company provides remote IT support to T-Mobile
- Service is PERFORMED in Colorado (where the staff is)
- Not subject to WA tax regardless of T-Mobile being in WA

### Vendor Type Triggers

| When I See... | I Should Think About... |
|---------------|------------------------|
| Cloud/SaaS vendor (Azure, AWS, Salesforce) | Multi-point use allocation - T-Mobile has nationwide employees |
| Construction/tower company | Job site location - is it outside WA? Check Site ID or address |
| "Consulting", "advisory", "engineering" | Professional services exclusion - human effort, not automated |
| Equipment shipped somewhere | Delivery address - OOS if outside WA |
| Software purchase | Custom vs prewritten? SaaS vs perpetual? MPU opportunity? |
| Installation services | Real property (OOS sourcing) vs TPP installation? |

### Opportunistic Data Use

**Site ID available?** → Use it to verify location AND check tax rate
**Ship-to address visible?** → Check if outside WA for OOS
**Invoice description unclear?** → Web search the vendor
**Rate seems wrong?** → Compare to expected rate for location

### Invoice Address Extraction (CRITICAL - Don't Confuse These!)

**Invoices have THREE different addresses - only ONE matters for tax sourcing:**

| Address Label | What It Is | Use for OOS? |
|---------------|-----------|--------------|
| **Remit To** / **Vendor Address** | Where vendor is located | ❌ NO - Ignore |
| **Bill To** | Where invoice is sent (T-Mobile PO Box) | ❌ NO - Ignore |
| **Ship To** / **Deliver To** | Where goods/services go | ✅ YES - This determines OOS |

**Common Mistakes to Avoid:**
- ❌ "Vendor is in Texas, so this is out-of-state" → WRONG (vendor location doesn't matter)
- ❌ "Bill To shows Portland OR" → WRONG (billing address doesn't matter)
- ✅ "Ship To shows E533 - Knoxville Market (Tennessee)" → CORRECT (delivery location matters)

**Example - Reading a Nokia Invoice Correctly:**
```
Remit To: NOKIA SOLUTIONS AND NETWORKS US LLC
          1950 N STEMMONS FWY STE 5010
          DALLAS TX 75207              ← IGNORE - This is just vendor's address

Bill To:  T-Mobile Bill To Address
          PO Box 3245
          PORTLAND OR 97208            ← IGNORE - This is just where bill goes

Ship To:  E533 - Knoxville Market
          6609 Gem Apparel Lane        ← USE THIS - Delivery is in Tennessee = OOS
```

**For Services:** If no Ship To address, the service is sourced to where PERFORMED (WAC 458-20-193), which may require checking the contract or Site ID.

## Analysis Process

### Step 1: Load and Filter Data
```python
# Read source file
df = pd.read_excel(source_file, sheet_name=sheet_name)

# Apply standard filters
filtered = apply_standard_filters(df, tax_type)

# Apply user filters
filtered = apply_user_filters(filtered, user_request)
```

### Step 1.5: Use Input Description Columns as Hints (Not Conclusions)

**Sales Tax 2024** - Review these columns for initial context:
- `txz01_po_description` - PO line item description (often vague: "PROFESSIONAL SERVICES", "EQUIPMENT")
- `matk1_po_material_group_desc` - Material group category (SOFTWARE, HARDWARE, etc.)

These provide starting hints but are often generic. Use them to guide where to look, but **never conclude based solely on these columns**.

**Use Tax (2023 & 2024)** - The `Description` column may have useful info. The `Tower vendor invoice description` column is mostly empty - don't rely on it.

**Example:** PO description says "MAINTENANCE" but the invoice could reveal:
- Software maintenance → potential MPU opportunity
- Tower site maintenance in Oregon → OOS
- Consulting services → professional services exclusion

Always verify with invoice and vendor research.

### Step 1.6: Tax Amount Validation (CRITICAL)

**Before determining any row is OVERPAID, check the actual tax charged:**

```python
# CRITICAL CHECK - Must validate tax was actually charged
tax_amount = row['hwste_tax_amount_lc']

if tax_amount == 0 or pd.isna(tax_amount):
    # NO TAX WAS CHARGED - Cannot be OVERPAID
    decision = 'NO_TAX_CHARGED'
    estimated_refund = 0
    reasoning = "No tax was charged on this line item - nothing to refund"
```

**Why this matters:**
- Many invoices have multiple line items
- Some line items are taxed, others are not (vendor may have already applied exemptions)
- A row with $0 tax CANNOT be "OVERPAID" - there's nothing to refund
- Must check `hwste_tax_amount_lc` column before making refund determination

**Example - Ookla Invoice:**
```
Invoice has 11 line items:
  - CoverageRight North America    $146,397  tax: $0.00      → NO_TAX_CHARGED
  - Mobile Consumer Speedtest      $221,000  tax: $65,973.90 → Check for MPU (OVERPAID)
  - Downdetector Pro Services       $42,750  tax: $0.00      → NO_TAX_CHARGED
  - Cell Analytics Portal          $156,000  tax: $0.00      → NO_TAX_CHARGED
  ...
```

Only the Speedtest line has tax charged - only that row can potentially be OVERPAID.

### Handling Multi-Row Invoices (Critical)

**Many invoices have multiple Excel rows** - same document/INVNO but different line items:
- Sales Tax: ~8,000 documents have multiple rows (up to 119 rows per document)
- Use Tax: ~4,200 invoices have multiple rows (up to 2,000+ rows per INVNO)

**When you see multiple rows with the same invoice number:**

1. **Read the FULL invoice PDF** - extract ALL line items with their amounts
2. **Match each Excel row to its invoice line by amount** (tax base or tax amount)
3. **Check tax amount on each row** - $0 tax = NO_TAX_CHARGED, not OVERPAID
4. **Analyze each line item specifically** - don't apply blanket analysis to all rows

**Matching strategy:**
- Primary match: `hwbas_tax_base_lc` (tax base) to invoice line item amount
- Secondary match: `hwste_tax_amount_lc` (tax amount) to invoice tax column
- Tertiary match: Description if amounts are identical across multiple lines
- If no clear match: Note in AI_Reasoning which line item appears to correspond

**Example:**
```
Invoice PDF shows:
  Line 1: Software License    $139,080  (tax: $14,186)
  Line 2: Support Services    $355,740  (tax: $0)      ← No tax charged!
  Line 3: Training             $960     (tax: $97)

Excel rows for same doc:
  Row A: tax_base=$139,080, tax=$14,186 → Line 1 (Software - check MPU) → OVERPAID
  Row B: tax_base=$355,740, tax=$0      → Line 2 (No tax charged) → NO_TAX_CHARGED
  Row C: tax_base=$960, tax=$97         → Line 3 (Training - taxable) → CORRECT
```

**Each row gets its own analysis** - don't copy/paste the same reasoning for all rows of the same invoice.

### Vendor Mismatch Detection (IMPORTANT)

**Always read BOTH invoices** when Inv 1 and Inv 2 are present, then check for mismatches:

| Check | What to Compare | Flag If... |
|-------|-----------------|------------|
| **Excel vs Invoice** | Vendor name in Excel row vs vendor on invoice PDF | Names don't match (allowing for abbreviations) |
| **Inv 1 vs Inv 2** | Vendor on first invoice vs vendor on second invoice | Different vendors on the two invoices |
| **Invoice vs PO** | Vendor on invoice vs what you'd expect for this PO | Completely unrelated vendor |

**How to Flag:**

Set `Vendor_Mismatch` column to:
- `""` (empty) - No mismatch, vendor matches
- `"YES - Invoice shows [X] but Excel shows [Y]"` - Mismatch with explanation
- `"YES - Inv 1 is [X] but Inv 2 is [Y]"` - Two invoices have different vendors
- `"WRONG INVOICE ATTACHED"` - Invoice is clearly for a different transaction

**Smart Matching - These are the SAME vendor (NOT a mismatch):**

| Excel Shows | Invoice Shows | Why It's the Same |
|-------------|---------------|-------------------|
| NOKIA SOLUTIONS AND NETWORKS US LLC | Nokia | Full legal name vs common name |
| MICROSOFT CORPORATION | Microsoft Azure | Parent company vs product/division |
| INTERNATIONAL BUSINESS MACHINES | IBM | Full name vs acronym |
| AMAZON WEB SERVICES INC | AWS | Full name vs acronym |
| CISCO SYSTEMS INC | Cisco | Full legal name vs short name |
| ERICSSON INC | Ericsson AB | US entity vs parent entity |
| ORACLE AMERICA INC | Oracle Corporation | Subsidiary vs parent |
| CDW CORPORATION | CDW Direct LLC | Parent vs subsidiary |
| MOREDIRECT INC | Connection Enterprise | Acquired company (now same) |

**These ARE actual mismatches (FLAG THEM):**

| Excel Shows | Invoice Shows | Why It's a Mismatch |
|-------------|---------------|---------------------|
| Nokia | Ericsson | Completely different companies |
| Microsoft | Salesforce | Different vendors |
| AWS | Google Cloud | Competing cloud providers |
| Cisco | Juniper Networks | Different network vendors |
| Any vendor | Invoice for different PO# | Wrong invoice attached |

**Handling Resellers/Distributors:**

Sometimes invoices come through resellers:
| Excel Shows | Invoice Shows | Action |
|-------------|---------------|--------|
| CDW Corporation | Dell (product manufacturer) | Check if CDW is reselling Dell equipment - may be OK |
| Zones Inc | HP Inc (on invoice letterhead) | Zones resells HP products - verify PO matches |
| SHI International | Microsoft (software) | SHI is a Microsoft reseller - likely OK |

If a reseller is involved, note in AI_Reasoning: "Invoice is from [manufacturer] via reseller [reseller name] - matches expected transaction"

**In AI_Reasoning, note:**
- "Read both Inv 1 and Inv 2 - both are from Nokia, match confirmed"
- "WARNING: Inv 2 appears to be for a different vendor (Cisco) - flagging mismatch"

### Site ID Recognition and Matching (IMPORTANT)

**Site IDs appear on invoices for tower/construction work.** Matching them correctly is critical for determining if work is out-of-state (OOS).

**What Real Site IDs Look Like (from actual T-Mobile data):**

| Pattern | Examples | Description |
|---------|----------|-------------|
| **2-letter market + digits** | SE01403, SP01545, BL20511 | Seattle, Spokane, Bellevue markets |
| **2-letter + digits + suffix** | SE05398A, SE0103WA, BL20511W | Base site with sector suffix |
| **3-letter market + digits** | CHI9417A, NYC01747, DEN0523 | Chicago, New York, Denver |
| **Complex format with XC** | RPO03XC031, RSE98XC129, RNA59XC001 | Special site types |
| **Digit prefix + market** | 9ME080A, 2YK4765A, 7WDC016A | Numbered region + market code |

**Common Market Codes:**
- **WA markets:** SE (Seattle), SP (Spokane), BL (Bellevue), SEI (Seattle alt)
- **Other states:** CHI (Chicago), NY/NYC (New York), DEN (Denver), SA (San Antonio), PHX (Phoenix)

**Smart Matching Rules - These ARE the Same Site:**

| Invoice Shows | Workbook Shows | Why They Match |
|---------------|----------------|----------------|
| SE0523 | SE0523A | Base site matches, suffix is just sector indicator |
| SE01403 | SE01403W | Same base, different suffix (A, B, W = sectors) |
| CHI9417 | CHI9417A | Base without suffix matches base with suffix |
| BL20511 | BL20511W | Same site, 'W' suffix indicates a sector variant |

**The "Ring" column in the Site ID workbook shows the BASE Site ID without suffix - use this for matching.**

**What is NOT a Site ID (Don't False-Match These):**

| Text | Why It's NOT a Site ID |
|------|------------------------|
| E533 | Too short, doesn't follow market code pattern |
| 12345 | Just numbers, no market prefix |
| INV-2024-001 | Invoice number format |
| PO4900123456 | Purchase order format |
| 123 Main Street | Address, not Site ID |
| Project #445 | Project reference, not Site ID |
| CR f21802-01 | Change Request number |

**Site ID Pattern Test (Apply This Logic):**
```
Does it start with 2-3 letters that could be a market code? (SE, SP, CHI, NY, etc.)
  └─ NO → Probably not a Site ID
  └─ YES → Does it have 3-5 digits after the letters?
           └─ NO → Probably not a Site ID
           └─ YES → Does it optionally end with 1-2 letters (A, B, W, WA)?
                    └─ This looks like a valid Site ID pattern
```

**How to Use Site IDs for Tax Analysis:**

1. **Extract Site ID from invoice** - Look for patterns like "Site: SE05398A" or "Location: CHI9417"
2. **Look up in Site ID workbook** - Check `~/Desktop/Files/Site IDs/wa_sites_with_rates.xlsx`
3. **Try fuzzy match if exact match fails:**
   - Strip suffix (SE05398A → SE05398) and search again
   - Check the "Ring" column which has base IDs
4. **Determine state from lookup:**
   - If found in WA sites file → Washington site → WA tax applies
   - If market code suggests other state (CHI, NY) → Look up that state → Likely OOS
5. **Flag in `Site_ID` column and `Location_Mismatch` if applicable**

**Example - Site ID Detection in Reasoning:**
```
Invoice shows "Site: SE05398A - Tower Modification"

Checking Site ID pattern:
- Starts with "SE" (Seattle market code) ✓
- Has 5 digits after market code ✓
- Ends with letter suffix "A" ✓
- This matches the Site ID pattern

Looking up SE05398A in the Site ID workbook...
- Found match: SE05398A, Seattle WA, King County
- This is a Washington site, so WA tax jurisdiction applies

Since the work was performed at a WA site, construction sourcing (WAC 458-20-170)
means WA tax is correct. No OOS refund opportunity.
```

**Example - OOS Site Detection:**
```
Invoice shows "Site: CHI9417A - Equipment Installation"

Checking Site ID pattern:
- Starts with "CHI" (Chicago market code) ✓
- Has 4 digits after market code ✓
- Ends with suffix "A" ✓
- This matches the Site ID pattern

Market code "CHI" indicates Chicago, Illinois - not Washington.
Construction services are sourced to job site location (WAC 458-20-170).
Work performed in Illinois is not subject to WA sales tax.

Decision: OUT OF STATE - refund eligible
```

### Location Confidence Analysis (For Sales Tax 2024)

**The `quadrant` column is often WRONG.** ~5,000+ rows have conflicts between the quadrant and other signals. Use this process to determine WHERE tax was actually collected.

#### Step 1: Collect All Location Signals

For each row, note:
- `quadrant` value ("Yes Tax, In WA" or "Yes Tax, NOT in WA")
- `sales_tax_state` value
- `tax_jurisdiction_state` value
- `rate` value
- Invoice Ship-To address (from PDF)
- Site ID (if present)

#### Step 2: Validate Rate Against WA Table

**WA combined rates range from 7.50% to 10.60%**

| Rate | Interpretation |
|------|----------------|
| < 6.5% | **DEFINITELY NOT WA** - Below WA state minimum |
| 6.0%, 7.0% exactly | **STRONG indicator NOT WA** - These don't exist in WA |
| 7.5% - 10.6% | **POSSIBLE WA** - Need to verify with other signals |
| 10.0% exactly | **STRONG indicator NOT WA** - 10.0% doesn't exist in WA |
| > 10.6% | **LIKELY NOT WA** - Above WA max rate |

#### Step 3: Check for Conflicts

**Flag a LOCATION CONFLICT if ANY of these are true:**
1. Quadrant says "In WA" but `tax_jurisdiction_state` ≠ "WA"
2. Quadrant says "In WA" but rate < 7.5% or > 10.6%
3. `sales_tax_state` ≠ `tax_jurisdiction_state`
4. Invoice Ship-To shows non-WA address
5. Site ID resolves to non-WA state

**Known conflict patterns in the data:**
- **Type 1 (2,541 rows):** Quadrant = "In WA" but jurisdiction ≠ WA
- **Type 3 (3,204 rows):** Rate ~2.5% for "In WA" transactions (e.g., GENERAL DATATECH)
- **Type 4 (1,000+ rows):** sales_tax_state ≠ tax_jurisdiction_state

#### Step 4: Web Search to Verify Suspected State

**When signals conflict, web search to verify the suspected state's rates:**

```
Example:
- Quadrant: "In WA"
- tax_jurisdiction_state: KS
- Rate: 9.21%

Web search: "Kansas sales tax rate range"

Finding: Kansas state rate is 6.5%, combined rates range 6.5% to ~11.5%.
9.21% IS a valid Kansas rate (e.g., Overland Park area).

Conclusion: Tax was likely charged in Kansas, not Washington.
```

**What to search:**
- "[State] sales tax rate range"
- "[State] combined sales tax rates"
- "Does [State] have [X]% sales tax"

#### Step 5: Read Invoice for Ground Truth

**The invoice Ship-To address is the ground truth.** It tells you where goods/services were delivered.

After reading the invoice, you can determine which scenario applies.

#### Step 6: Determine Scenario & Final Decision

| Scenario | Tax Charged In | Delivery To | Implication | Final_Decision |
|----------|---------------|-------------|-------------|----------------|
| A | Kansas | Kansas | Correct - not a WA issue | `CORRECT` |
| B | Kansas | Washington | Complex - vendor error or use tax credit | `REVIEW` |
| C | Washington | Kansas | WA tax on OOS delivery - refund | `OUT OF STATE` |
| D | Unknown | Unknown | Insufficient data | `REVIEW` |

#### Step 7: Output Location Analysis Columns

| Column | What to Write |
|--------|---------------|
| `Location_Signals` | "Quadrant: In WA; Jurisdiction: KS; Rate: 9.21%; Ship-To: Kansas City, KS" |
| `Location_Confidence` | "HIGH for KS - invoice confirms" or "LOW - conflicting signals" |
| `Likely_Tax_State` | "KS" (your best determination) |
| `Location_Conflict_Type` | "TYPE_1: Quadrant vs jurisdiction mismatch" |

#### AI_Reasoning Template for Location Conflicts

```
LOCATION CONFLICT DETECTED:

Excel signals:
- Quadrant: "Yes Tax, In WA"
- sales_tax_state: WA
- tax_jurisdiction_state: KS  ← CONFLICT
- Rate: 9.21%

STEP 1 - Rate Analysis:
9.21% could exist in WA (some King County locations are ~9.2%).
Rate alone is AMBIGUOUS.

STEP 2 - Web Search for Kansas:
Searched: "Kansas sales tax rates"
Result: Kansas combined rates range 6.5% to ~11.5%.
Overland Park, KS has combined rate of ~9.2%.
Source: https://www.avalara.com/taxrates/en/state-rates/kansas.html

9.21% IS a valid Kansas rate.

STEP 3 - Invoice Verification:
Reading invoice PDF...
Ship-To: "1234 Main St, Overland Park, KS 66210"

CONCLUSION:
Tax was charged in KANSAS, not Washington.
- Invoice Ship-To confirms KS
- tax_jurisdiction_state = KS
- Rate matches Kansas (verified via web search)
- Quadrant column was INCORRECT

Location_Confidence: HIGH for Kansas
Likely_Tax_State: KS
Location_Conflict_Type: TYPE_1

TAX IMPLICATION:
This was Kansas sales tax, correctly charged for a Kansas delivery.
WA has no jurisdiction over this transaction.

Final_Decision: CORRECT
Explanation: Kansas tax correctly charged on Kansas delivery. Not a WA refund opportunity.
```

### Step 2: For EACH Row, Perform Deep Contextual Analysis

**DO NOT BE LAZY - Full research is required:**

1. **Read the invoice PDF** from ~/Desktop/Invoices/
2. **Understand the vendor** - Web search if cryptic or unfamiliar
3. **Identify what's being sold** - Product? Service? Digital? Installation?
4. **Think contextually** - What exemptions/issues could apply to THIS specific transaction?
5. **Check opportunistic data** - Site ID? Ship-to address? Rate verification?
6. **Apply proper tax treatment** with specific citations

### Step 3: Contextual Tax Treatment Decision Tree

**When analyzing, think through this based on what you observe:**

```
Is this a CLOUD/SAAS service?
  └─ Yes → Consider Multi-Point Use (MPU)
     └─ T-Mobile has nationwide employees
     └─ Citation: RCW 82.08.0208(4) / 82.12.0208(7); WAC 458-20-15502
     └─ Recovery: 70-95% if mostly out-of-state users

Is this PROFESSIONAL SERVICES / CONSULTING?
  └─ Yes → Consider Human Effort Exclusion
     └─ Test: Is it primarily human expertise, not automation?
     └─ Citation: RCW 82.04.050(6)(a); RCW 82.04.192(3)(b)(i)
     └─ Recovery: 100% - not taxable

Is this CONSTRUCTION / TOWER WORK / INSTALLATION?
  └─ Yes → Check job site location
     └─ If outside WA → OOS - not WA taxable
     └─ Citation: WAC 458-20-170
     └─ Use Site ID to verify location if available

Is there a SHIP-TO ADDRESS outside WA?
  └─ Yes → Out-of-State Delivery
     └─ Citation: RCW 82.08.0264 / 82.12.0264
     └─ Recovery: 100%

Is there a SITE ID?
  └─ Yes → Look up correct rate, verify tax rate charged is correct
     └─ If wrong rate → Rate correction opportunity

Is this EQUIPMENT that could be M&E?
  └─ STOP - T-Mobile CANNOT claim M&E exemption
     └─ Telecom companies are public utilities, excluded by statute

Is this for RESALE to customers?
  └─ Yes → Resale exemption
     └─ Citation: RCW 82.08.0251 / 82.12.0251
```

### Step 4: Write AI_Reasoning (Show Your Thinking)

**The AI_Reasoning must show the THINKING PROCESS, not just conclusions.** Write it like you're explaining your detective work - how you figured out what this cryptic invoice line actually is.

**Good example (Nokia invoice with "CR f21802-01 lab exit"):**
```
Looking at this Nokia invoice, I see the line item "CR f21802-01 lab exit" which is pretty cryptic.

Let me break this down:
- Nokia is a major 5G network equipment and software provider for T-Mobile
- "CR" in telecom/software context typically means "Change Request" - a request for new development
- "f21802-01" looks like an internal project/feature ID
- "lab exit" is a software development term meaning the code has passed testing and is ready for production

So this appears to be custom software development work - Nokia developed a specific feature (CR f21802-01) for T-Mobile and this is the billing for that development work exiting the lab phase.

Custom software development is explicitly excluded from the retail sale definition under RCW 82.04.050(6)(a)(i)-(ii). This covers software "developed for a particular purchaser" - which this clearly is (a specific CR number for T-Mobile).

This means the tax charged here shouldn't have been charged at all - it's not a retail sale.
Decision: OVERPAID - 100% refund eligible
```

**Good example (Kiosk invoice with "Key injection services"):**
```
Looking at this Kiosk Information Systems invoice for "Key injection services" plus freight...

First, what is "key injection"? This is a security/cryptographic term. When you have payment terminals or kiosks that process card transactions, each device needs unique encryption keys programmed into it. "Key injection" is the SERVICE of securely loading these keys into the hardware.

Even though there's freight on the invoice (suggesting something physical shipped), the key injection itself is a SERVICE - it's the act of programming/configuring the devices with security credentials. The freight is probably for shipping devices back after the keys were injected.

Since key injection is a service (human effort configuring equipment), not a sale of tangible personal property, it's not subject to retail sales tax under the human effort exclusion.

Additionally, if Kiosk's facility is in Colorado and that's where the work is performed, the service would be sourced to Colorado per WAC 458-20-193 anyway.

Decision: OVERPAID - this is a service, not TPP
```

**Bad example (don't do this):**
```
Vendor: Nokia - Network equipment company
Product: CR f21802-01 lab exit
Classification: Software
Decision: OVERPAID
Citation: RCW 82.04.050(6)(a)
```

## MANDATORY: ROW ANALYSIS FORM (Fill Before Writing Output)

**STOP. For EACH row, fill in this form FIRST. Do not write AI_Reasoning until every field is filled.**

```
┌─────────────────────────────────────────────────────────────────┐
│                    ROW ANALYSIS FORM                            │
├─────────────────────────────────────────────────────────────────┤
│ 1. INVOICE VERIFICATION (Read the PDF first)                    │
│    Invoice #: _______________ (from PDF, not filename)          │
│    Invoice Date: _______________                                │
│    PDF Filename: _______________                                │
│                                                                 │
│ 2. DELIVERY LOCATION (Extract from invoice)                     │
│    Ship-To Address: _______________                             │
│    City, State, Zip: _______________                            │
│                                                                 │
│ 3. LINE ITEM MATCHING                                           │
│    Excel Description: [from txz01_po_description]               │
│    Excel Amount: $_______________                               │
│    Matched Invoice Line #: _______________                      │
│    Invoice Line Text: _______________                           │
│    Amount Match: □ Yes  □ No → explain: _______________         │
│                                                                 │
│ 4. VENDOR RESEARCH (WebSearch required if unfamiliar)           │
│    What does this vendor do? _______________                    │
│    Business model (products/services): _______________          │
│    Company size/location: _______________                       │
│    Research URL: _______________                                │
│                                                                 │
│ 5. PRODUCT/SERVICE ANALYSIS                                     │
│    What is T-Mobile actually buying? _______________            │
│    How does this product/service work? _______________          │
│    Category: □ Physical goods □ Software □ Human labor □ Constr │
│    How determined: □ Invoice clear □ Web search □ Vendor known  │
│                                                                 │
│ 6. WHY IS THIS TAXABLE OR NOT? (Explain reasoning)              │
│    Is this a "retail sale" under WA law? □ Yes □ No             │
│    Why or why not? _______________                              │
│    If exempt, what category? _______________                    │
│                                                                 │
│ 7. TAX DETERMINATION                                            │
│    Product Type: □ DAS □ TPP □ Service □ Construction □ Custom  │
│    Applicable Exemption: _______________                        │
│    Citation: _______________ (must be in target_rcws.txt)       │
│                                                                 │
│ 8. DECISION                                                     │
│    Final Decision: □ REFUND  □ NO REFUND  □ REVIEW              │
│    If REVIEW, what needs checking: _______________              │
│    Confidence: ___ (0.0-1.0)                                    │
│    Estimated Refund: $_______________                           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ □ ALL FIELDS FILLED → Now write AI_Reasoning from this form     │
└─────────────────────────────────────────────────────────────────┘
```

**Why this form exists:** Rules in CLAUDE.md get forgotten during work. This form embeds the rules INTO the work. You can't skip fields - blanks mean incomplete analysis.

**After filling the form, convert to AI_Reasoning:**
```
INVOICE VERIFIED: Invoice #[number] dated [date]
SHIP-TO: [full address]
MATCHED LINE ITEM: [text] @ $[amount]
---

VENDOR RESEARCH (from web search):
[2-4 sentences: What does this company do? Business model? Size/location?]
Source: [URL]

PRODUCT/SERVICE ANALYSIS:
[2-4 sentences: What is T-Mobile buying? How does it work?]

WHY THIS IS/ISN'T TAXABLE:
[2-4 sentences: Is this a retail sale? Why/why not? What exemption applies?]

TAX ANALYSIS:
- Product Type: [type]
- Exemption Basis: [basis]
- Citation: [RCW/WAC]

DECISION: [decision]
ESTIMATED REFUND: $[amount]

[ENFORCED_PROCESS|timestamp|v1]
```

## Citation Rules

**Two types of citations required:**

### 1. Tax Law Citations
**RCWs**: ONLY use RCWs from `knowledge_base/target_rcws.txt` (364 from Summary of Impacts 2024)
**WACs**: Can use any relevant WAC (e.g., WAC 458-20-15502, WAC 458-20-170)
**ETAs**: Can reference ETAs for DOR guidance (e.g., ETA 3100, ETA 3201)

### 2. Research Sources (Web Links)
When you web search to understand a product/service, **include the source URL** in your analysis:
- Vendor website explaining their product
- Technical documentation defining industry terms
- News articles about what the company does

**Example Citation_Source field:**
```
Tax: RCW 82.08.0208(4); WAC 458-20-15502
Research: https://www.nokia.com/networks/core-networks/cloud-native-core/ (BSF is 5G core software)
```

This shows your work - both WHY the tax treatment applies AND how you understood what the product is.

| Scenario | Citation | Notes |
|----------|----------|-------|
| Out-of-state delivery | RCW 82.08.0264 / 82.12.0264 | Check ship-to address |
| Multi-point use | RCW 82.08.0208(4) / 82.12.0208(7); WAC 458-20-15502 | SaaS, cloud services |
| M&E exemption | RCW 82.08.02565 / 82.12.02565 | **EXCLUDES TELECOM** |
| Professional services | RCW 82.04.050(6)(a); RCW 82.04.192(3)(b)(i) | Human effort exclusion |
| Custom software | RCW 82.04.050(6)(a)(i)-(ii) | Definition exclusion |
| Resale | RCW 82.08.0251 / 82.12.0251 | Reseller certificate |
| Real property installation | WAC 458-20-170 | Sourced to job site location |
| Digital automated services | RCW 82.04.192; WAC 458-20-15502 | Check for MPU/exclusions |

**CRITICAL: T-Mobile and telecom companies CANNOT claim M&E exemption (public utility exclusion)**

## Output Requirements

### Column Order
Follow the column order specified in CLAUDE.md for each tax type.

### Invoice Hyperlinks
```
=HYPERLINK("http://localhost:8888/filename.pdf","filename.pdf")
```

### Validation (BEFORE Writing to Excel)

**CRITICAL**: Validate all analysis rows BEFORE writing to Excel:
```python
from scripts.validate_analysis import validate_row, validate_dataframe

# For each row:
is_valid, errors = validate_row(row_dict)
if not is_valid:
    print(f"Row failed validation: {errors}")
    # Fix the errors before proceeding

# For DataFrame:
all_valid, error_dict = validate_dataframe(df)
if not all_valid:
    print(f"Validation failed for {len(error_dict)} rows")
    # Address all errors before writing
```

**Validation checks:**
- `INVOICE VERIFIED:` header present with invoice # and date
- `SHIP-TO:` header present with full address
- `MATCHED LINE ITEM:` header present with line item match
- Citation valid against `knowledge_base/target_rcws.txt`
- REVIEW decisions have research evidence
- Confidence score in 0.0-1.0 range

### Excel Formatting (Apply After Analysis)

After writing output to Excel, apply formatting using:
```bash
python3 scripts/format_excel_output.py "/path/to/output.xlsx"
```

**Header Formatting (color-coded by section):**
| Column Group | Background | Font |
|--------------|------------|------|
| Input Data (cols 1-13) | Light Blue (#B4C6E7) | White, Bold |
| AI Analysis (cols 14-29) | Light Green (#C6EFCE) | Black, Bold |
| Human Review (cols 30-36) | Light Yellow (#FFEB9C) | Black, Bold |

**Number Formatting:**
| Column | Format | Example |
|--------|--------|---------|
| `hwbas_tax_base_lc` | Commas, 2 decimals | 225,000.00 |
| `hwste_tax_amount_lc` | Commas, 2 decimals | 18,900.00 |
| `rate` | Percentage | 8.4% |
| `Estimated_Refund` | Commas, 2 decimals | 17,010.00 |

**Row Highlighting by Decision:**
- `OVERPAID` → Light green background
- `REVIEW` → Light yellow background
- `NO_TAX_CHARGED` → Light gray background

### Final_Decision Values
- `CORRECT` - Tax correctly charged
- `OVERPAID` - Refund eligible (rate too high or exempt) - **ONLY if tax > $0**
- `UNDERPAID` - Additional tax owed
- `OUT OF STATE` - Not WA taxable
- `NO_TAX_CHARGED` - Row has $0 tax - nothing to refund (vendor may have already applied exemption)
- `REVIEW` - Only if research was done and specific guidance provided

**CRITICAL**: A row can only be `OVERPAID` if `hwste_tax_amount_lc > 0`. If tax = $0, use `NO_TAX_CHARGED`.

### For REVIEW Rows
Never leave empty guidance. Always include:
1. What research was done
2. What is unclear
3. Specific next steps to resolve
4. Sources consulted

Example:
```
"Web search shows [vendor] is a construction contractor. Invoice shows 'site prep services' at [address].
Could be: (1) Real property installation → OOS if site outside WA per WAC 458-20-170,
or (2) TPP installation → taxable at point of sale.
Need: Verify if equipment becomes permanent fixture. Check work order for installation type."
```

## Web Search Guidance

**When to search:**
- Cryptic vendor names you don't recognize
- Unclear product/service descriptions
- Industry jargon you need to understand
- Need to understand vendor's business model

**What to find:**
- What does this vendor sell/do?
- Are they hardware, software, or services?
- Are they a consulting firm or product company?
- Where are they headquartered?

## Reference Files

- **Tax rules**: `knowledge_base/states/washington/tax_rules.json` (comprehensive scenarios)
- **Valid RCWs**: `knowledge_base/target_rcws.txt` (364 citations)
- **Site rates**: `data/wa_rates/Q424_Excel_LSU-rates.xlsx`
- **Site master**: Use Site ID to look up location
- **Invoices**: `~/Desktop/Invoices/`
- **WACs**: `knowledge_base/wa_tax_law/wac/title_458/` (read directly if needed)
- **ETAs**: `knowledge_base/states/washington/ETAs/` (read directly if needed)

## T-Mobile Specific Opportunities

### Data Center Exemption (RCW 82.08.986 / 82.12.986)

**When you see data center equipment purchases, consider this exemption:**
- Server hardware and storage arrays
- Cooling/HVAC equipment for data centers
- Power distribution units, backup generators
- Networking equipment (switches, routers in data centers)

**Requirements to qualify:**
- Facility must be 20,000+ sq ft dedicated to servers
- Must have power backup and fire suppression
- Must have physical security measures
- Must apply for exemption certificate with DOR

**Action:** When server/data center equipment appears, flag for data center exemption review. Note if T-Mobile has qualifying data centers.

### Resale Exemption (RCW 82.08.0251 / 82.12.0251)

**T-Mobile resells products to customers - these should be tax-exempt:**
- Mobile phones and smartphones
- Tablets and devices
- Accessories (cases, chargers, cables)
- IoT devices
- Home internet equipment (gateways, routers)
- SIM cards

**Test:** Was this item purchased FOR RESALE to T-Mobile customers? If yes, no tax should apply.

### Nationwide Network = MPU Opportunity

**T-Mobile's network infrastructure serves all 50 states:**
- Core network software (5G core, IMS, BSF, AMF, SMF)
- Operations support systems (OSS/BSS)
- Network management platforms
- Any cloud/SaaS software used to manage the nationwide network

**These are prime MPU candidates** - only the WA portion should be taxed. T-Mobile operates in every state, so WA usage is typically a small fraction.

### DAS Exclusions to Remember

**Many "cloud" purchases aren't DAS at all - they're EXCLUDED from the definition:**

| What It Looks Like | Why It's Excluded | Citation |
|-------------------|-------------------|----------|
| AWS hosting, Azure storage | Storage/hosting exclusion | RCW 82.04.192(3)(b)(xiv) |
| Data processing, ETL services | Data processing exclusion | RCW 82.04.192(3)(b)(xv) |
| Telecom/network services | Telecom exclusion | RCW 82.04.192(3)(b)(vi) |

**Key insight:** The vendor may have charged tax on "cloud services" that are actually EXCLUDED from DAS entirely.

## Example Analysis

```
User: "analyze B & C TOWER rows from Use Tax 2024 over $1000"

Claude:
1. Loads Use Tax Phase 3 2024 Oct 17.xlsx
2. Applies standard filters (INDICATOR=Remit, KOM Analysis empty)
3. Filters: vendor contains "B & C TOWER", tax amount > $1000
4. For each row:
   - Web searches "B & C Tower" → construction contractor, tower installation
   - Reads invoice PDF - sees "tower installation services at [site address]"
   - Thinks: Tower installation = real property installation per WAC 458-20-170
   - Checks Site ID if available → resolves to [state]
   - If outside WA: OOS - sourced to job site per WAC 458-20-170
   - Writes full AI_Reasoning with step-by-step analysis
5. Outputs to Phase_3_2024_Use Tax - Analyzed.xlsx with:
   - Invoice hyperlinks (localhost:8888)
   - Full AI_Reasoning for each row
   - Proper citations
   - Header formatting
```

## Quality Checklist

Before completing analysis, verify:

### First Principles Checks (NEW)
- [ ] **SKEPTICAL STARTING POINT**: Did you ask "should tax have been charged at all?"
- [ ] **DEFINITIONAL EXCLUSIONS CHECKED**: Before exemptions, checked if it's even a retail sale
- [ ] **DAS EXCLUSIONS CONSIDERED**: Did you check storage/hosting, data processing, telecom exclusions?
- [ ] **T-MOBILE OPPORTUNITIES SCANNED**: Data center? Resale? Interstate commerce?
- [ ] **JURISDICTION VERIFIED**: Does WA even have the right to tax this (sourcing)?

### Reasoning Quality (CRITICAL)
- [ ] **THINKING CHAIN SHOWN**: AI_Reasoning shows HOW you figured out what the product is, not just conclusions
- [ ] **ABBREVIATIONS DECODED**: Cryptic terms (CR, AMF, SON, etc.) are explained with reasoning
- [ ] **VENDOR CONTEXT USED**: Reasoning connects vendor's business to the line item interpretation
- [ ] **NO SHALLOW REASONING**: Reject reasoning like "Vendor: X, Product: Y, Decision: Z" - must show the deductive process

**Example of FAILING reasoning (don't do this):**
```
Vendor: Nokia - Network equipment
Product: BSF software
Classification: DAS
Decision: OVERPAID - MPU applies
```

**Example of PASSING reasoning:**
```
Looking at this Nokia invoice for "BSF"...
BSF stands for Binding Support Function - this is a 5G core network component that handles device authentication. Nokia is one of T-Mobile's primary 5G infrastructure vendors.
Since BSF is cloud-native software that runs across T-Mobile's nationwide network, it qualifies as Digital Automated Services. T-Mobile operates in all 50 states, so Multi-Point Use allocation applies...
```

### Data Validation
- [ ] **TAX AMOUNT CHECK**: No rows with $0 tax marked as OVERPAID (use NO_TAX_CHARGED instead)
- [ ] Multi-row invoices: each row matched to specific line item by amount
- [ ] Multi-row invoices: each row has its OWN analysis (no copy/paste)
- [ ] Multi-row invoices: tax amount validated per line item
- [ ] **BOTH INVOICES READ**: If Inv 1 and Inv 2 exist, both were read and compared
- [ ] **VENDOR MISMATCH CHECKED**: Excel vendor vs invoice vendor compared, flagged if different
- [ ] **SITE ID PATTERN VERIFIED**: If Site ID extracted, verified it matches actual pattern (2-3 letters + digits + optional suffix)
- [ ] **SITE ID FUZZY MATCHING**: Tried stripping suffix if exact match fails (SE0523A → SE0523)
- [ ] **NO FALSE SITE IDS**: Didn't flag short codes (E533), invoice numbers, or PO numbers as Site IDs

### Location Conflict Detection (Sales Tax 2024)
- [ ] **ALL SIGNALS COLLECTED**: Quadrant, sales_tax_state, tax_jurisdiction_state, rate, invoice Ship-To
- [ ] **RATE VALIDATED**: Checked if rate is valid for WA (7.5%-10.6%) or indicates another state
- [ ] **CONFLICTS DETECTED**: Flagged if quadrant ≠ jurisdiction, or rate outside WA range
- [ ] **WEB SEARCH DONE**: If conflict detected, searched to verify suspected state's tax rates
- [ ] **INVOICE VERIFIED**: Read Ship-To address to get ground truth when signals conflict
- [ ] **LOCATION COLUMNS POPULATED**: Location_Signals, Location_Confidence, Likely_Tax_State, Location_Conflict_Type

### Output Format
- [ ] Citations are from approved RCW list or appropriate WAC/ETA
- [ ] Invoice hyperlinks use localhost:8888 format
- [ ] Output columns are in correct order per CLAUDE.md
- [ ] **FORMATTING APPLIED**: Run `python3 scripts/format_excel_output.py` after writing
- [ ] Headers have color-coded backgrounds (blue/green/yellow)
- [ ] Currency columns show commas (18,900.00 not 18900)
- [ ] Rate column shows percentage (8.4% not 0.084)
- [ ] No lazy "REVIEW" flags without actual research documented

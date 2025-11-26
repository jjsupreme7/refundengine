# Research Single Vendor

Uses AI to research a specific vendor and enrich the knowledge base with information about what they sell, their industry, and tax classification. Use this when you encounter an unknown vendor during analysis.

## What It Discovers

For a given vendor name, the AI researches and stores:

| Field | Example |
|-------|---------|
| Industry | "Technology / Cloud Services" |
| Business Model | "B2B SaaS" |
| Products/Services | "Cloud computing, productivity software, AI services" |
| Tax Classification | "Digital Products / Digital Automated Services" |
| Delivery Method | "Electronic delivery" |

## How It Fits In The System

```
/04-analyze finds unknown vendor
        |
        v
"ACME CORP - no vendor data found"
        |
        v
    /18-research-vendor "ACME CORP"
        |
        +--> AI searches web for company info
        |
        +--> Determines what they sell
        |
        +--> Classifies for tax purposes
        |
        +--> Saves to vendor_products table
        |
        v
Next /04-analyze run has vendor context
```

## Arguments

$ARGUMENTS (required)
- Vendor name in quotes

## Examples

```bash
/18-research-vendor "MICROSOFT CORPORATION"
/18-research-vendor "AMAZON WEB SERVICES"
/18-research-vendor "GRAINGER"
/18-research-vendor "ACME INDUSTRIAL SUPPLY"
```

## Success Looks Like

```
Researching vendor: MICROSOFT CORPORATION

Gathering information...
  - Company website: microsoft.com
  - Industry: Technology / Software
  - Primary products: Operating systems, productivity software, cloud services

Analyzing for tax classification...
  - Digital products: Yes (software, cloud services)
  - Tangible goods: Some (Xbox, Surface devices)
  - Primary classification: Digital Automated Services

Saving to database...
✓ Vendor MICROSOFT CORPORATION added to knowledge base

Summary:
  Industry: Technology / Cloud Services
  Products: Windows OS, Microsoft 365, Azure Cloud, Xbox
  Tax Class: Digital Products (primarily), Mixed (some physical goods)
  Confidence: 95%
```

## When To Use

- Analysis shows "unknown vendor"
- You want better context for a specific vendor
- Analyst questions AI's vendor classification
- Before processing a large batch from new client

## Rate Limiting

This uses OpenAI API calls, so:
- One vendor at a time is fine
- For many vendors, use `/19-research-vendors` instead
- ~30 seconds per vendor typical

```bash
python scripts/ai_training/research_all_vendors.py --vendor $ARGUMENTS
```

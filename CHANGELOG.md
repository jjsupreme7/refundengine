# Changelog

All notable changes to the Washington State Tax Refund Analysis Engine are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Category index READMEs for docs subfolders (guides/, technical/, setup/, security/)
- Comprehensive folder READMEs (scripts/, analysis/, tests/, knowledge_base/)
- Master documentation index at docs/README.md
- Archive folders for historical reports (docs/reports/, docs/security/reports/)

### Changed
- Reorganized documentation with dates in filenames (REPORT_TYPE_YYYY-MM-DD.md format)
- Moved misplaced guides to appropriate folders
- Renamed chatbot/README_CHATBOT.md to chatbot/README.md for consistency
- Updated schema audit report to reflect 95% migration completion

---

## [1.0.0] - 2025-11-13

### Major Milestone: Production-Ready System

#### Added
- **Agentic RAG Decision Layer** - Intelligent retrieval optimization with self-verification (Corrective RAG)
- **Web-Based Chatbot UI** - Interactive chatbot with clickable source document links
- **Comprehensive Web Scraping System** - Automated download of WA state tax law (WAC, RCW, WTD)
- **Pattern Learning Module** - Learn from human corrections to improve future accuracy
- **Test Data Ingestion** - Automated test data pipeline for invoices, POs, and Excel files
- **Database Schema Migration** - New schema (knowledge_documents, tax_law_chunks) with compatibility layer
- **Enhanced RAG System** - Query expansion, vendor background integration, advanced filtering
- **Security Audit System** - Comprehensive security code review and vulnerability detection
- **Product Roadmap 2025-2026** - Strategic planning for next 18 months

#### Changed
- **Documentation Reorganization** - Logical folder structure (guides/, technical/, setup/, security/)
- **Database Architecture** - Migration from old schema to optimized new schema
- **Chunking Algorithm** - Smart chunking with sentence boundaries and metadata preservation

#### Security
- **PII Protection** - Comprehensive PII implementation guide and detection
- **Cloud Storage Security** - Secure Supabase Storage configuration
- **Security Best Practices** - Plain-English security guide for developers

---

## [0.9.0] - 2025-11-12

### Beta Release: Core RAG System

#### Added
- **Knowledge Base Management** - 1,681 documents, 4,226 chunks ingested
- **RCW Title 82 Scraper** - Downloaded 1,128 sections with metadata enrichment
- **WAC Title 458 Scraper** - Downloaded 755 sections of administrative code
- **Tax Decisions Scraper** - Automated download of Washington Tax Decisions (WTD)
- **Vector Search** - Supabase pgvector integration for semantic search
- **Document Ingestion Pipeline** - PDF processing with embeddings generation
- **Excel Workflow** - Complete Excel-based analysis workflow
- **Invoice Lookup** - Extract line items from invoice PDFs
- **Refund Analysis Engine** - AI-powered refund eligibility determination

#### Changed
- **Storage System** - Knowledge base sync across machines via Supabase Storage
- **Metadata Management** - Excel-based metadata editing workflow

---

## [0.5.0] - 2025-11-10

### Alpha Release: Proof of Concept

#### Added
- **Core Database Schema** - Initial tables (legal_documents, document_chunks)
- **OpenAI Integration** - GPT-4 for analysis and embeddings
- **Supabase Integration** - PostgreSQL database with pgvector extension
- **Basic Analysis Engine** - Initial refund analysis logic
- **PDF Processing** - pdftotext integration for document parsing
- **Environment Configuration** - .env setup for credentials

---

## Version History

- **1.0.0** (2025-11-13) - Production-ready system with agentic RAG, web UI, and security audit
- **0.9.0** (2025-11-12) - Beta release with complete RAG system and 1,681 documents
- **0.5.0** (2025-11-10) - Alpha proof of concept with basic analysis

---

## Categories

### Added
New features, functionality, or files added to the system.

### Changed
Changes to existing functionality or refactoring.

### Deprecated
Features that are being phased out (still functional but will be removed).

### Removed
Features or files that have been deleted.

### Fixed
Bug fixes and error corrections.

### Security
Security-related changes, vulnerability fixes, or security enhancements.

---

**Current Status** (as of 2025-11-13):
- **Documents in KB**: 1,681 documents
- **Chunks in DB**: 4,226 chunks
- **Schema Migration**: 95% complete
- **Documentation**: 47 markdown files, professionally organized

---

**See also**: [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md) for future development plans.

**Last Updated**: 2025-11-13

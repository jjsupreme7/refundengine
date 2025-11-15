# Documentation Index

Complete guide to all documentation for the Washington State Tax Refund Analysis Engine.

## 🚀 Quick Start

**New to the system? Start here:**

1. **[QUICKSTART Guide](guides/QUICKSTART.md)** - Get up and running in 15 minutes
2. **[Simple Explanation](guides/SIMPLE_EXPLANATION.md)** - Understand how the system works
3. **[Local Environment Setup](setup/LOCAL_ENVIRONMENT_SETUP.md)** - Set up your machine

---

## 📚 Documentation Categories

### 📖 Guides (User-Friendly Tutorials)
Located in: `docs/guides/`

| Guide | Purpose | Best For |
|-------|---------|----------|
| [QUICKSTART](guides/QUICKSTART.md) | Get started in 15 min | New users |
| [SIMPLE_EXPLANATION](guides/SIMPLE_EXPLANATION.md) | How the system works | Understanding concepts |
| [KNOWLEDGE_BASE_GUIDE](guides/KNOWLEDGE_BASE_GUIDE.md) | KB architecture & management | Adding tax law docs |
| [EXCEL_WORKFLOW_GUIDE](guides/EXCEL_WORKFLOW_GUIDE.md) | Excel-based analysis workflow | Analyzing refunds |
| [WEB_SCRAPING_GUIDE](guides/WEB_SCRAPING_GUIDE.md) | Scraping WA tax law | Downloading regulations |
| [ASYNC_PROCESSING_GUIDE](guides/ASYNC_PROCESSING_GUIDE.md) | Celery async processing | Large-scale processing |
| [TESTING_GUIDE](guides/TESTING_GUIDE.md) | Running tests | Developers |
| [QUICK_REFERENCE](guides/QUICK_REFERENCE.md) | Command cheatsheet | Daily use |

---

### 🏗️ Technical Documentation (Deep Dives)
Located in: `docs/technical/`

| Doc | Purpose | Best For |
|-----|---------|----------|
| [ARCHITECTURE](technical/ARCHITECTURE.md) | Business/workflow architecture | Understanding the process |
| [SYSTEM_ARCHITECTURE](technical/SYSTEM_ARCHITECTURE.md) | Technical/database architecture | Database & system design |
| [AGENTIC_RAG_GUIDE](technical/AGENTIC_RAG_GUIDE.md) | Agentic RAG implementation | Advanced RAG features |
| [ENHANCED_RAG_GUIDE](technical/ENHANCED_RAG_GUIDE.md) | Enhanced RAG system | RAG system details |
| [EXCEL_INTEGRATION_EXPLAINED](technical/EXCEL_INTEGRATION_EXPLAINED.md) | Excel integration details | Excel workflows |
| [SMART_CHUNKING_IMPLEMENTATION](technical/SMART_CHUNKING_IMPLEMENTATION.md) | Document chunking algorithm | Improving search quality |
| [RAG_COMPARISON](technical/RAG_COMPARISON.md) | Supabase vs Pinecone | Choosing vector DB |
| [OPTIMIZATION_TIPS](technical/OPTIMIZATION_TIPS.md) | Performance optimization | Speed improvements |

---

### ⚙️ Setup Guides (Getting Started)
Located in: `docs/setup/`

| Guide | Purpose | Best For |
|-------|---------|----------|
| [GETTING_STARTED_CHECKLIST](setup/GETTING_STARTED_CHECKLIST.md) | Complete setup checklist | First-time setup |
| [LOCAL_ENVIRONMENT_SETUP](setup/LOCAL_ENVIRONMENT_SETUP.md) | Local development setup | Developers |
| [DOCKER_GUIDE](setup/DOCKER_GUIDE.md) | Docker deployment | Containerized deployment |
| [PRODUCTION_SETUP](setup/PRODUCTION_SETUP.md) | Production deployment | Production environments |
| [MULTI_COMPUTER_SETUP](setup/MULTI_COMPUTER_SETUP.md) | Multi-machine setup | Team environments |
| [WORK_LAPTOP_QUICKSTART](setup/WORK_LAPTOP_QUICKSTART.md) | Work laptop setup | Corporate environments |

---

### 🔒 Security Documentation
Located in: `docs/security/`

| Doc | Purpose | Best For |
|-----|---------|----------|
| [SECURITY_POLICY](security/SECURITY_POLICY.md) | Security policy | Security overview |
| [SECURITY_BEST_PRACTICES](security/SECURITY_BEST_PRACTICES.md) | Security best practices | Implementation |
| [PII_IMPLEMENTATION_GUIDE](security/PII_IMPLEMENTATION_GUIDE.md) | PII protection | Handling sensitive data |
| [CLOUD_STORAGE_SECURITY](security/CLOUD_STORAGE_SECURITY.md) | Cloud storage security | Supabase Storage |
| [KNOWLEDGE_BASE_SYNC](security/KNOWLEDGE_BASE_SYNC.md) | KB sync across machines | Multi-machine workflows |
| [Security Reports](security/reports/) | Historical security audits | Audit trail |

---

### 📊 Historical Reports (Status Reports)
Located in: `docs/reports/`

| Report | Date | Purpose |
|--------|------|---------|
| [PRE_INGESTION_REPORT_2025-11-12](reports/PRE_INGESTION_REPORT_2025-11-12.md) | Nov 12, 2025 | RAG system audit |
| [SCHEMA_AUDIT_REPORT_2025-11-13](reports/SCHEMA_AUDIT_REPORT_2025-11-13.md) | Nov 13, 2025 | Schema migration status |

See [reports/README.md](reports/README.md) for more details.

---

## 🎯 Find Documentation By Task

### "I want to..."

#### Get Started
- **Set up the system** → [LOCAL_ENVIRONMENT_SETUP](setup/LOCAL_ENVIRONMENT_SETUP.md)
- **Understand how it works** → [SIMPLE_EXPLANATION](guides/SIMPLE_EXPLANATION.md)
- **Run it in 15 minutes** → [QUICKSTART](guides/QUICKSTART.md)

#### Analyze Refunds
- **Analyze Excel file** → [EXCEL_WORKFLOW_GUIDE](guides/EXCEL_WORKFLOW_GUIDE.md)
- **Improve accuracy** → [Knowledge Base Guide](guides/KNOWLEDGE_BASE_GUIDE.md)
- **Process large batches** → [ASYNC_PROCESSING_GUIDE](guides/ASYNC_PROCESSING_GUIDE.md)

#### Manage Knowledge Base
- **Add tax law documents** → [KNOWLEDGE_BASE_GUIDE](guides/KNOWLEDGE_BASE_GUIDE.md)
- **Download regulations** → [WEB_SCRAPING_GUIDE](guides/WEB_SCRAPING_GUIDE.md)
- **Sync across machines** → [KNOWLEDGE_BASE_SYNC](security/KNOWLEDGE_BASE_SYNC.md)

#### Deploy & Configure
- **Deploy to production** → [PRODUCTION_SETUP](setup/PRODUCTION_SETUP.md)
- **Use Docker** → [DOCKER_GUIDE](setup/DOCKER_GUIDE.md)
- **Set up team environment** → [MULTI_COMPUTER_SETUP](setup/MULTI_COMPUTER_SETUP.md)

#### Develop & Extend
- **Understand architecture** → [ARCHITECTURE](technical/ARCHITECTURE.md) + [SYSTEM_ARCHITECTURE](technical/SYSTEM_ARCHITECTURE.md)
- **Improve RAG system** → [ENHANCED_RAG_GUIDE](technical/ENHANCED_RAG_GUIDE.md)
- **Optimize performance** → [OPTIMIZATION_TIPS](technical/OPTIMIZATION_TIPS.md)
- **Run tests** → [TESTING_GUIDE](guides/TESTING_GUIDE.md)

#### Security & Compliance
- **Understand security** → [SECURITY_POLICY](security/SECURITY_POLICY.md)
- **Implement PII protection** → [PII_IMPLEMENTATION_GUIDE](security/PII_IMPLEMENTATION_GUIDE.md)
- **Secure cloud storage** → [CLOUD_STORAGE_SECURITY](security/CLOUD_STORAGE_SECURITY.md)

---

## 📁 Documentation Outside `docs/` Folder

### Module READMEs
- [core/README.md](../core/README.md) - Document ingestion pipeline
- [chatbot/README.md](../chatbot/README.md) - Chatbot usage
- [scripts/README.md](../scripts/README.md) - All scripts explained
- [analysis/README.md](../analysis/README.md) - Analysis modules
- [outputs/README.md](../outputs/README.md) - Excel export workflow
- [metadata_exports/README.md](../metadata_exports/README.md) - Metadata editing
- [database/README.md](../database/README.md) - Database documentation
- [tests/README.md](../tests/README.md) - Testing information
- [knowledge_base/README.md](../knowledge_base/README.md) - KB organization

### Root Documentation
- [../README.md](../README.md) - Main project README
- [../PRODUCT_ROADMAP.md](../PRODUCT_ROADMAP.md) - Product strategy 2025-2026
- [../CHANGELOG.md](../CHANGELOG.md) - Version history

---

## 🔗 External Resources

### Supabase
- [Supabase Documentation](https://supabase.com/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)

### Washington State Tax Law
- [WAC 458 (Tax)](https://app.leg.wa.gov/wac/default.aspx?cite=458)
- [RCW 82 (Revenue)](https://app.leg.wa.gov/rcw/default.aspx?cite=82)
- [WA Tax Decisions](https://dor.wa.gov/about/statistics-reports/tax-decisions)

### OpenAI
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [GPT-4 Best Practices](https://platform.openai.com/docs/guides/gpt-best-practices)

---

## 📝 Documentation Standards

### Naming Conventions
- Guides: `TOPIC_GUIDE.md`
- Technical docs: `COMPONENT_NAME.md`
- Status reports: `REPORT_TYPE_YYYY-MM-DD.md`
- READMEs: Always `README.md` (never `README_FOLDERNAME.md`)

### File Organization
- User guides → `docs/guides/`
- Technical docs → `docs/technical/`
- Setup guides → `docs/setup/`
- Security docs → `docs/security/`
- Status reports → `docs/reports/`
- Module docs → `module_folder/README.md`

---

## 🆘 Need Help?

1. **Check QUICK_REFERENCE** - [Quick Reference Guide](guides/QUICK_REFERENCE.md)
2. **Search this index** - Find relevant doc above
3. **Check module README** - Each folder has README.md
4. **Ask in issues** - GitHub issues for questions

---

**Last Updated**: 2025-11-13

**Documentation Quality**: 47 documents, professionally organized

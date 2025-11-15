# Test Tools

This directory contains standalone testing and interactive debugging scripts.

These are **not** automated pytest unit tests - they are manual testing tools that:
- Connect to real APIs (OpenAI, Supabase, etc.)
- Require valid API keys and credentials
- Are meant to be run interactively for debugging and validation

## Available Tools

- `test_rag.py` - Interactive RAG (Retrieval Augmented Generation) testing tool
- `test_enhanced_rag.py` - Testing for enhanced RAG with multi-query support
- `test_agentic_rag.py` - Testing for autonomous agent RAG system
- `test_chatbot.py` - Quick test of the RAG chatbot
- `test_pii_protection.py` - Testing PII detection and redaction
- `test_analyze_refunds.py` - Testing refund analysis functionality
- `test_vendor_research.py` - Testing vendor research capabilities
- `test_refund_calculations.py` - Testing refund calculation logic

## Usage

Run these scripts directly with Python when you need to manually test functionality:

```bash
python scripts/test_tools/test_rag.py
python scripts/test_tools/test_chatbot.py
```

Make sure you have:
1. Valid API keys in your `.env` file
2. Required dependencies installed (`pip install -r requirements.txt`)
3. Database connections configured

## Automated Tests

For automated CI/CD tests, see the `tests/` directory which contains proper pytest unit tests.

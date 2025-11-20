#!/bin/bash
# Quick test script for Enhanced RAG improvements

echo "=================================="
echo "Testing Enhanced RAG Improvements"
echo "=================================="
echo ""

echo "🧪 Running tests..."
pytest tests/test_enhanced_rag.py -v

echo ""
echo "=================================="
echo "📊 Comparing all RAG methods"
echo "=================================="
echo ""

python analysis/analyze_refunds_enhanced.py \
    --vendor "Microsoft Corporation" \
    --product "Microsoft 365 E5 licenses for multi-state workforce" \
    --product-type "SaaS" \
    --amount 50000 \
    --tax 5000 \
    --compare

echo ""
echo "=================================="
echo "✅ Test complete!"
echo "=================================="
echo ""
echo "📚 Next steps:"
echo "  1. Read ENHANCED_RAG_GUIDE.md"
echo "  2. Choose your default RAG method"
echo "  3. Integrate into production"
echo ""

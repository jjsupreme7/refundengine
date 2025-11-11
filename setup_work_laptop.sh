#!/bin/bash
# Work Laptop Setup Script
# Run this on your work laptop to set up the refund engine

echo "🚀 Refund Engine - Work Laptop Setup"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.12+"
    echo "   Download from: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check if in correct directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Not in refund-engine directory"
    echo "   Please cd to the refund-engine folder first"
    exit 1
fi

echo "✅ In refund-engine directory"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "⬇️  Installing dependencies (this may take a few minutes)..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo ""
    echo "📝 Creating .env template..."
    cat > .env << 'EOF'
# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Database
SUPABASE_DB_PASSWORD=your_db_password_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_key_here
EOF
    echo "✅ Created .env template"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your actual credentials!"
    echo "   1. Go to https://supabase.com/dashboard"
    echo "   2. Select your project"
    echo "   3. Go to Settings → API"
    echo "   4. Copy credentials to .env file"
    echo ""
else
    echo "✅ .env file exists"
fi

# Create client_documents structure
echo "📁 Setting up client_documents folders..."
mkdir -p client_documents/invoices
mkdir -p client_documents/purchase_orders
mkdir -p client_documents/master_data
echo "✅ Client document folders created"
echo ""

# Create outputs structure
echo "📁 Setting up outputs folders..."
mkdir -p outputs/reports
mkdir -p outputs/analysis
mkdir -p outputs/dor_filings
echo "✅ Output folders created"
echo ""

echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Supabase credentials"
echo "2. Test connection: python scripts/utils/check_supabase_tables.py"
echo "3. Add client documents to: client_documents/invoices/"
echo "4. Run analysis: python analysis/analyze_refunds.py"
echo ""
echo "📖 See docs/MULTI_COMPUTER_SETUP.md for detailed instructions"

#!/bin/bash

# Local Environment Setup Script for Refund Engine
# This script sets up your local development environment

set -e  # Exit on error

echo "======================================"
echo "Refund Engine - Local Setup"
echo "======================================"
echo ""

# Check if .env exists
if [ -f ".env" ]; then
    echo "✅ .env file already exists"
    read -p "Do you want to recreate it? (y/N): " recreate
    if [[ $recreate =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo "✅ Created new .env from template"
    fi
else
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
fi

echo ""
echo "======================================"
echo "Step 1: Python Environment"
echo "======================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Python dependencies installed"

echo ""
echo "======================================"
echo "Step 2: Directory Structure"
echo "======================================"

# Create necessary directories
directories=(
    "client_documents/invoices"
    "knowledge_base/states/washington/legal_documents"
    "knowledge_base/vendors"
    "knowledge_base/taxonomy"
    "output"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "✅ Created $dir"
    else
        echo "✅ $dir already exists"
    fi
done

echo ""
echo "======================================"
echo "Step 3: Configuration"
echo "======================================"
echo ""
echo "⚠️  IMPORTANT: You need to configure your .env file"
echo ""
echo "Required credentials:"
echo "  1. OpenAI API Key (https://platform.openai.com/api-keys)"
echo "  2. Supabase URL and Service Role Key (https://supabase.com/dashboard)"
echo "  3. Supabase Database Password"
echo ""
echo "Edit .env file and add your credentials:"
echo "  nano .env"
echo ""

read -p "Press Enter when you've configured your .env file..."

echo ""
echo "======================================"
echo "Step 4: Database Setup"
echo "======================================"
echo ""
echo "Do you want to deploy the database schema to Supabase? (y/N)"
read -p "> " deploy_db

if [[ $deploy_db =~ ^[Yy]$ ]]; then
    # Load environment variables
    source .env

    echo "Deploying database schema..."

    if [ -f "scripts/0_deploy_schema.sh" ]; then
        bash scripts/0_deploy_schema.sh
    else
        echo "Running manual deployment..."
        PGPASSWORD=$SUPABASE_DB_PASSWORD psql -h $SUPABASE_DB_HOST -U $SUPABASE_DB_USER -d $SUPABASE_DB_NAME -f database/schema_knowledge_base.sql
        PGPASSWORD=$SUPABASE_DB_PASSWORD psql -h $SUPABASE_DB_HOST -U $SUPABASE_DB_USER -d $SUPABASE_DB_NAME -f database/schema_vendor_learning.sql
    fi

    echo "✅ Database schema deployed"
else
    echo "⏭️  Skipping database deployment"
    echo "   Run manually later with: bash scripts/0_deploy_schema.sh"
fi

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Test the RAG system:"
echo "   python3 scripts/test_rag.py"
echo ""
echo "3. Ingest tax law documents:"
echo "   python3 scripts/8_ingest_knowledge_base.py tax_law \"knowledge_base/states/washington/legal_documents/\" --citation \"RCW 82.08\" --law-category exemption"
echo ""
echo "4. Analyze invoices:"
echo "   python3 scripts/6_analyze_refunds.py \"your-file.xlsx\" --save-db"
echo ""
echo "For more info, see:"
echo "  - README.md"
echo "  - QUICKSTART.md"
echo "  - docs/ folder"
echo ""

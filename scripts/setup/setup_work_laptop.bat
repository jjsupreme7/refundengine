@echo off
REM Work Laptop Setup Script (Windows)
REM Run this on your work laptop to set up the refund engine

echo ===================================
echo Refund Engine - Work Laptop Setup
echo ===================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo X Python not found. Please install Python 3.12+
    echo   Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Check if in correct directory
if not exist requirements.txt (
    echo X Not in refund-engine directory
    echo   Please cd to the refund-engine folder first
    pause
    exit /b 1
)

echo [OK] In refund-engine directory
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies (this may take a few minutes)...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [OK] Installation complete!
echo.

REM Check for .env file
if not exist .env (
    echo [!] .env file not found
    echo.
    echo Creating .env template...
    (
        echo # Supabase Configuration
        echo SUPABASE_URL=your_supabase_url_here
        echo SUPABASE_KEY=your_anon_key_here
        echo SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
        echo.
        echo # Database
        echo SUPABASE_DB_PASSWORD=your_db_password_here
        echo.
        echo # OpenAI API Key
        echo OPENAI_API_KEY=your_openai_key_here
    ) > .env
    echo [OK] Created .env template
    echo.
    echo [!] IMPORTANT: Edit .env file with your actual credentials!
    echo   1. Go to https://supabase.com/dashboard
    echo   2. Select your project
    echo   3. Go to Settings -^> API
    echo   4. Copy credentials to .env file
    echo.
) else (
    echo [OK] .env file exists
)

REM Create client_documents structure
echo Setting up client_documents folders...
if not exist client_documents\invoices mkdir client_documents\invoices
if not exist client_documents\purchase_orders mkdir client_documents\purchase_orders
if not exist client_documents\master_data mkdir client_documents\master_data
echo [OK] Client document folders created
echo.

REM Create outputs structure
echo Setting up outputs folders...
if not exist outputs\reports mkdir outputs\reports
if not exist outputs\analysis mkdir outputs\analysis
if not exist outputs\dor_filings mkdir outputs\dor_filings
echo [OK] Output folders created
echo.

echo ===================================
echo [OK] Setup Complete!
echo ===================================
echo.
echo Next steps:
echo 1. Edit .env file with your Supabase credentials
echo 2. Test connection: python scripts\utils\check_supabase_tables.py
echo 3. Add client documents to: client_documents\invoices\
echo 4. Run analysis: python analysis\analyze_refunds.py
echo.
echo See docs\MULTI_COMPUTER_SETUP.md for detailed instructions
echo.
pause

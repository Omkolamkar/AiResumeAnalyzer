@echo off
echo 🚀 Setting up AI Resume Analyzer Environment
echo ========================================

echo.
echo 📝 This script will help you set up the required API keys.
echo You'll need to get API keys from these services:
echo.
echo 1. Google AI Studio (Gemini API): https://makersuite.google.com/app/apikey
echo 2. Adzuna API: https://developer.adzuna.com/overview
echo 3. RapidAPI (JSearch): https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
echo.

REM Create .env file
echo Creating .env file...
echo # AI Resume Analyzer Configuration > .env
echo # Get your API keys from the URLs mentioned above >> .env
echo. >> .env
echo # Google AI Studio API Key for Gemini >> .env
echo GOOGLE_API_KEY=your_google_api_key_here >> .env
echo. >> .env
echo # Adzuna API Credentials >> .env
echo ADZUNA_APP_ID=your_adzuna_app_id_here >> .env
echo ADZUNA_APP_KEY=your_adzuna_app_key_here >> .env
echo. >> .env
echo # RapidAPI Key for JSearch >> .env
echo RAPIDAPI_KEY=your_rapidapi_key_here >> .env
echo. >> .env

echo ✅ Created .env file
echo.
echo 🔧 NEXT STEPS:
echo 1. Edit the .env file and add your real API keys
echo 2. Run: python config_check_windows.py
echo 3. Run: python app.py
echo.
echo 💡 TIP: Open .env with notepad and replace the placeholder values
echo.
pause

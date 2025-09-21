# 🚀 Deployment & Troubleshooting Guide

## Quick Start (5 Minutes Setup)

### 1. **Clone and Setup** 
```bash
git clone <your-repo-url>
cd ai-resume-analyzer

# Make setup script executable and run
chmod +x setup.sh
./setup.sh
```

### 2. **Get API Keys**
- **Google AI**: https://makersuite.google.com/app/apikey (Required)
- **Adzuna**: https://developer.adzuna.com/overview (Recommended)
- **RapidAPI**: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch/ (Optional)

### 3. **Configure Environment**
```bash
cp .env.example .env
# Edit .env and add your API keys
nano .env
```

### 4. **Run Application**
```bash
streamlit run app_improved.py
```

---

## 📋 **File Checklist**

### **Enhanced Files (Recommended)**
- ✅ `config.py` - Configuration management
- ✅ `utils.py` - Enhanced utilities 
- ✅ `jobs_api_improved.py` - Advanced job search
- ✅ `matching_improved.py` - ML-powered matching
- ✅ `utils_profile_improved.py` - Enhanced profiling
- ✅ `app_improved.py` - Main enhanced application
- ✅ `requirements_improved.txt` - Updated dependencies
- ✅ `.env.example` - Environment template
- ✅ `setup.sh` - Automated setup script

### **Original Files (Fallback)**
- 📄 `app.py` - Original application
- 📄 `jobs_api.py` - Basic job search
- 📄 `matching.py` - Simple matching
- 📄 `utils_profile.py` - Basic profiling
- 📄 `requirements.txt` - Basic dependencies

---

## 🐛 **Common Issues & Solutions**

### **Issue 1: Import Errors**
```
ModuleNotFoundError: No module named 'config'
```
**Solution:**
```bash
# Ensure you're using enhanced files
ls -la *.py
# Should show all enhanced files (config.py, utils.py, etc.)

# If missing, use original app
streamlit run app.py
```

### **Issue 2: API Key Errors**
```
Error: Missing required API keys: GOOGLE_API_KEY
```
**Solution:**
```bash
# Check .env file exists
ls -la .env

# Check content
cat .env | grep GOOGLE_API_KEY

# Add missing key
echo "GOOGLE_API_KEY=your_actual_key_here" >> .env
```

### **Issue 3: PDF Processing Fails**
```
Error: Failed to extract text from PDF
```
**Solutions:**
```bash
# Install system dependencies
# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler

# Windows: Download and install manually
```

### **Issue 4: Streamlit Won't Start**
```
Command 'streamlit' not found
```
**Solution:**
```bash
# Install streamlit
pip install streamlit

# Or reinstall all requirements
pip install -r requirements_improved.txt
```

### **Issue 5: Job Search Fails**
```
Job search failed: All job search APIs failed
```
**Solutions:**
1. Check API keys in .env
2. Verify internet connection
3. Check API rate limits
4. Use individual APIs:
```python
# Test individual APIs
from jobs_api_improved import search_adzuna
jobs = search_adzuna("python developer", "remote")
```

---

## 🔧 **Advanced Troubleshooting**

### **Debug Mode**
```bash
# Enable debug logging
echo "LOG_LEVEL=DEBUG" >> .env
streamlit run app_improved.py

# Check logs
tail -f app.log
```

### **Check Dependencies**
```bash
# Verify Python version (need 3.8+)
python3 --version

# Check installed packages
pip list | grep -E "(streamlit|google-generativeai|requests)"

# Reinstall if needed
pip install --upgrade streamlit google-generativeai
```

### **Test Components Individually**
```python
# Test AI connection
python3 -c "
from config import validate_api_keys
try:
    validate_api_keys()
    print('✅ API keys valid')
except Exception as e:
    print(f'❌ API Error: {e}')
"

# Test PDF processing
python3 -c "
from utils import validate_file
print('✅ Utils working')
"
```

---

## 🌐 **Deployment Options**

### **Option 1: Streamlit Cloud (Recommended)**
1. Push code to GitHub
2. Go to https://share.streamlit.io
3. Connect repository
4. Add secrets in dashboard:
   ```toml
   GOOGLE_API_KEY = "your_key"
   ADZUNA_APP_ID = "your_id"
   ADZUNA_APP_KEY = "your_key"
   ```

### **Option 2: Heroku**
```bash
# Create Procfile
echo "web: streamlit run app_improved.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# Deploy
heroku create your-app-name
heroku config:set GOOGLE_API_KEY=your_key
git push heroku main
```

### **Option 3: Docker**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements_improved.txt .
RUN pip install -r requirements_improved.txt

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app_improved.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### **Option 4: Local Network**
```bash
# Run on local network
streamlit run app_improved.py --server.address=0.0.0.0 --server.port=8501

# Access from other devices on network
# http://YOUR_LOCAL_IP:8501
```

---

## 🔒 **Security Best Practices**

### **API Key Security**
```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use environment variables in production
export GOOGLE_API_KEY=your_key
export ADZUNA_APP_ID=your_id

# Rotate keys regularly
# Monitor usage in API dashboards
```

### **File Upload Security**
```python
# Enhanced version has built-in security:
# - File size limits (10MB default)
# - File type validation
# - Content validation
# - Secure temporary file handling
```

---

## 📊 **Performance Optimization**

### **Caching Configuration**
```bash
# Adjust cache settings in .env
CACHE_TTL=3600  # 1 hour
MAX_JOBS_PER_SEARCH=50
API_TIMEOUT=30
```

### **System Requirements**
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 1GB free space
- **Internet**: Stable connection for API calls
- **Python**: 3.8+ (3.9+ recommended)

### **Resource Monitoring**
```bash
# Monitor resource usage
htop  # CPU/Memory
iostat  # Disk I/O
netstat -i  # Network
```

---

## 🧪 **Testing & Validation**

### **Quick Health Check**
```bash
# Run health check script
./setup.sh --validate

# Or manual check
python3 -c "
import sys
print(f'Python: {sys.version}')
try:
    import streamlit
    print(f'Streamlit: {streamlit.__version__}')
except:
    print('❌ Streamlit not installed')
"
```

### **Component Tests**
```python
# Test individual components
python3 -c "
# Test config
from config import api_config, app_config
print('✅ Config loaded')

# Test utilities
from utils import validate_file
print('✅ Utils working')

# Test job APIs (if keys configured)
try:
    from jobs_api_improved import get_job_search_stats
    stats = get_job_search_stats()
    print(f'✅ Job APIs working: {stats}')
except Exception as e:
    print(f'⚠️  Job APIs: {e}')
"
```

---

## 📞 **Getting Help**

### **Check Logs First**
```bash
# Application logs
tail -f app.log

# Streamlit logs
~/.streamlit/logs/
```

### **Common Log Patterns**
- `API Error`: Check API keys and internet
- `Import Error`: Check file structure and dependencies
- `Validation Error`: Check input files and formats
- `Rate Limit`: Wait or check API quotas

### **Contact & Support**
- **GitHub Issues**: For bugs and feature requests
- **Documentation**: This guide and README_enhanced.md
- **Community**: Streamlit forums for general questions

---

## 🎯 **Quick Reference**

### **Essential Commands**
```bash
# Setup everything
./setup.sh

# Run enhanced app
streamlit run app_improved.py

# Run original app (fallback)
streamlit run app.py

# Debug mode
LOG_LEVEL=DEBUG streamlit run app_improved.py

# Install dependencies
pip install -r requirements_improved.txt
```

### **Essential Files**
- **`.env`**: API keys and configuration
- **`app.log`**: Application logs
- **`app_improved.py`**: Enhanced application
- **`config.py`**: Configuration management

---

**🎉 You're all set! Enjoy the Enhanced AI Resume Analyzer!**
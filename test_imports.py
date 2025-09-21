# test_imports.py - Test Script for Import Issues

import sys
import os

print("🧪 Testing AI Resume Analyzer Imports")
print("=" * 50)

def test_import(module_name, items):
    """Test importing specific items from a module"""
    try:
        module = __import__(module_name, fromlist=items)
        for item in items:
            if hasattr(module, item):
                print(f"✅ {module_name}.{item} - OK")
            else:
                print(f"❌ {module_name}.{item} - MISSING")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name} - OTHER ERROR: {e}")
        return False

print("\n1. Testing Core Dependencies...")
core_modules = {
    'streamlit': ['session_state', 'error', 'success'],
    'requests': ['get', 'post'],
    'logging': ['getLogger', 'info'],
    'os': ['getenv', 'path']
}

for module, items in core_modules.items():
    test_import(module, items)

print("\n2. Testing Application Modules...")
app_modules = {
    'config': ['api_config', 'app_config'],
    'utils': ['retry_with_exponential_backoff', 'cache_key_generator'],
    'jobs_api_improved': ['search_all_apis', 'JobResult', 'get_job_search_stats'],
    'matching_improved': ['AdvancedJobMatcher'],
    'utils_profile_improved': ['ProfileExtractor']
}

success_count = 0
total_count = 0

for module, items in app_modules.items():
    total_count += 1
    if test_import(module, items):
        success_count += 1

print("\n" + "=" * 50)
print(f"📊 RESULTS: {success_count}/{total_count} modules imported successfully")

if success_count == total_count:
    print("\n🎉 ALL IMPORTS WORKING!")
    print("✅ Your application should start without errors.")
    print("\n🚀 Run: streamlit run app.py")
else:
    print("\n⚠️  SOME IMPORTS FAILED!")
    print("💡 Check the errors above and ensure:")
    print("   1. All files are in the same directory")
    print("   2. Python dependencies are installed: pip install -r requirements.txt")
    print("   3. No syntax errors in the Python files")

print("\n📝 Tip: If jobs_api_improved import fails, run fix_import_error.bat")

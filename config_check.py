# config_check_windows.py - Windows Configuration Validator

import os
import sys
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import config
try:
    from config import api_config
    print("✅ Successfully imported config")
except Exception as e:
    print(f"❌ Failed to import config: {e}")
    sys.exit(1)

class WindowsAPIValidator:
    def __init__(self):
        self.results = {}

    def check_rapidapi_jsearch(self):
        """Test RapidAPI/JSearch configuration specifically for Windows"""
        print("\n🔍 Testing JSearch API Configuration...")

        rapidapi_key = api_config.rapidapi_key
        if not rapidapi_key:
            print("❌ RAPIDAPI_KEY not found in environment")
            return False

        print(f"✅ RAPIDAPI_KEY found: {rapidapi_key[:8]}...")

        # Test the actual API call
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        params = {
            "query": "test",
            "page": "1", 
            "num_pages": "1",
            "results_per_page": "1"
        }

        try:
            print("🌐 Making test API call...")
            response = requests.get(url, headers=headers, params=params, timeout=10)

            print(f"📊 Response Status: {response.status_code}")

            if response.status_code == 200:
                print("✅ JSearch API working correctly!")
                data = response.json()
                print(f"📈 Found {len(data.get('data', []))} test jobs")
                return True
            elif response.status_code == 403:
                print("❌ 403 Forbidden: Invalid API key or subscription expired")
                print("💡 Solution: Check your RapidAPI subscription for JSearch")
                return False
            elif response.status_code == 429:
                print("⚠️ 429 Rate Limited: Too many requests")
                print("💡 Solution: Wait a moment and try again")
                return False
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return False

        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    def run_diagnosis(self):
        print("🚀 Windows JSearch API Diagnosis")
        print("=" * 40)

        # Test the API
        jsearch_working = self.check_rapidapi_jsearch()

        print("\n" + "=" * 40)
        print("📋 DIAGNOSIS SUMMARY:")

        if jsearch_working:
            print("✅ JSearch API is working correctly")
            print("✅ Your application should be able to fetch jobs from JSearch")
        else:
            print("❌ JSearch API is not working")
            print("💡 SOLUTIONS TO TRY:")
            print("1. Check your RapidAPI subscription: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch")
            print("2. Verify your API key in the .env file or environment variables")
            print("3. Make sure you have an active subscription to JSearch API")
            print("4. Check if your IP is blocked or rate limited")

if __name__ == "__main__":
    validator = WindowsAPIValidator()
    validator.run_diagnosis()

#!/usr/bin/env python3
"""
Coohom API Authentication Test Script

Tests API credentials using the Account Information endpoint.
This endpoint is perfect for authentication testing because it:
- Returns real data (not timeouts like STS endpoints)
- Uses the proper account API signature method
- Provides clear success/failure responses

Run: python3 test_api.py
"""

import requests
import hashlib
import time
from urllib.parse import quote

def load_credentials():
    """Load credentials from file."""
    try:
        with open('credentials.txt', 'r') as f:
            creds = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    creds[key] = value
            return creds
    except FileNotFoundError:
        print("❌ credentials.txt file not found!")
        return None



def generate_account_signature(app_secret, app_key, timestamp):
    """Generate signature for account API using different method."""
    # For account API: sign = md5(appSecret + appkey + timestamp)
    sign_string = f"{app_secret}{app_key}{timestamp}"
    print(f"🔍 Account API sign string: {sign_string}")
    signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
    return signature

def test_authentication():
    """Test API authentication without triggering file upload processes."""
    print("🧪 Testing Coohom API Authentication...")
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        return False
    
    app_key = creds.get('appKey')
    app_secret = creds.get('appSecret')
    
    if not app_key or not app_secret:
        print("❌ Missing appKey or appSecret in credentials.txt")
        return False
    
    print(f"✅ Credentials loaded:")
    print(f"   App Key: {app_key}")
    print(f"   App Secret: {app_secret[:10]}...")
    
    # Test the Account Information API - perfect for authentication testing
    timestamp = str(int(time.time() * 1000))  # milliseconds for account API
    
    print(f"\n🔍 Testing Account Information API...")
    print(f"   URL: https://api.coohom.com/global/user")
    print(f"   This endpoint returns real account data if authentication works!")
    
    params = {
        'appkey': app_key,
        'timestamp': timestamp,
        'start': '0',
        'num': '1'
    }
    
    # Generate signature using account API method: md5(appSecret + appkey + timestamp)
    signature = generate_account_signature(app_secret, app_key, timestamp)
    params['sign'] = signature
    
    try:
        response = requests.get("https://api.coohom.com/global/user", params=params, timeout=15)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Response Code: {data.get('c', 'N/A')}")
                print(f"   Message: {data.get('m', 'N/A')}")
                
                if data.get('c') == '0':
                    print("   🎉 SUCCESS! Authentication is working perfectly!")
                    
                    # Show account information
                    account_data = data.get('d', {})
                    print(f"   📊 Account Info:")
                    print(f"      Total Accounts: {account_data.get('totalCount', 'N/A')}")
                    print(f"      Returned Count: {account_data.get('count', 'N/A')}")
                    print(f"      Has More: {account_data.get('hasMore', 'N/A')}")
                    
                    return True
                else:
                    print(f"   ❌ API Error: {data.get('m', 'Unknown error')}")
                    return False
                    
            except ValueError as e:
                print(f"   ❌ Invalid JSON response: {str(e)}")
                return False
                
        elif response.status_code == 401:
            print("   ❌ 401 Unauthorized - authentication failed")
            print("   🔍 Check your appKey and appSecret in credentials.txt")
            return False
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("   ⏱️ Request timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("   🌐 Connection error - check your internet connection")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🏠 Coohom API Authentication Test Script")
    print("=" * 60)
    
    # Test the Account Information API (perfect for authentication testing)
    auth_success = test_authentication()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    
    if auth_success:
        print("🎉 AUTHENTICATION: ✅ SUCCESS!")
        print("✅ Your API credentials are working perfectly.")
        print("✅ You can access Coohom's API successfully.")
    else:
        print("💥 AUTHENTICATION: ❌ FAILED!")
        print("❌ There's an issue with your API credentials.")
        print("🔍 Double-check your appKey and appSecret in credentials.txt")
        print("🌐 Also verify your internet connection.")
    
    print("=" * 60)

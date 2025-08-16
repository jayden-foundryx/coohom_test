#!/usr/bin/env python3
"""
Standalone Python request script for testing Coohom API without Streamlit.
This script demonstrates how to upload 3D files to Coohom using their API.
"""

import requests
import hashlib
import time
import os
from urllib.parse import quote
import json


class CoohomAPITester:
    """
    Standalone Coohom API client for testing without UI dependencies.
    """
    
    def __init__(self, app_key, app_secret):
        """
        Initialize the Coohom API tester.
        
        Args:
            app_key (str): Coohom API key
            app_secret (str): Coohom API secret
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = "https://api.coohom.com"
        
        print(f"🔧 Initialized Coohom API Tester")
        print(f"   App Key: {app_key}")
        print(f"   Base URL: {self.base_url}")
    
    def generate_signature(self, params):
        """
        Generate signature for API authentication following Coohom pattern.
        
        Args:
            params (dict): Parameters to include in signature
            
        Returns:
            str: MD5 hash signature
        """
        # Sort parameters alphabetically (excluding sign if present)
        filtered_params = {k: v for k, v in params.items() if k != 'sign'}
        sorted_params = sorted(filtered_params.items())
        param_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # Create signature string by appending appSecret
        sign_string = f"{param_string}&{self.app_secret}"
        
        # Generate MD5 hash
        signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
        return signature
    
    def get_sts_credentials(self, filename, max_retries=3):
        """
        Get STS credentials for file upload from Coohom API.
        
        Args:
            filename (str): Name of the file to upload
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            dict or None: STS credentials if successful, None otherwise
        """
        print(f"\n📡 Getting STS credentials for: {filename}")
        
        for attempt in range(max_retries):
            try:
                # URL encode the filename
                encoded_filename = quote(filename)
                
                # Prepare parameters
                timestamp = str(int(time.time()))
                params = {
                    'appkey': self.app_key,  # Note: lowercase 'appkey'
                    'timestamp': timestamp,
                    'file_name': encoded_filename
                }
                
                # Generate signature
                signature = self.generate_signature(params)
                params['sign'] = signature
                
                # API endpoint
                url = f"{self.base_url}/global/commodity/upload/sts"
                
                print(f"🔍 Attempt {attempt + 1}/{max_retries}")
                print(f"   URL: {url}")
                print(f"   Encoded filename: {encoded_filename}")
                print(f"   Timestamp: {timestamp}")
                print(f"   Signature: {signature[:10]}...")
                
                # Make API request
                response = requests.get(url, params=params, timeout=30)
                
                print(f"   Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   Response Code: {data.get('c', 'N/A')}")
                        print(f"   Response Message: {data.get('m', 'N/A')}")
                        
                        if data.get('c') == '0':  # Success code
                            print("✅ STS credentials obtained successfully!")
                            return data.get('d')
                        
                        elif data.get('c') == '100004':  # Timeout error - retry
                            if attempt < max_retries - 1:
                                wait_time = (attempt + 1) * 2  # Exponential backoff
                                print(f"⏱️ API Timeout. Retrying in {wait_time}s...")
                                time.sleep(wait_time)
                                continue
                            else:
                                print("❌ API Timeout after all retry attempts")
                                print("📡 Coohom servers are experiencing high load. Try again later.")
                                return None
                        
                        else:
                            print(f"❌ API Error (Code {data.get('c')}): {data.get('m', 'Unknown error')}")
                            print(f"Raw response: {json.dumps(data, indent=2)}")
                            return None
                    
                    except ValueError as e:
                        print(f"❌ Invalid JSON response: {str(e)}")
                        print(f"Raw response: {response.text[:200]}...")
                        return None
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    print(f"Response text: {response.text[:200]}...")
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⏱️ Request timeout. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print("❌ Request timeout after all attempts")
                    return None
                    
            except requests.exceptions.ConnectionError:
                print("❌ Connection error - Check your internet connection")
                return None
                
            except Exception as e:
                print(f"❌ Unexpected error getting STS credentials: {str(e)}")
                return None
        
        return None
    
    def upload_to_oss(self, file_path, sts_data):
        """
        Upload file to Alibaba Cloud OSS using STS credentials.
        
        Args:
            file_path (str): Local file path to upload
            sts_data (dict): STS credentials from get_sts_credentials
            
        Returns:
            dict: Upload result with success status and details
        """
        print(f"\n📤 Uploading file to OSS: {file_path}")
        
        try:
            import oss2
        except ImportError:
            print("❌ oss2 library not installed. Please install it with: pip install oss2")
            return {'success': False, 'error': 'Missing oss2 library'}
        
        try:
            # Read file data
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Extract STS credentials
            access_key_id = sts_data['accessKeyId']
            access_key_secret = sts_data['accessKeySecret']
            security_token = sts_data['securityToken']
            bucket_name = sts_data['bucket']
            region = sts_data['region']
            remote_file_path = sts_data['filePath']
            
            print(f"   File size: {len(file_data)} bytes")
            print(f"   Bucket: {bucket_name}")
            print(f"   Region: {region}")
            print(f"   Remote path: {remote_file_path}")
            
            # Create OSS client with STS token
            auth = oss2.StsAuth(access_key_id, access_key_secret, security_token)
            endpoint = f"https://oss-{region}.aliyuncs.com"
            bucket = oss2.Bucket(auth, endpoint, bucket_name)
            
            # Upload file
            result = bucket.put_object(remote_file_path, file_data)
            
            if result.status == 200:
                print("✅ File uploaded to OSS successfully!")
                return {
                    'success': True,
                    'upload_task_id': sts_data['uploadTaskId'],
                    'file_path': remote_file_path,
                    'file_size': len(file_data)
                }
            else:
                print(f"❌ Upload failed with status: {result.status}")
                return {'success': False, 'error': f"Upload failed with status: {result.status}"}
                
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
            return {'success': False, 'error': f'File not found: {file_path}'}
        except Exception as e:
            print(f"❌ Upload error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def check_upload_status(self, upload_task_id):
        """
        Check the status of an upload task.
        
        Args:
            upload_task_id (str): Task ID returned from STS credentials
            
        Returns:
            dict: Status information or error details
        """
        print(f"\n🔍 Checking upload status for task: {upload_task_id}")
        
        try:
            timestamp = str(int(time.time()))
            params = {
                'appkey': self.app_key,  # Note: lowercase 'appkey'
                'timestamp': timestamp,
                'upload_task_id': upload_task_id
            }
            
            signature = self.generate_signature(params)
            params['sign'] = signature
            
            url = f"{self.base_url}/global/commodity/upload/status"
            
            print(f"   URL: {url}")
            print(f"   Task ID: {upload_task_id}")
            
            response = requests.get(url, params=params, timeout=30)
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response Code: {data.get('c', 'N/A')}")
                print(f"   Response Message: {data.get('m', 'N/A')}")
                
                if data.get('c') == '0':
                    status_data = data.get('d')
                    print(f"✅ Status check successful!")
                    if status_data:
                        print(f"   Status details: {json.dumps(status_data, indent=2)}")
                    return status_data
                else:
                    print(f"❌ Status check error: {data.get('m', 'Unknown error')}")
                    print(f"Raw response: {json.dumps(data, indent=2)}")
                    return {'error': data.get('m', 'Unknown error')}
            else:
                print(f"❌ Status check HTTP error: {response.status_code}")
                return {'error': f"HTTP Error: {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Status check error: {str(e)}")
            return {'error': str(e)}
    
    def submit_parsed_model(self, upload_task_id):
        """
        Submit parsed ZIP files for Coohom models (Step 5 of upload process).
        
        Args:
            upload_task_id (str): Task ID from upload
            
        Returns:
            dict: Submission result
        """
        print(f"\n🎯 Submitting parsed model for task: {upload_task_id}")
        
        try:
            timestamp = str(int(time.time()))
            params = {
                'appkey': self.app_key,
                'timestamp': timestamp,
                'upload_task_id': upload_task_id
            }
            
            signature = self.generate_signature(params)
            params['sign'] = signature
            
            url = f"{self.base_url}/global/commodity/upload/submit"
            
            print(f"   URL: {url}")
            print(f"   Task ID: {upload_task_id}")
            
            response = requests.post(url, data=params, timeout=30)
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response Code: {data.get('c', 'N/A')}")
                print(f"   Response Message: {data.get('m', 'N/A')}")
                
                if data.get('c') == '0':
                    print("✅ Model submission successful!")
                    result_data = data.get('d')
                    if result_data:
                        print(f"   Result: {json.dumps(result_data, indent=2)}")
                    return result_data
                else:
                    print(f"❌ Submission error: {data.get('m', 'Unknown error')}")
                    print(f"Raw response: {json.dumps(data, indent=2)}")
                    return {'error': data.get('m', 'Unknown error')}
            else:
                print(f"❌ Submission HTTP error: {response.status_code}")
                return {'error': f"HTTP Error: {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Submission error: {str(e)}")
            return {'error': str(e)}
    
    def get_account_information(self):
        """
        Get account information using API #6 from the documentation.
        This tests a different endpoint to see if timeouts are universal.
        
        Returns:
            dict: Account information or error details
        """
        print(f"\n👤 Getting account information (API #6)")
        
        try:
            timestamp = str(int(time.time()))
            params = {
                'appkey': self.app_key,  # Note: lowercase 'appkey'
                'timestamp': timestamp
            }
            
            signature = self.generate_signature(params)
            params['sign'] = signature
            
            # Based on the API docs, this appears to be for account info
            # We'll try the most likely endpoint path
            url = f"{self.base_url}/global/account/info"
            
            print(f"   URL: {url}")
            print(f"   Timestamp: {timestamp}")
            print(f"   Signature: {signature[:10]}...")
            
            response = requests.get(url, params=params, timeout=30)
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response Code: {data.get('c', 'N/A')}")
                    print(f"   Response Message: {data.get('m', 'N/A')}")
                    
                    if data.get('c') == '0':  # Success code
                        print("✅ Account information retrieved successfully!")
                        account_data = data.get('d')
                        if account_data:
                            print(f"   Account data: {json.dumps(account_data, indent=2)}")
                        return account_data
                    
                    elif data.get('c') == '100004':  # Timeout error
                        print("⏱️ Account API also timing out")
                        print("📡 This confirms it's a general Coohom server issue")
                        return None
                    
                    else:
                        print(f"❌ API Error (Code {data.get('c')}): {data.get('m', 'Unknown error')}")
                        print(f"Raw response: {json.dumps(data, indent=2)}")
                        return None
                
                except ValueError as e:
                    print(f"❌ Invalid JSON response: {str(e)}")
                    print(f"Raw response: {response.text[:200]}...")
                    return None
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response text: {response.text[:200]}...")
                
                # If 404, try alternative endpoint paths
                if response.status_code == 404:
                    print("🔄 Trying alternative endpoint...")
                    return self._try_alternative_account_endpoints()
                
                return None
                
        except requests.exceptions.Timeout:
            print("❌ Request timeout")
            return None
        except requests.exceptions.ConnectionError:
            print("❌ Connection error")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return None
    
    def _try_alternative_account_endpoints(self):
        """Try different possible account endpoint paths."""
        alternative_paths = [
            "/global/user/info",
            "/api/account/info", 
            "/account/info",
            "/user/info",
            "/global/account/detail"
        ]
        
        for path in alternative_paths:
            try:
                print(f"   Trying: {self.base_url}{path}")
                
                timestamp = str(int(time.time()))
                params = {
                    'appkey': self.app_key,
                    'timestamp': timestamp
                }
                
                signature = self.generate_signature(params)
                params['sign'] = signature
                
                url = f"{self.base_url}{path}"
                response = requests.get(url, params=params, timeout=15)
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Found working endpoint: {path}")
                    print(f"   Response Code: {data.get('c', 'N/A')}")
                    print(f"   Response Message: {data.get('m', 'N/A')}")
                    
                    if data.get('c') == '0':
                        account_data = data.get('d')
                        if account_data:
                            print(f"   Account data: {json.dumps(account_data, indent=2)}")
                        return account_data
                    else:
                        print(f"   API returned: {data}")
                        
            except Exception as e:
                print(f"   Error with {path}: {str(e)}")
                continue
        
        print("❌ No working account endpoints found")
        return None
    
    def search_enterprise_account(self):
        """
        Search Enterprise Account using API #7 from the documentation.
        This should return account information including appuid.
        
        Returns:
            dict: Enterprise account information or error details
        """
        print(f"\n🏢 Searching Enterprise Account (API #7)")
        
        try:
            timestamp = str(int(time.time()))
            params = {
                'appkey': self.app_key,  # Note: lowercase 'appkey'
                'timestamp': timestamp
            }
            
            signature = self.generate_signature(params)
            params['sign'] = signature
            
            # Try different possible enterprise account endpoints
            possible_endpoints = [
                "/global/enterprise/search",
                "/global/enterprise/account",
                "/enterprise/search",
                "/enterprise/account",
                "/global/account/enterprise",
                "/account/enterprise/search"
            ]
            
            for endpoint in possible_endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    print(f"   Trying: {url}")
                    print(f"   Timestamp: {timestamp}")
                    print(f"   Signature: {signature[:10]}...")
                    
                    response = requests.get(url, params=params, timeout=30)
                    
                    print(f"   Response Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            print(f"   Response Code: {data.get('c', 'N/A')}")
                            print(f"   Response Message: {data.get('m', 'N/A')}")
                            
                            if data.get('c') == '0':  # Success code
                                print(f"   ✅ Found working enterprise endpoint: {endpoint}")
                                print("✅ Enterprise account information retrieved successfully!")
                                account_data = data.get('d')
                                if account_data:
                                    print(f"   Enterprise data: {json.dumps(account_data, indent=2)}")
                                    
                                    # Look for appuid in the response
                                    if isinstance(account_data, dict):
                                        appuid = account_data.get('appuid') or account_data.get('app_uid') or account_data.get('uid')
                                        if appuid:
                                            print(f"   🎯 Found appuid: {appuid}")
                                        else:
                                            print("   ℹ️  No appuid found in response data")
                                    elif isinstance(account_data, list) and len(account_data) > 0:
                                        print(f"   📋 Found {len(account_data)} account(s)")
                                        for i, account in enumerate(account_data):
                                            print(f"   Account {i+1}: {json.dumps(account, indent=4)}")
                                            if isinstance(account, dict):
                                                appuid = account.get('appuid') or account.get('app_uid') or account.get('uid')
                                                if appuid:
                                                    print(f"   🎯 Found appuid in account {i+1}: {appuid}")
                                
                                return account_data
                            
                            elif data.get('c') == '100004':  # Timeout error
                                print(f"   ⏱️ Enterprise endpoint also timing out")
                                continue
                            
                            elif data.get('c') == '100003':  # Missing parameter
                                print(f"   ❓ Missing parameter: {data.get('m', 'Unknown')}")
                                continue
                            
                            else:
                                print(f"   ❌ API Error (Code {data.get('c')}): {data.get('m', 'Unknown error')}")
                                print(f"   Raw response: {json.dumps(data, indent=2)}")
                                continue
                        
                        except ValueError as e:
                            print(f"   ❌ Invalid JSON response: {str(e)}")
                            print(f"   Raw response: {response.text[:200]}...")
                            continue
                    else:
                        print(f"   ❌ HTTP Error: {response.status_code}")
                        if response.status_code != 404:  # Don't show 404 details
                            print(f"   Response text: {response.text[:100]}...")
                        continue
                        
                except requests.exceptions.Timeout:
                    print(f"   ❌ Request timeout for {endpoint}")
                    continue
                except requests.exceptions.ConnectionError:
                    print(f"   ❌ Connection error for {endpoint}")
                    continue
                except Exception as e:
                    print(f"   ❌ Error with {endpoint}: {str(e)}")
                    continue
            
            print("❌ No working enterprise account endpoints found")
            return None
                
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return None
    
    def find_appuid_various_methods(self):
        """
        Try various methods to find the appuid for this account.
        """
        print(f"\n🔍 Attempting to find appuid using various methods")
        
        # Method 1: Try user list/profile endpoints
        user_endpoints = [
            "/global/user/list",
            "/global/user/profile", 
            "/user/list",
            "/user/profile",
            "/global/account/users",
            "/account/users"
        ]
        
        print("\n📋 Method 1: Trying user/profile endpoints...")
        for endpoint in user_endpoints:
            try:
                timestamp = str(int(time.time()))
                params = {
                    'appkey': self.app_key,
                    'timestamp': timestamp
                }
                
                signature = self.generate_signature(params)
                params['sign'] = signature
                
                url = f"{self.base_url}{endpoint}"
                print(f"   Trying: {endpoint}")
                
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Working endpoint: {endpoint}")
                    print(f"   Response Code: {data.get('c', 'N/A')}")
                    print(f"   Response Message: {data.get('m', 'N/A')}")
                    
                    if data.get('c') == '0':
                        print(f"   Data: {json.dumps(data.get('d'), indent=2)}")
                        return data.get('d')
                    elif data.get('c') != '100004':  # Not timeout
                        print(f"   Response: {json.dumps(data, indent=2)}")
                elif response.status_code != 404:
                    print(f"   Status {response.status_code}: {response.text[:100]}...")
                    
            except Exception as e:
                continue
        
        # Method 2: Try different variations of the user info endpoint that worked before
        print("\n👤 Method 2: Trying user info variations without appuid...")
        info_endpoints = [
            "/global/user/current",
            "/global/user/me",
            "/user/current", 
            "/user/me",
            "/global/account/current",
            "/account/current"
        ]
        
        for endpoint in info_endpoints:
            try:
                timestamp = str(int(time.time()))
                params = {
                    'appkey': self.app_key,
                    'timestamp': timestamp
                }
                
                signature = self.generate_signature(params)
                params['sign'] = signature
                
                url = f"{self.base_url}{endpoint}"
                print(f"   Trying: {endpoint}")
                
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Working endpoint: {endpoint}")
                    print(f"   Response Code: {data.get('c', 'N/A')}")
                    print(f"   Response Message: {data.get('m', 'N/A')}")
                    
                    if data.get('c') == '0':
                        user_data = data.get('d')
                        print(f"   User data: {json.dumps(user_data, indent=2)}")
                        
                        # Look for appuid in the response
                        if isinstance(user_data, dict):
                            appuid = user_data.get('appuid') or user_data.get('app_uid') or user_data.get('uid')
                            if appuid:
                                print(f"   🎯 Found appuid: {appuid}")
                                return {'appuid': appuid, 'data': user_data}
                        return user_data
                    elif data.get('c') != '100004':  # Not timeout
                        print(f"   Response: {json.dumps(data, indent=2)}")
                elif response.status_code != 404:
                    print(f"   Status {response.status_code}: {response.text[:100]}...")
                    
            except Exception as e:
                continue
        
        # Method 3: Try common appuid values based on appkey
        print("\n🔢 Method 3: Testing with potential appuid patterns...")
        
        # Common patterns: use appkey as appuid, or variations
        potential_appuids = [
            self.app_key,  # Sometimes appuid = appkey
            self.app_key.lower(),
            self.app_key.upper(),
            "1",  # Default/admin user
            "admin",
            "root"
        ]
        
        for test_appuid in potential_appuids:
            try:
                print(f"   Testing appuid: {test_appuid}")
                
                timestamp = str(int(time.time()))
                params = {
                    'appkey': self.app_key,
                    'timestamp': timestamp,
                    'appuid': test_appuid
                }
                
                signature = self.generate_signature(params)
                params['sign'] = signature
                
                url = f"{self.base_url}/global/user/info"
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   Response Code: {data.get('c', 'N/A')}")
                    print(f"   Response Message: {data.get('m', 'N/A')}")
                    
                    if data.get('c') == '0':
                        print(f"   🎯 SUCCESS! Working appuid: {test_appuid}")
                        user_data = data.get('d')
                        if user_data:
                            print(f"   User data: {json.dumps(user_data, indent=2)}")
                        return {'appuid': test_appuid, 'data': user_data}
                    elif data.get('c') != '100003':  # Not "missing parameter"
                        print(f"   Different error: {data}")
                        
            except Exception as e:
                continue
        
        print("\n❌ Could not find appuid using any method")
        print("💡 Suggestions:")
        print("   - Check your Coohom developer account for a User ID or App UID")
        print("   - Contact Coohom support for your account's appuid")
        print("   - Check if your account needs user registration first")
        
        return None


def load_credentials():
    """
    Load API credentials from credentials.txt file.
    
    Returns:
        dict or None: Credentials dictionary or None if file not found
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        creds_path = os.path.join(script_dir, 'credentials.txt')
        
        with open(creds_path, 'r') as f:
            creds = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    creds[key] = value
            return creds
    except FileNotFoundError:
        print("❌ credentials.txt file not found!")
        return None


def test_full_upload_workflow(file_path=None):
    """
    Test the complete upload workflow for a 3D file.
    
    Args:
        file_path (str): Path to the file to upload. If None, uses the sample 3D file.
    """
    print("🚀 Starting Coohom API Upload Test")
    print("=" * 50)
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        print("❌ Failed to load credentials")
        return
    
    app_key = creds.get('appKey')
    app_secret = creds.get('appSecret')
    
    if not app_key or not app_secret:
        print("❌ Missing appKey or appSecret in credentials.txt")
        return
    
    # Use sample file if no file specified
    if file_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, '3D_sample_file.obj')
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    filename = os.path.basename(file_path)
    print(f"📁 Test file: {filename}")
    print(f"📁 File path: {file_path}")
    print(f"📁 File size: {os.path.getsize(file_path)} bytes")
    
    # Initialize API tester
    api_tester = CoohomAPITester(app_key, app_secret)
    
    # Step 1: Get STS credentials
    sts_data = api_tester.get_sts_credentials(filename)
    if not sts_data:
        print("❌ Failed to get STS credentials")
        return
    
    print(f"\n📋 STS Data received:")
    print(f"   Upload Task ID: {sts_data.get('uploadTaskId', 'N/A')}")
    print(f"   Bucket: {sts_data.get('bucket', 'N/A')}")
    print(f"   Region: {sts_data.get('region', 'N/A')}")
    
    # Step 2: Upload to OSS
    upload_result = api_tester.upload_to_oss(file_path, sts_data)
    if not upload_result.get('success'):
        print(f"❌ Failed to upload to OSS: {upload_result.get('error')}")
        return
    
    upload_task_id = upload_result['upload_task_id']
    
    # Step 3: Check upload status (with retries)
    print(f"\n⏳ Waiting for file processing...")
    max_status_checks = 10
    check_interval = 10  # seconds
    
    for i in range(max_status_checks):
        time.sleep(check_interval)
        
        status_result = api_tester.check_upload_status(upload_task_id)
        if 'error' not in status_result:
            print(f"   Check {i+1}/{max_status_checks}: Processing...")
            # Check if processing is complete (this depends on the actual response format)
            # You may need to adjust this based on the actual API response
            if status_result.get('status') == 'completed':
                print("✅ File processing completed!")
                break
        else:
            print(f"❌ Status check failed: {status_result['error']}")
            break
    
    # Step 4: Submit parsed model (if applicable for your use case)
    # Note: This step might only be needed for certain file types or workflows
    submit_result = api_tester.submit_parsed_model(upload_task_id)
    if 'error' not in submit_result:
        print("✅ Model submission completed!")
    else:
        print(f"❌ Model submission failed: {submit_result['error']}")
    
    print("\n" + "=" * 50)
    print("🎉 Upload test completed!")
    print(f"📋 Upload Task ID: {upload_task_id}")


def test_api_authentication():
    """
    Test API authentication by making a simple request.
    """
    print("🔐 Testing API Authentication")
    print("=" * 30)
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        return
    
    app_key = creds.get('appKey')
    app_secret = creds.get('appSecret')
    
    if not app_key or not app_secret:
        print("❌ Missing credentials")
        return
    
    # Initialize API tester
    api_tester = CoohomAPITester(app_key, app_secret)
    
    # Test with a simple filename
    test_filename = "test.obj"
    sts_data = api_tester.get_sts_credentials(test_filename)
    
    if sts_data:
        print("✅ Authentication successful!")
        print("✅ API credentials are working correctly!")
    else:
        print("❌ Authentication failed!")


def test_account_api():
    """
    Test API #6 - Account Information endpoint.
    """
    print("👤 Testing Account Information API (#6)")
    print("=" * 40)
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        return
    
    app_key = creds.get('appKey')
    app_secret = creds.get('appSecret')
    
    if not app_key or not app_secret:
        print("❌ Missing credentials")
        return
    
    # Initialize API tester
    api_tester = CoohomAPITester(app_key, app_secret)
    
    # Test account information endpoint
    account_data = api_tester.get_account_information()
    
    if account_data:
        print("\n✅ Account API working!")
        print("✅ Successfully retrieved account information!")
    else:
        print("\n📋 Account API test completed")
        print("ℹ️  This helps us understand if timeouts are affecting all endpoints")


def test_enterprise_account_api():
    """
    Test API #7 - Search Enterprise Account endpoint to find appuid.
    """
    print("🏢 Testing Enterprise Account Search API (#7)")
    print("=" * 50)
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        return
    
    app_key = creds.get('appKey')
    app_secret = creds.get('appSecret')
    
    if not app_key or not app_secret:
        print("❌ Missing credentials")
        return
    
    # Initialize API tester
    api_tester = CoohomAPITester(app_key, app_secret)
    
    # Test enterprise account search endpoint
    print("🔍 Searching for enterprise account and appuid...")
    enterprise_data = api_tester.search_enterprise_account()
    
    if enterprise_data:
        print("\n✅ Enterprise Account API working!")
        print("✅ Successfully retrieved enterprise account information!")
    else:
        print("\n📋 Enterprise Account API test completed")
        print("ℹ️  This helps us find the appuid needed for other endpoints")


def test_find_appuid():
    """
    Try various methods to find the appuid for this account.
    """
    print("🔍 Finding AppUID using Multiple Methods")
    print("=" * 45)
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        return
    
    app_key = creds.get('appKey')
    app_secret = creds.get('appSecret')
    
    if not app_key or not app_secret:
        print("❌ Missing credentials")
        return
    
    # Initialize API tester
    api_tester = CoohomAPITester(app_key, app_secret)
    
    # Try various methods to find appuid
    result = api_tester.find_appuid_various_methods()
    
    if result:
        if isinstance(result, dict) and 'appuid' in result:
            appuid = result['appuid']
            print(f"\n🎉 SUCCESS! Found working appuid: {appuid}")
            print("\n💾 You can now use this appuid in other API calls!")
            print(f"   Add this to your credentials: appuid={appuid}")
        else:
            print("\n✅ Found some user data!")
            print("📋 Check the output above for any uid/appuid values")
    else:
        print("\n📋 AppUID search completed")
        print("💡 Check your Coohom developer account for user/app information")


def test_api_endpoints():
    """
    Test different API endpoints to check which ones are working.
    """
    print("🔍 Testing API Endpoints")
    print("=" * 30)
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        return
    
    app_key = creds.get('appKey')
    app_secret = creds.get('appSecret')
    
    if not app_key or not app_secret:
        print("❌ Missing credentials")
        return
    
    api_tester = CoohomAPITester(app_key, app_secret)
    
    print("📡 Testing connectivity to Coohom API...")
    
    # Test basic connectivity
    try:
        response = requests.get("https://api.coohom.com", timeout=10)
        print(f"✅ Base API reachable - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Base API unreachable: {str(e)}")
    
    # Test with different file types
    test_files = ["test.obj", "test.fbx", "test.3ds", "test.zip"]
    
    for test_file in test_files:
        print(f"\n🧪 Testing with {test_file}:")
        try:
            # Just test the first attempt, don't retry
            encoded_filename = quote(test_file)
            timestamp = str(int(time.time()))
            params = {
                'appkey': app_key,
                'timestamp': timestamp,
                'file_name': encoded_filename
            }
            
            signature = api_tester.generate_signature(params)
            params['sign'] = signature
            url = f"{api_tester.base_url}/global/commodity/upload/sts"
            
            response = requests.get(url, params=params, timeout=15)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Code: {data.get('c', 'N/A')}")
                print(f"   Message: {data.get('m', 'N/A')}")
                
                if data.get('c') == '0':
                    print(f"   ✅ Success! STS credentials obtained")
                    break
                elif data.get('c') == '100004':
                    print(f"   ⏱️ Timeout (auth working)")
                else:
                    print(f"   ❓ Other response")
            else:
                print(f"   ❌ HTTP Error")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        time.sleep(1)  # Small delay between tests


def debug_request_details():
    """
    Show detailed request information for debugging.
    """
    print("🔬 Debug Request Details")
    print("=" * 30)
    
    creds = load_credentials()
    if not creds:
        return
    
    app_key = creds.get('appKey')
    app_secret = creds.get('appSecret')
    
    print(f"🔑 Credentials:")
    print(f"   App Key: {app_key}")
    print(f"   App Secret: {app_secret[:10]}... (truncated)")
    
    # Show signature generation process
    test_filename = "3D_sample_file.obj"
    encoded_filename = quote(test_filename)
    timestamp = str(int(time.time()))
    
    params = {
        'appkey': app_key,
        'timestamp': timestamp,
        'file_name': encoded_filename
    }
    
    print(f"\n📋 Request Parameters:")
    for key, value in params.items():
        print(f"   {key}: {value}")
    
    # Show signature generation
    api_tester = CoohomAPITester(app_key, app_secret)
    signature = api_tester.generate_signature(params)
    
    print(f"\n🔏 Signature Generation:")
    sorted_params = sorted(params.items())
    param_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
    sign_string = f"{param_string}&{app_secret}"
    
    print(f"   Param String: {param_string}")
    print(f"   Sign String: {sign_string[:50]}... (truncated)")
    print(f"   MD5 Hash: {signature}")
    
    print(f"\n🌐 Final Request URL:")
    params['sign'] = signature
    url = f"https://api.coohom.com/global/commodity/upload/sts"
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    print(f"   {url}?{query_string}")


if __name__ == "__main__":
    import sys
    
    print("🏠 Coohom API Request Tester")
    print("=" * 40)
    print()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--auth-test":
            test_api_authentication()
        elif sys.argv[1] == "--upload":
            file_path = sys.argv[2] if len(sys.argv) > 2 else None
            test_full_upload_workflow(file_path)
        elif sys.argv[1] == "--endpoints":
            test_api_endpoints()
        elif sys.argv[1] == "--debug":
            debug_request_details()
        elif sys.argv[1] == "--account":
            test_account_api()
        elif sys.argv[1] == "--enterprise":
            test_enterprise_account_api()
        elif sys.argv[1] == "--find-appuid":
            test_find_appuid()
        else:
            print("Usage:")
            print("  python3 test_coohom_requests.py --auth-test     # Test authentication only")
            print("  python3 test_coohom_requests.py --upload [file] # Test full upload workflow")
            print("  python3 test_coohom_requests.py --endpoints     # Test different API endpoints")
            print("  python3 test_coohom_requests.py --debug         # Show debug information")
            print("  python3 test_coohom_requests.py --account       # Test account info API (#6)")
            print("  python3 test_coohom_requests.py --enterprise    # Test enterprise account API (#7)")
            print("  python3 test_coohom_requests.py --find-appuid   # Try to find your appuid")
    else:
        print("Choose an option:")
        print("1. Test authentication only")
        print("2. Test full upload workflow with sample file")
        print("3. Test full upload workflow with custom file")
        print("4. Test API endpoints")
        print("5. Show debug information")
        print("6. Test account info API (#6)")
        print("7. Test enterprise account API (#7)")
        print("8. Find appuid using multiple methods")
        print("9. Retry upload (sometimes Coohom servers recover)")
        
        choice = input("\nEnter choice (1-9): ").strip()
        
        if choice == "1":
            test_api_authentication()
        elif choice == "2":
            test_full_upload_workflow()
        elif choice == "3":
            custom_file = input("Enter file path: ").strip()
            test_full_upload_workflow(custom_file)
        elif choice == "4":
            test_api_endpoints()
        elif choice == "5":
            debug_request_details()
        elif choice == "6":
            test_account_api()
        elif choice == "7":
            test_enterprise_account_api()
        elif choice == "8":
            test_find_appuid()
        elif choice == "9":
            print("🔄 Retrying upload - sometimes Coohom servers recover after a few minutes...")
            test_full_upload_workflow()
        else:
            print("Invalid choice!")

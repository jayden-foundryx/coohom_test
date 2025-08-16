"""
Coohom API client module for handling uploads and API interactions.
"""
import requests
import hashlib
import time
from urllib.parse import quote
import streamlit as st


class CoohomUploader:
    """
    Client for interacting with Coohom's API for 3D model uploads.
    """
    
    def __init__(self, app_key, app_secret):
        """
        Initialize the Coohom uploader with API credentials.
        
        Args:
            app_key (str): Coohom API key
            app_secret (str): Coohom API secret
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = "https://api.coohom.com"
    
    def generate_signature(self, params):
        """
        Generate signature for API authentication following Kujiale/Coohom pattern.
        
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
    
    def get_sts_credentials(self, filename):
        """
        Get STS credentials for file upload from Coohom API.
        
        Args:
            filename (str): Name of the file to upload
            
        Returns:
            dict or None: STS credentials if successful, None otherwise
        """
        try:
            # URL encode the filename
            encoded_filename = quote(filename)
            
            # Prepare parameters following Kujiale/Coohom pattern
            timestamp = str(int(time.time()))
            params = {
                'appkey': self.app_key,  # Note: lowercase 'appkey'
                'timestamp': timestamp,
                'file_name': encoded_filename
            }
            
            # Generate signature
            signature = self.generate_signature(params)
            params['sign'] = signature
            
            # Make API request using correct endpoint from documentation  
            url = f"{self.base_url}/global/commodity/upload/sts"
            
            # Debug info
            st.info(f"🔍 **Debug Info:**")
            st.write(f"- API URL: `{url}`")
            st.write(f"- App Key: `{self.app_key}`")
            st.write(f"- Filename: `{filename}` → `{encoded_filename}`")
            st.write(f"- Timestamp: `{timestamp}`")
            st.write(f"- Signature: `{signature[:10]}...`")
            
            # Send as GET request with query parameters only (as per documentation)
            response = requests.get(url, params=params, timeout=30)
            
            st.write(f"- Response Status: `{response.status_code}`")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    st.write(f"- Response Code: `{data.get('c', 'N/A')}`")
                    st.write(f"- Response Message: `{data.get('m', 'N/A')}`")
                    
                    if data.get('c') == '0':  # Success code
                        st.success("✅ API call successful!")
                        return data.get('d')
                    elif data.get('c') == '100004':  # Timeout error - authentication works but API has issues
                        st.warning(f"⏱️ API Timeout: {data.get('m', 'Request timed out')}")
                        st.success("✅ Good news: Your authentication is working correctly!")
                        st.info("📡 The Coohom API servers are experiencing high load or timeouts.")
                        st.info("🔄 **Solution**: Try uploading again in a few minutes. This is a temporary server issue.")
                        
                        # Show what would have been returned for demo purposes
                        st.info("💡 **For demonstration**: In production, you would retry this request automatically.")
                        return None
                    else:
                        st.error(f"❌ API Error (Code {data.get('c')}): {data.get('m', 'Unknown error')}")
                        
                        # Show raw response for debugging
                        with st.expander("🔍 Raw API Response"):
                            st.json(data)
                        return None
                except ValueError as e:
                    st.error(f"❌ Invalid JSON response: {str(e)}")
                    st.write(f"Raw response: `{response.text[:200]}...`")
                    return None
            else:
                st.error(f"❌ HTTP Error: {response.status_code}")
                st.write(f"Response text: `{response.text[:200]}...`")
                return None
                
        except requests.exceptions.Timeout:
            st.error("❌ Request timeout - API server may be slow or unavailable")
            return None
        except requests.exceptions.ConnectionError:
            st.error("❌ Connection error - Check your internet connection")
            return None
        except Exception as e:
            st.error(f"❌ Unexpected error getting STS credentials: {str(e)}")
            import traceback
            st.error(f"Stack trace: {traceback.format_exc()}")
            return None
    
    def upload_to_oss(self, file_data, sts_data, original_filename):
        """
        Upload file to Alibaba Cloud OSS using STS credentials.
        
        Args:
            file_data (bytes): File data to upload
            sts_data (dict): STS credentials from get_sts_credentials
            original_filename (str): Original filename
            
        Returns:
            dict: Upload result with success status and details
        """
        try:
            import oss2
            
            # Extract STS credentials
            access_key_id = sts_data['accessKeyId']
            access_key_secret = sts_data['accessKeySecret']
            security_token = sts_data['securityToken']
            bucket_name = sts_data['bucket']
            region = sts_data['region']
            file_path = sts_data['filePath']
            
            # Create OSS client with STS token
            auth = oss2.StsAuth(access_key_id, access_key_secret, security_token)
            endpoint = f"https://oss-{region}.aliyuncs.com"
            bucket = oss2.Bucket(auth, endpoint, bucket_name)
            
            # Upload file
            result = bucket.put_object(file_path, file_data)
            
            if result.status == 200:
                return {
                    'success': True,
                    'upload_task_id': sts_data['uploadTaskId'],
                    'file_path': file_path
                }
            else:
                return {'success': False, 'error': f"Upload failed with status: {result.status}"}
                
        except ImportError:
            st.error("oss2 library not installed. Please install it with: pip install oss2")
            return {'success': False, 'error': 'Missing oss2 library'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_upload_status(self, upload_task_id):
        """
        Check the status of an upload task.
        
        Args:
            upload_task_id (str): Task ID returned from STS credentials
            
        Returns:
            dict: Status information or error details
        """
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
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('c') == '0':
                    return data.get('d')
                else:
                    return {'error': data.get('m', 'Unknown error')}
            else:
                return {'error': f"HTTP Error: {response.status_code}"}
                
        except Exception as e:
            return {'error': str(e)}

    def submit_parsed_model(self, upload_task_id):
        """
        Submit parsed ZIP files for Coohom models (Step 5 of upload process).
        
        Args:
            upload_task_id (str): Task ID from upload
            
        Returns:
            dict: Submission result
        """
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
            response = requests.post(url, data=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('c') == '0':
                    return data.get('d')
                else:
                    return {'error': data.get('m', 'Unknown error')}
            else:
                return {'error': f"HTTP Error: {response.status_code}"}
                
        except Exception as e:
            return {'error': str(e)}


def load_credentials():
    """
    Load API credentials from credentials.txt file.
    
    Returns:
        dict or None: Credentials dictionary or None if file not found
    """
    try:
        with open('credentials.txt', 'r') as f:
            creds = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    creds[key] = value
            return creds
    except FileNotFoundError:
        st.error("credentials.txt file not found!")
        return None

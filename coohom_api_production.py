"""
Production version of Coohom API client with cleaner error handling and retry logic.
"""
import requests
import hashlib
import time
from urllib.parse import quote
import streamlit as st


class CoohomUploader:
    """
    Production Coohom API client with retry logic and cleaner error handling.
    """
    
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = "https://api.coohom.com"
    
    def generate_signature(self, params):
        """Generate signature for API authentication."""
        sign_string = f"{params['appsecret']}{params['appkey']}{params['timestamp']}"
        signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
        return signature
    
    def get_sts_credentials(self, filename, max_retries=3, show_debug=False):
        """
        Get STS credentials with retry logic.
        
        Args:
            filename (str): Name of the file to upload
            max_retries (int): Maximum number of retry attempts
            show_debug (bool): Whether to show debug information
        """
        for attempt in range(max_retries):
            try:
                encoded_filename = quote(filename)
                timestamp = str(int(time.time()) * 1000)
                params = {
                    'appkey': self.app_key,
                    'timestamp': timestamp,
                    'appsecret': self.app_secret,
                    'file_name': encoded_filename
                }
                
                signature = self.generate_signature(params)
                params['sign'] = signature
                url = f"{self.base_url}/global/commodity/upload/sts"
                
                if show_debug:
                    st.write(f"🔍 Attempt {attempt + 1}/{max_retries}")
                    st.write(f"- URL: `{url}`")
                    st.write(f"- Filename: `{filename}`")
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('c') == '0':  # Success
                        if show_debug:
                            st.success("✅ API call successful!")
                        return data.get('d')
                    
                    elif data.get('c') == '100004':  # Timeout - retry
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2  # Exponential backoff
                            if show_debug:
                                st.warning(f"⏱️ Timeout on attempt {attempt + 1}. Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        else:
                            st.error("⏱️ API Timeout after all retry attempts")
                            st.error("📡 Coohom servers are experiencing high load. Please try again later.")
                            if show_debug:
                                with st.expander("🔍 API Response"):
                                    st.json(data)
                            return None
                    
                    else:  # Other API error
                        st.error(f"❌ API Error (Code {data.get('c')}): {data.get('m', 'Unknown error')}")
                        if show_debug:
                            with st.expander("🔍 API Response"):
                                st.json(data)
                        return None
                
                else:  # HTTP error
                    st.error(f"❌ HTTP Error: {response.status_code}")
                    if show_debug:
                        st.error(f"Response content: {response.text[:500]}...")
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    st.warning(f"⏱️ Request timeout. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    st.error("❌ Request timeout after all attempts")
                    return None
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection error - Check your internet connection")
                return None
                
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                return None
        
        return None
    
    def check_upload_status(self, upload_task_id):
        """Check the status of an upload task."""
        try:
            timestamp = str(int(time.time()) * 1000)
            params = {
                'appkey': self.app_key,
                'timestamp': timestamp,
                'upload_task_id': upload_task_id
            }
            
            signature = self.generate_signature(params)
            params['sign'] = signature
            
            url = f"{self.base_url}/global/commodity/upload/status"
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('c') == '0':
                    return data.get('d')
                else:
                    st.error(f"❌ Status Check Error (Code {data.get('c')}): {data.get('m', 'Unknown error')}")
                    with st.expander("🔍 Status API Response"):
                        st.json(data)
                    return {'error': data.get('m', 'Unknown error')}
            else:
                st.error(f"❌ Status Check HTTP Error: {response.status_code}")
                return {'error': f"HTTP Error: {response.status_code}"}
                
        except Exception as e:
            return {'error': str(e)}


def load_credentials():
    """Load API credentials from credentials.txt file."""
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

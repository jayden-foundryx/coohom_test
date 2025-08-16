"""
Production version of Coohom API client with cleaner error handling and retry logic.
"""
import requests
import hashlib
import time
from urllib.parse import quote
import streamlit as st
import json


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
        sign_string = f"{self.app_secret}{params['appkey']}{params['timestamp']}"
        signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
        return signature
    
    def get_sts_credentials(self, filename, max_retries=3, show_debug=False, timeout=30):
        """
        Get STS credentials with retry logic.
        
        Args:
            filename (str): Name of the file to upload
            max_retries (int): Maximum number of retry attempts
            show_debug (bool): Whether to show debug information
            timeout (int): Request timeout in seconds
        """
        for attempt in range(max_retries):
            try:
                encoded_filename = quote(filename)
                timestamp = str(int(time.time() * 1000))
                params = {
                    'appkey': self.app_key,
                    'timestamp': timestamp,
                    'file_name': encoded_filename
                }
                
                signature = self.generate_signature(params)
                params['sign'] = signature
                url = f"{self.base_url}/global/commodity/upload/sts"
                
                if show_debug:
                    st.write(f"🔍 Attempt {attempt + 1}/{max_retries}")
                    st.write(f"- URL: `{url}`")
                    st.write(f"- Filename: `{filename}`")
                    st.write(f"- Timeout: `{timeout}s`")
                
                # Use the timeout parameter
                response = requests.get(url, params=params, timeout=timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('c') == '0':  # Success
                        if show_debug:
                            st.success("✅ API call successful!")
                        result = data.get('d')
                        # Ensure we always return a dictionary
                        if result is None:
                            return {'success': True, 'data': None, 'message': 'STS credentials obtained successfully'}
                        elif isinstance(result, dict):
                            return result
                        else:
                            return {'success': True, 'data': result, 'message': 'STS credentials obtained successfully'}
                    
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
                            # Return structured error response for UI display
                            return {
                                'error': 'API Timeout after all retry attempts - Coohom servers are experiencing high load',
                                'error_code': '100004',
                                'full_response': data,
                                'endpoint': 'sts_credentials',
                                'retry_attempts': max_retries,
                                'request_data': {
                                    'url': url,
                                    'params': params,
                                    'filename': filename,
                                    'timestamp': timestamp
                                }
                            }
                    
                    else:  # Other API error
                        st.error(f"❌ API Error (Code {data.get('c')}): {data.get('m', 'Unknown error')}")
                        if show_debug:
                            with st.expander("🔍 API Response"):
                                st.json(data)
                        # Return structured error response for UI display
                        return {
                            'error': data.get('m', 'Unknown error'),
                            'error_code': data.get('c'),
                            'full_response': data,
                            'endpoint': 'sts_credentials',
                            'request_data': {
                                'url': url,
                                'params': params,
                                'filename': filename,
                                'timestamp': timestamp
                            }
                        }
                
                else:  # HTTP error
                    st.error(f"❌ HTTP Error: {response.status_code}")
                    if show_debug:
                        st.error(f"Response content: {response.text[:500]}...")
                    # Return structured error response for UI display
                    return {
                        'error': f"HTTP Error: {response.status_code}",
                        'error_code': response.status_code,
                        'response_text': response.text[:500],
                        'endpoint': 'sts_credentials',
                        'request_data': {
                            'url': url,
                            'params': params,
                            'filename': filename,
                            'timestamp': timestamp
                        }
                    }
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    st.warning(f"⏱️ Request timeout. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    st.error("❌ Request timeout after all attempts")
                    # Return structured error response for UI display
                    return {
                        'error': 'Request timeout after all attempts',
                        'error_code': 'TIMEOUT',
                        'endpoint': 'sts_credentials',
                        'request_data': {
                            'url': url,
                            'params': params,
                            'filename': filename,
                            'timestamp': timestamp
                        },
                        'retry_attempts': max_retries
                    }
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection error - Check your internet connection")
                # Return structured error response for UI display
                return {
                    'error': 'Connection error - Check your internet connection',
                    'error_code': 'CONNECTION_ERROR',
                    'endpoint': 'sts_credentials',
                    'request_data': {
                        'url': url,
                        'params': params,
                        'filename': filename,
                        'timestamp': timestamp
                    }
                }
                
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                # Return structured error response for UI display
                return {
                    'error': str(e),
                    'error_code': 'UNEXPECTED_ERROR',
                    'endpoint': 'sts_credentials',
                    'request_data': {
                        'url': url,
                        'params': params,
                        'filename': filename,
                        'timestamp': timestamp
                    }
                }
        
        return None
    
    def check_upload_status(self, upload_task_id):
        """Check the status of an upload task."""
        try:
            timestamp = str(int(time.time() * 1000))
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
                    result = data.get('d')
                    # Ensure we always return a dictionary
                    if result is None:
                        return {'success': True, 'data': None, 'message': 'Upload status checked successfully'}
                    elif isinstance(result, dict):
                        return result
                    else:
                        return {'success': True, 'data': result, 'message': 'Upload status checked successfully'}
                else:
                    st.error(f"❌ Status Check Error (Code {data.get('c')}): {data.get('m', 'Unknown error')}")
                    with st.expander("🔍 Status API Response"):
                        st.json(data)
                    # Return structured error response for UI display
                    return {
                        'error': data.get('m', 'Unknown error'),
                        'error_code': data.get('c'),
                        'full_response': data,
                        'endpoint': 'upload_status',
                        'task_id': upload_task_id,
                        'request_data': {
                            'url': url,
                            'params': params,
                            'timestamp': timestamp
                        }
                    }
            else:
                st.error(f"❌ Status Check HTTP Error: {response.status_code}")
                # Return structured error response for UI display
                return {
                    'error': f"HTTP Error: {response.status_code}",
                    'error_code': response.status_code,
                    'response_text': response.text[:500],
                    'endpoint': 'upload_status',
                    'task_id': upload_task_id,
                    'request_data': {
                        'url': url,
                        'params': params,
                        'timestamp': timestamp
                    }
                }
                
        except Exception as e:
            # Return structured error response for UI display
            return {
                'error': str(e),
                'error_code': 'EXCEPTION',
                'endpoint': 'upload_status',
                'task_id': upload_task_id,
                'request_data': {
                    'url': url,
                    'params': params,
                    'timestamp': timestamp
                }
            }

    def poll_upload_status_until_complete(self, upload_task_id, max_attempts=5, interval_minutes=2, show_debug=False):
        """
        Poll upload status until it reaches a terminal state (2, 4, 5, or 6).
        
        Args:
            upload_task_id (str): The upload task ID to monitor
            max_attempts (int): Maximum number of status checks (default: 5)
            interval_minutes (int): Minutes to wait between checks (default: 2)
            show_debug (bool): Whether to show debug information
            
        Returns:
            dict: Final status result with polling details
        """
        if show_debug:
            st.info(f"🔄 Starting status polling for task: {upload_task_id}")
            st.info(f"⏱️ Will check every {interval_minutes} minutes, up to {max_attempts} times")
        
        terminal_statuses = [2, 4, 5, 6]  # Status codes that indicate completion (including parsing failures)
        status_history = []
        
        for attempt in range(1, max_attempts + 1):
            if show_debug:
                st.write(f"🔍 Check {attempt}/{max_attempts} - Checking status...")
            
            # Check current status
            status_result = self.check_upload_status(upload_task_id)
            
            if 'error' in status_result:
                if show_debug:
                    st.error(f"❌ Status check {attempt} failed: {status_result['error']}")
                status_history.append({
                    'attempt': attempt,
                    'timestamp': time.time(),
                    'error': status_result['error']
                })
                
                # If this is the last attempt, return the error
                if attempt == max_attempts:
                    return {
                        'success': False,
                        'error': f"Failed to check status after {max_attempts} attempts",
                        'status_history': status_history,
                        'final_attempt': attempt,
                        'task_id': upload_task_id
                    }
                
                # Wait before next attempt
                if attempt < max_attempts:
                    wait_seconds = interval_minutes * 60
                    if show_debug:
                        st.info(f"⏳ Waiting {interval_minutes} minutes before next check...")
                    time.sleep(wait_seconds)
                continue
            
            # Extract status from the response
            current_status = None
            if isinstance(status_result, dict):
                # Check if status is directly in status_result (from check_upload_status)
                if 'status' in status_result:
                    current_status = status_result.get('status')
                # Check if status is in data field (from other methods)
                elif 'data' in status_result:
                    # Handle different response structures
                    data = status_result['data']
                    if isinstance(data, dict):
                        current_status = data.get('status')
                    elif isinstance(data, list) and len(data) > 0:
                        current_status = data[0].get('status')
            
            # If we can't determine status, log and continue
            if current_status is None:
                if show_debug:
                    st.warning(f"⚠️ Could not determine status from response: {status_result}")
                status_history.append({
                    'attempt': attempt,
                    'timestamp': time.time(),
                    'status': 'unknown',
                    'response': status_result
                })
                
                # If this is the last attempt, return with unknown status
                if attempt == max_attempts:
                    return {
                        'success': True,
                        'status': 'unknown',
                        'message': f"Status polling completed after {max_attempts} attempts",
                        'status_history': status_history,
                        'final_attempt': attempt,
                        'task_id': upload_task_id,
                        'final_response': status_result
                    }
                
                # Wait before next attempt
                if attempt < max_attempts:
                    wait_seconds = interval_minutes * 60
                    if show_debug:
                        st.info(f"⏳ Waiting {interval_minutes} minutes before next check...")
                    time.sleep(wait_seconds)
                continue
            
            # Convert status to int if it's a string
            try:
                current_status = int(current_status)
            except (ValueError, TypeError):
                current_status = None
            
            if current_status is None:
                if show_debug:
                    st.warning(f"⚠️ Invalid status value: {current_status}")
                status_history.append({
                    'attempt': attempt,
                    'timestamp': time.time(),
                    'status': 'invalid',
                    'response': status_result
                })
                
                # If this is the last attempt, return with invalid status
                if attempt == max_attempts:
                    return {
                        'success': True,
                        'status': 'invalid',
                        'message': f"Status polling completed after {max_attempts} attempts",
                        'status_history': status_history,
                        'final_attempt': attempt,
                        'task_id': upload_task_id,
                        'final_response': status_result
                    }
                
                # Wait before next attempt
                if attempt < max_attempts:
                    wait_seconds = interval_minutes * 60
                    if show_debug:
                        st.info(f"⏳ Waiting {interval_minutes} minutes before next check...")
                    time.sleep(wait_seconds)
                continue
            
            # Record this status check
            status_history.append({
                'attempt': attempt,
                'timestamp': time.time(),
                'status': current_status,
                'response': status_result
            })
            
            if show_debug:
                from config import UPLOAD_STATUS_CODES
                status_desc = UPLOAD_STATUS_CODES.get(current_status, f"Unknown status: {current_status}")
                st.write(f"📊 Current status: {current_status} - {status_desc}")
            
            # Check if we've reached a terminal status
            if current_status in terminal_statuses:
                if show_debug:
                    if current_status == 2:
                        st.error(f"❌ Parsing failed! Status: {current_status}")
                    elif current_status == 4:
                        st.success(f"🎉 Upload completed successfully! Status: {current_status}")
                    elif current_status == 5:
                        st.error(f"❌ Upload failed! Status: {current_status}")
                    elif current_status == 6:
                        st.info(f"📊 Upload analyzed offline. Status: {current_status}")
                
                return {
                    'success': True,
                    'status': current_status,
                    'message': f"Upload reached terminal status {current_status} after {attempt} checks",
                    'status_history': status_history,
                    'final_attempt': attempt,
                    'task_id': upload_task_id,
                    'final_response': status_result,
                    'completed_early': True
                }
            
            # If not terminal and not the last attempt, wait before next check
            if attempt < max_attempts:
                wait_seconds = interval_minutes * 60
                if show_debug:
                    st.info(f"⏳ Status {current_status} is not terminal. Waiting {interval_minutes} minutes before next check...")
                time.sleep(wait_seconds)
        
        # If we've exhausted all attempts without reaching terminal status
        if show_debug:
            st.warning(f"⚠️ Status polling completed after {max_attempts} attempts without reaching terminal status")
        
        return {
            'success': True,
            'status': current_status,
            'message': f"Status polling completed after {max_attempts} attempts without reaching terminal status",
            'status_history': status_history,
            'final_attempt': max_attempts,
            'task_id': upload_task_id,
            'final_response': status_result,
            'completed_early': False
        }

    def upload_to_oss(self, file_data, sts_data, original_filename):
        """
        Upload file to Alibaba Cloud OSS using STS credentials (Endpoint #2).
        
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
            
            # Create OSS auth and bucket
            auth = oss2.StsAuth(access_key_id, access_key_secret, security_token)
            endpoint = f"https://oss-{region}.aliyuncs.com"
            bucket = oss2.Bucket(auth, endpoint, bucket_name)
            
            # Upload file
            result = bucket.put_object(file_path, file_data)
            
            if result.status == 200:
                return {
                    'success': True,
                    'message': 'File uploaded successfully to OSS',
                    'oss_path': file_path,
                    'etag': result.etag
                }
            else:
                return {
                    'success': False,
                    'error': f"Upload failed with status: {result.status}",
                    'request_data': {
                        'bucket': bucket_name,
                        'region': region,
                        'file_path': file_path,
                        'filename': original_filename,
                        'file_size': len(file_data)
                    }
                }
                
        except ImportError:
            st.error("oss2 library not installed. Please install it with: pip install oss2")
            return {
                'success': False, 
                'error': 'Missing oss2 library',
                'request_data': {
                    'filename': original_filename,
                    'file_size': len(file_data),
                    'required_library': 'oss2'
                }
            }
        except Exception as e:
            return {
                'success': False, 
                'error': str(e),
                'request_data': {
                    'filename': original_filename,
                    'file_size': len(file_data),
                    'exception_type': type(e).__name__
                }
            }

    def parse_uploaded_file(self, upload_task_id):
        """
        Parse the ZIP file uploaded to OSS (Endpoint #3).
        
        Args:
            upload_task_id (str): Task ID from upload
            
        Returns:
            dict: Parsing result
        """
        try:
            timestamp = str(int(time.time() * 1000))
            params = {
                'appkey': self.app_key,
                'timestamp': timestamp,
                'upload_task_id': upload_task_id
            }
            
            signature = self.generate_signature(params)
            params['sign'] = signature
            
            url = f"{self.base_url}/global/commodity/upload/create"
            response = requests.post(url, data=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('c') == '0':
                    result = data.get('d')
                    # Ensure we always return a dictionary
                    if result is None:
                        return {'success': True, 'data': None, 'message': 'Parsing completed successfully'}
                    elif isinstance(result, dict):
                        return result
                    else:
                        return {'success': True, 'data': result, 'message': 'Parsing completed successfully'}
                else:
                    st.error(f"❌ Parse Error (Code {data.get('c')}): {data.get('m', 'Unknown error')}")
                    with st.expander("🔍 Parse API Response"):
                        st.json(data)
                    # Return structured error response for UI display
                    return {
                        'error': data.get('m', 'Unknown error'),
                        'error_code': data.get('c'),
                        'full_response': data,
                        'endpoint': 'parse_file',
                        'task_id': upload_task_id,
                        'request_data': {
                            'url': url,
                            'params': params,
                            'timestamp': timestamp
                        }
                    }
            else:
                st.error(f"❌ Parse HTTP Error: {response.status_code}")
                # Return structured error response for UI display
                return {
                    'error': f"HTTP Error: {response.status_code}",
                    'error_code': response.status_code,
                    'response_text': response.text[:500],
                    'endpoint': 'parse_file',
                    'task_id': upload_task_id,
                    'request_data': {
                        'url': url,
                        'params': params,
                        'timestamp': timestamp
                    }
                }
                
        except Exception as e:
            # Return structured error response for UI display
            return {
                'error': str(e),
                'error_code': 'EXCEPTION',
                'endpoint': 'parse_file',
                'task_id': upload_task_id,
                'request_data': {
                    'url': url,
                    'params': params,
                    'timestamp': timestamp
                }
            }

    def submit_parsed_model(self, upload_task_id, model_name="3D Model", pos=99, prod_cat=288, brand_cats=None, brand_good_code="code"):
        """
        Submit parsed ZIP files for Coohom models (Step 5 of upload process).
        
        Args:
            upload_task_id (str): Task ID from upload
            model_name (str): Name for the model submission
            pos (int): Position value (default: 99)
            prod_cat (int): Product category ID (default: 288)
            brand_cats (list): Brand category IDs (default: ["3FO4K6E984C7"])
            brand_good_code (str): Brand good code (default: "code")
            
        Returns:
            dict: Submission result
        """
        try:
            timestamp = str(int(time.time() * 1000))
            
            # Set default brand categories if none provided
            if brand_cats is None:
                brand_cats = ["3FO4K6E984C7"]
            
            # The API expects a List of CommodityUploadSubmitInput objects
            # So we need to wrap our data in an array
            request_body = [{
                "uploadTaskId": upload_task_id,
                "name": model_name,
                "pos": pos,
                "prodCat": prod_cat,
                "location": 1,
                "brandCats": brand_cats,
                "brandGoodCode": brand_good_code
            }]
            
            # Prepare authentication parameters
            auth_params = {
                'appkey': self.app_key,
                'timestamp': timestamp
            }
            
            signature = self.generate_signature(auth_params)
            auth_params['sign'] = signature
            
            url = f"{self.base_url}/global/commodity/upload/submit"
            
            # Debug info
            st.info(f"🔍 **Submit Debug Info:**")
            st.write(f"- API URL: `{url}`")
            st.write(f"- Request Body (Array): `{json.dumps(request_body, indent=2)}`")
            st.write(f"- Auth Params: `{auth_params}`")
            
            # Make POST request with JSON body (as array) and auth params as query string
            response = requests.post(
                url, 
                json=request_body,
                params=auth_params,
                timeout=30
            )
            
            st.write(f"- Response Status: `{response.status_code}`")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    st.write(f"- Response Code: `{data.get('c', 'N/A')}`")
                    st.write(f"- Response Message: `{data.get('m', 'N/A')}`")
                    
                    if data.get('c') == '0':
                        st.success("✅ Model submitted successfully!")
                        result = data.get('d')
                        # Ensure we always return a dictionary
                        if result is None:
                            return {'success': True, 'data': None, 'message': 'Model submitted successfully'}
                        elif isinstance(result, dict):
                            return result
                        else:
                            return {'success': True, 'data': result, 'message': 'Model submitted successfully'}
                    else:
                        st.error(f"❌ Submit Error (Code {data.get('c')}): {data.get('m', 'Unknown error')}")
                        with st.expander("🔍 Submit API Response"):
                            st.json(data)
                        # Return structured error response for UI display
                        return {
                            'error': data.get('m', 'Unknown error'),
                            'error_code': data.get('c'),
                            'full_response': data,
                            'endpoint': 'submit_model',
                            'task_id': upload_task_id,
                            'model_name': model_name,
                            'pos': pos,
                            'prod_cat': prod_cat,
                            'request_data': {
                                'url': url,
                                'auth_params': auth_params,
                                'request_body': request_body,
                                'timestamp': timestamp
                            }
                        }
                except ValueError as e:
                    st.error(f"❌ Invalid JSON response: {str(e)}")
                    st.write(f"Raw response: `{response.text[:200]}...`")
                    return {
                        'error': f"Invalid JSON response: {str(e)}",
                        'error_code': 'JSON_PARSE_ERROR',
                        'response_text': response.text[:500],
                        'endpoint': 'submit_model',
                        'task_id': upload_task_id,
                        'request_data': {
                            'url': url,
                            'auth_params': auth_params,
                            'request_body': request_body,
                            'timestamp': timestamp
                        }
                    }
            else:
                st.error(f"❌ Submit HTTP Error: {response.status_code}")
                st.write(f"Response text: `{response.text[:200]}...`")
                # Return structured error response for UI display
                return {
                    'error': f"HTTP Error: {response.status_code}",
                    'error_code': response.status_code,
                    'response_text': response.text[:500],
                    'endpoint': 'submit_model',
                    'task_id': upload_task_id,
                    'model_name': model_name,
                    'pos': pos,
                    'prod_cat': prod_cat,
                    'request_data': {
                        'url': url,
                        'auth_params': auth_params,
                        'request_body': request_body,
                        'timestamp': timestamp
                    }
                }
                
        except Exception as e:
            st.error(f"❌ Submit Exception: {str(e)}")
            import traceback
            st.error(f"Stack trace: {traceback.format_exc()}")
            # Return structured error response for UI display
            return {
                'error': str(e),
                'error_code': 'EXCEPTION',
                'endpoint': 'submit_model',
                'task_id': upload_task_id,
                'model_name': model_name,
                'pos': pos,
                'prod_cat': prod_cat,
                'request_data': {
                    'url': url,
                    'auth_params': auth_params,
                    'timestamp': timestamp
                }
            }

    def safe_submit_parsed_model(self, upload_task_id, model_name="3D Model", pos=99, prod_cat=288, brand_cats=None, brand_good_code="code", auto_poll=True, max_poll_attempts=5, poll_interval_minutes=2, show_debug=False):
        """
        Safely submit parsed ZIP files for Coohom models with automatic status checking.
        
        This method prevents the "compressed package not parsed successfully" error by:
        1. Checking current status before submission
        2. Waiting for parsing to complete if needed
        3. Only submitting when status = 3 (ready to submit)
        
        Args:
            upload_task_id (str): Task ID from upload
            model_name (str): Name for the model submission
            pos (int): Position value (default: 99)
            prod_cat (int): Product category ID (default: 288)
            brand_cats (list): Brand category IDs (default: ["3FO4K6E984C7"])
            brand_good_code (str): Brand good code (default: "code")
            auto_poll (bool): Whether to automatically wait for parsing to complete
            max_poll_attempts (int): Maximum polling attempts if auto_poll is True
            poll_interval_minutes (int): Minutes between status checks
            show_debug (bool): Whether to show debug information
            
        Returns:
            dict: Submission result with status checking details
        """
        try:
            if show_debug:
                st.info(f"🔄 Starting safe submission workflow for task: {upload_task_id}")
            
            # Step 1: Check current status
            if show_debug:
                st.write("🔍 Step 1: Checking current upload status...")
            
            status_result = self.check_upload_status(upload_task_id)
            
            if 'error' in status_result:
                if show_debug:
                    st.error(f"❌ Status check failed: {status_result['error']}")
                return {
                    'success': False,
                    'error': f"Status check failed: {status_result['error']}",
                    'error_code': 'STATUS_CHECK_FAILED',
                    'endpoint': 'safe_submit_model',
                    'task_id': upload_task_id,
                    'status_check_result': status_result
                }
            
            # Extract current status
            current_status = None
            if isinstance(status_result, dict):
                # Check if status is directly in status_result (from check_upload_status)
                if 'status' in status_result:
                    current_status = status_result.get('status')
                # Check if status is in data field (from other methods)
                elif 'data' in status_result:
                    data = status_result['data']
                    if isinstance(data, dict):
                        current_status = data.get('status')
                    elif isinstance(data, list) and len(data) > 0:
                        current_status = data[0].get('status')
            
            # Convert status to int if it's a string
            try:
                current_status = int(current_status) if current_status is not None else None
            except (ValueError, TypeError):
                current_status = None
            
            if show_debug:
                from config import UPLOAD_STATUS_CODES
                status_desc = UPLOAD_STATUS_CODES.get(current_status, f"Unknown status: {current_status}")
                st.write(f"📊 Current status: {current_status} - {status_desc}")
            
            # Step 2: Handle different status scenarios
            if current_status == 3:
                # Status 3: Ready to submit - proceed immediately
                if show_debug:
                    st.success("✅ Status 3 detected - ready to submit immediately!")
                
            elif current_status in [0, 1]:
                # Status 0 or 1: Still processing - need to wait
                if show_debug:
                    st.warning(f"⏳ Status {current_status} detected - parsing still in progress")
                
                if auto_poll:
                    if show_debug:
                        st.info(f"🔄 Auto-polling enabled - waiting for parsing to complete...")
                    
                    # Use the polling method to wait for completion
                    poll_result = self.poll_upload_status_until_complete(
                        upload_task_id=upload_task_id,
                        max_attempts=max_poll_attempts,
                        interval_minutes=poll_interval_minutes,
                        show_debug=show_debug
                    )
                    
                    if not poll_result.get('success'):
                        if show_debug:
                            st.error(f"❌ Auto-polling failed: {poll_result.get('error')}")
                        return {
                            'success': False,
                            'error': f"Auto-polling failed: {poll_result.get('error')}",
                            'error_code': 'AUTO_POLL_FAILED',
                            'endpoint': 'safe_submit_model',
                            'task_id': upload_task_id,
                            'poll_result': poll_result
                        }
                    
                    # Check final status from polling
                    final_status = poll_result.get('status')
                    if show_debug:
                        st.write(f"📊 Final status after polling: {final_status}")
                    
                    if final_status == 3:
                        if show_debug:
                            st.success("✅ Parsing completed - ready to submit!")
                    elif final_status in [2, 4, 5, 6]:
                        if show_debug:
                            if final_status == 2:
                                st.error(f"❌ Model parsing failed (status {final_status}) - cannot submit")
                            else:
                                st.info(f"📊 Model reached terminal status {final_status} during polling")
                        return {
                            'success': True,
                            'status': final_status,
                            'message': f"Model reached terminal status {final_status} during polling",
                            'endpoint': 'safe_submit_model',
                            'task_id': upload_task_id,
                            'poll_result': poll_result,
                            'submission_skipped': True
                        }
                    else:
                        if show_debug:
                            st.warning(f"⚠️ Unexpected final status after polling: {final_status}")
                        return {
                            'success': False,
                            'error': f"Unexpected final status after polling: {final_status}",
                            'error_code': 'UNEXPECTED_STATUS',
                            'endpoint': 'safe_submit_model',
                            'task_id': upload_task_id,
                            'poll_result': poll_result
                        }
                else:
                    # Auto-polling disabled - return error
                    if show_debug:
                        st.error("❌ Auto-polling disabled - cannot proceed with status 0 or 1")
                    return {
                        'success': False,
                        'error': f"Cannot submit with status {current_status} (parsing not complete). Enable auto_poll or wait for status 3.",
                        'error_code': 'PARSING_NOT_COMPLETE',
                        'endpoint': 'safe_submit_model',
                        'task_id': upload_task_id,
                        'current_status': current_status
                    }
            
            elif current_status == 2:
                # Status 2: Parsing failed - cannot submit
                if show_debug:
                    st.error("❌ Status 2 detected - parsing failed, cannot submit")
                return {
                    'success': False,
                    'status': 2,
                    'error': "Parsing failed (status 2) - cannot submit the model",
                    'error_code': 'PARSING_FAILED',
                    'endpoint': 'safe_submit_model',
                    'task_id': upload_task_id,
                    'current_status': current_status
                }
            
            elif current_status == 4:
                # Status 4: Already submitted - no need to submit again
                if show_debug:
                    st.info("📊 Status 4 detected - model already submitted")
                return {
                    'success': True,
                    'status': 4,
                    'message': "Model already submitted (status 4)",
                    'endpoint': 'safe_submit_model',
                    'task_id': upload_task_id,
                    'current_status': current_status,
                    'submission_skipped': True
                }
            
            elif current_status == 5:
                # Status 5: Previous submission failed - can retry
                if show_debug:
                    st.warning("⚠️ Status 5 detected - previous submission failed, will retry")
            
            elif current_status == 6:
                # Status 6: Analyzed offline - cannot submit
                if show_debug:
                    st.info("📊 Status 6 detected - model analyzed offline, cannot submit")
                return {
                    'success': False,
                    'error': "Model analyzed offline (status 6) - cannot submit",
                    'error_code': 'OFFLINE_ANALYSIS',
                    'endpoint': 'safe_submit_model',
                    'task_id': upload_task_id,
                    'current_status': current_status
                }
            
            elif current_status is None:
                # Unknown status - cannot proceed safely
                if show_debug:
                    st.error("❌ Unknown status - cannot proceed safely")
                return {
                    'success': False,
                    'error': "Unknown status - cannot proceed safely",
                    'error_code': 'UNKNOWN_STATUS',
                    'endpoint': 'safe_submit_model',
                    'task_id': upload_task_id,
                    'status_result': status_result
                }
            
            # Step 3: Submit the model (status should be 3 or 5 at this point)
            if show_debug:
                st.write("🚀 Step 3: Submitting model...")
            
            submit_result = self.submit_parsed_model(
                upload_task_id=upload_task_id,
                model_name=model_name,
                pos=pos,
                prod_cat=prod_cat,
                brand_cats=brand_cats,
                brand_good_code=brand_good_code
            )
            
            # Step 4: Return combined result
            if 'error' in submit_result:
                if show_debug:
                    st.error(f"❌ Model submission failed: {submit_result['error']}")
                return {
                    'success': False,
                    'error': f"Model submission failed: {submit_result['error']}",
                    'submit_result': submit_result,
                    'endpoint': 'safe_submit_model',
                    'task_id': upload_task_id,
                    'status_check_result': status_result
                }
            else:
                if show_debug:
                    st.success("✅ Safe submission workflow completed successfully!")
                return {
                    'success': True,
                    'status': 'submitted',
                    'message': 'Model submitted successfully through safe workflow',
                    'endpoint': 'safe_submit_model',
                    'task_id': upload_task_id,
                    'submit_result': submit_result,
                    'status_check_result': status_result
                }
                
        except Exception as e:
            if show_debug:
                st.error(f"❌ Safe submission exception: {str(e)}")
                import traceback
                st.error(f"Stack trace: {traceback.format_exc()}")
            
            return {
                'success': False,
                'error': str(e),
                'error_code': 'EXCEPTION',
                'endpoint': 'safe_submit_model',
                'task_id': upload_task_id,
                'model_name': model_name,
                'pos': pos,
                'prod_cat': prod_cat
            }

    def get_brand_good_library_categories(self, library_id=87, max_retries=3):
        """
        Get brand good library categories using the Coohom API.
        
        Args:
            library_id (int): Library ID (default: 87 as per documentation)
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            dict or None: Categories data if successful, None otherwise
        """
        for attempt in range(max_retries):
            try:
                # Prepare parameters
                timestamp = str(int(time.time() * 1000))
                params = {
                    'appkey': self.app_key,
                    'timestamp': timestamp,
                    'library': library_id
                }
                
                # Generate signature
                signature = self.generate_signature(params)
                params['sign'] = signature
                
                # API endpoint
                url = "https://openapi.kujiale.com/v2/custom/brandgood/library/category"
                
                # Make API request
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('c') == '0':
                            return data.get('d')
                        else:
                            if attempt < max_retries - 1:
                                time.sleep(2)
                                continue
                            return None
                    except json.JSONDecodeError:
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                        return None
                else:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return None
                    
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
        
        return None

    def get_brand_good_libraries(self, max_retries=3):
        """
        Get brand good libraries using the Coohom API.
        
        Args:
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            dict or None: Libraries data if successful, None otherwise
        """
        for attempt in range(max_retries):
            try:
                # Prepare parameters
                timestamp = str(int(time.time() * 1000))
                params = {
                    'appkey': self.app_key,
                    'timestamp': timestamp
                }
                
                # Generate signature
                signature = self.generate_signature(params)
                params['sign'] = signature
                
                # API endpoint
                url = "https://openapi.kujiale.com/v2/custom/brandgood/library/libraries"
                
                # Make API request
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('c') == '0':
                            return data.get('d')
                        else:
                            if attempt < max_retries - 1:
                                time.sleep(2)
                                continue
                            return None
                    except json.JSONDecodeError:
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                        return None
                else:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return None
                    
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
        
        return None

    def get_dynamic_brand_good_params(self, library_id=87):
        """
        Get dynamic parameters for obsBrandGoodLocationParam by fetching
        categories and libraries from the API.
        
        Args:
            library_id (int): Library ID to use for categories (default: 87)
            
        Returns:
            dict: Parameters for obsBrandGoodLocationParam
        """
        # Get categories for the specified library
        categories = self.get_brand_good_library_categories(library_id)
        
        # Get available libraries
        libraries = self.get_brand_good_libraries()
        
        # Default values if API calls fail
        default_params = {
            "obsCustomLibID": "1",  # Default library ID
            "obsBusinessCatIds": ["1"],  # Default category ID
            "sceneId": 1,
            "libraryId": library_id
        }
        
        if categories and libraries:
            try:
                # Extract category IDs from the response
                if isinstance(categories, list) and len(categories) > 0:
                    category_ids = [str(cat.get('id', cat.get('categoryId', '1'))) for cat in categories[:3]]
                    default_params["obsBusinessCatIds"] = category_ids
                
                # Extract library ID from the response
                if isinstance(libraries, list) and len(libraries) > 0:
                    lib_id = str(libraries[0].get('id', libraries[0].get('libraryId', '1')))
                    default_params["obsCustomLibID"] = lib_id
                
            except Exception:
                pass  # Use default values if processing fails
        
        return default_params


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

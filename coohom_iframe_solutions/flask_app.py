#!/usr/bin/env python3
"""
Flask-based Coohom Iframe Integration
Better iframe support than Streamlit
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import hashlib
import time
import json
from datetime import datetime, timedelta, timezone
import urllib.parse
import os

app = Flask(__name__)
app.secret_key = 'coohom_iframe_secret_key_2025'  # Change in production

# Coohom API Configuration
class CoohomAPI:
    def __init__(self):
        self.base_url = "https://api.coohom.com"
        self.load_credentials()
    
    def load_credentials(self):
        """Load API credentials from file"""
        try:
            with open("../credential.txt", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("appKey="):
                        self.appkey = line.split("=")[1].strip()
                    elif line.startswith("appSecret="):
                        self.appsecret = line.split("=")[1].strip()
        except FileNotFoundError:
            print("❌ credential.txt not found")
            self.appkey = None
            self.appsecret = None
    
    def generate_signature(self, appuid=None, timestamp=None):
        """Generate MD5 signature for API calls"""
        if timestamp is None:
            timestamp = str(int(time.time() * 1000))
        
        if appuid:
            content = f"{self.appsecret}{self.appkey}{appuid}{timestamp}"
        else:
            content = f"{self.appsecret}{self.appkey}{timestamp}"
        
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def register_user(self, appuid, name, email):
        """Register a new user with Coohom"""
        timestamp = str(int(time.time() * 1000))
        sign = self.generate_signature(timestamp=timestamp)
        
        url = f"{self.base_url}/global/i18n-user/register"
        params = {
            'appkey': self.appkey,
            'timestamp': timestamp,
            'sign': sign,
            'appuid': appuid
        }
        data = {
            'name': name,
            'email': email
        }
        
        try:
            response = requests.post(url, params=params, json=data)
            return response.json()
        except Exception as e:
            return {'c': '1', 'm': f'Error: {str(e)}'}
    
    def login_user(self, appuid):
        """Generate SSO token for user"""
        timestamp = str(int(time.time() * 1000))
        sign = self.generate_signature(appuid, timestamp)
        
        url = f"{self.base_url}/global/i18n-user/login"
        params = {
            'appkey': self.appkey,
            'timestamp': timestamp,
            'sign': sign,
            'appuid': appuid
        }
        
        try:
            response = requests.post(url, params=params)
            return response.json()
        except Exception as e:
            return {'c': '1', 'm': f'Error: {str(e)}'}

# Initialize API client
coohom_api = CoohomAPI()

@app.route('/')
def index():
    """Main page with iframe integration"""
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register_user():
    """API endpoint for user registration"""
    data = request.get_json()
    appuid = data.get('appuid')
    name = data.get('name')
    email = data.get('email')
    
    if not all([appuid, name, email]):
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    result = coohom_api.register_user(appuid, name, email)
    
    if result and result.get('c') == '0':
        return jsonify({'success': True, 'message': 'User registered successfully'})
    else:
        return jsonify({'success': False, 'error': result.get('m', 'Unknown error')})

@app.route('/api/login', methods=['POST'])
def login_user():
    """API endpoint for SSO login"""
    data = request.get_json()
    appuid = data.get('appuid')
    
    if not appuid:
        return jsonify({'success': False, 'error': 'Missing appuid'})
    
    result = coohom_api.login_user(appuid)
    
    if result and result.get('c') == '0':
        # Store in session
        session['sso_token'] = result['d']['token']
        session['sso_url'] = result['d'].get('url')
        session['token_expiry'] = datetime.now(timezone.utc) + timedelta(days=7)
        
        return jsonify({
            'success': True,
            'token': result['d']['token'],
            'url': result['d'].get('url'),
            'expires': session['token_expiry'].isoformat()
        })
    else:
        return jsonify({'success': False, 'error': result.get('m', 'Unknown error')})

@app.route('/iframe/<integration_type>')
def iframe_page(integration_type):
    """Iframe integration page"""
    if 'sso_token' not in session:
        return redirect(url_for('index'))
    
    # Check token expiry
    if 'token_expiry' in session and datetime.now(timezone.utc) > session['token_expiry']:
        session.clear()
        return redirect(url_for('index'))
    
    return render_template('iframe.html', 
                         integration_type=integration_type,
                         sso_token=session['sso_token'],
                         sso_url=session.get('sso_url'),
                         get_iframe_url=lambda: get_iframe_url(integration_type, session.get('sso_url')))

def get_iframe_url(integration_type, sso_url):
    """Generate the appropriate iframe URL based on integration type"""
    base_url = "https://www.coohom.com"
    
    if integration_type == 'sso-url' and sso_url:
        # Use the SSO response URL directly
        return f"{base_url}{sso_url}"
    elif integration_type == 'project-list':
        # Project list URL
        return f"{base_url}/pub/saas/apps/project/list"
    elif integration_type == 'design-tool':
        # Design tool URL
        return f"{base_url}/pub/tool/yundesign/cloud"
    elif integration_type == 'custom':
        # Custom integration - could be configurable
        return f"{base_url}/pub/saas/apps/project/list"
    else:
        # Default fallback
        return f"{base_url}/pub/saas/apps/project/list"

@app.route('/api/status')
def api_status():
    """Check API status and credentials"""
    if coohom_api.appkey and coohom_api.appsecret:
        return jsonify({
            'status': 'ready',
            'appkey': f"{coohom_api.appkey[:4]}...{coohom_api.appkey[-4:]}",
            'appsecret': f"{coohom_api.appsecret[:4]}...{coohom_api.appsecret[-4:]}"
        })
    else:
        return jsonify({'status': 'error', 'message': 'Credentials not loaded'})

@app.route('/coohom-iframe')
def coohom_iframe():
    """Serve Coohom iframe with SSO token"""
    if 'sso_token' not in session:
        return jsonify({'error': 'No SSO token found. Please login first.'}), 401
    
    # Check token expiry
    if 'token_expiry' in session and datetime.now(timezone.utc) > session['token_expiry']:
        session.clear()
        return jsonify({'error': 'SSO token expired. Please login again.'}), 401
    
    # Get the SSO token and URL from session
    sso_token = session['sso_token']
    sso_url = session.get('sso_url')
    
    # Debug logging
    print(f"DEBUG: SSO Token: {sso_token[:50]}...")
    print(f"DEBUG: SSO URL: {sso_url}")
    
    # Try the Kujiale-style authentication pattern first
    # Based on: https://www.kujiale.com/open/login?access_token={token}
    # For Coohom, this would be: https://www.coohom.com/open/login?access_token={SSO_TOKEN}
    
    # Try multiple authentication patterns in order of preference
    iframe_url = f"https://www.coohom.com/open/login?access_token={sso_token}"
    print(f"DEBUG: Using Kujiale-style URL: {iframe_url}")
    
    return jsonify({
        'success': True,
        'iframe_url': iframe_url,
        'sso_token': sso_token,
        'sso_url': sso_url,
        'expires': session['token_expiry'].isoformat() if 'token_expiry' in session else None
    })

@app.route('/test-url')
def test_url():
    """Test endpoint to verify URL construction"""
    if 'sso_token' not in session:
        return jsonify({'error': 'No SSO token found. Please login first.'}), 401
    
    sso_token = session['sso_token']
    sso_url = session.get('sso_url')
    
    # Test different URL constructions
    test_urls = {
        'kujiale_style': f"https://www.coohom.com/open/login?access_token={sso_token}",
        'sso_url_direct': f"https://www.coohom.com{sso_url}" if sso_url else None,
        'sso_url_with_token': f"https://www.coohom.com{sso_url}?token={sso_token}" if sso_url else None,
        'design_tool_with_token': f"https://www.coohom.com/pub/tool/yundesign/cloud?token={sso_token}",
        'project_list_with_token': f"https://www.coohom.com/pub/saas/apps/project/list?token={sso_token}",
        'sso_url_with_auth_header': f"https://www.coohom.com{sso_url}" if sso_url else None
    }
    
    return jsonify({
        'success': True,
        'session_data': {
            'sso_token': sso_token[:50] + '...' if sso_token else None,
            'sso_url': sso_url,
            'token_length': len(sso_token) if sso_token else 0
        },
        'test_urls': test_urls,
        'recommendation': 'Try kujiale_style first - this follows the Kujiale authentication pattern'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

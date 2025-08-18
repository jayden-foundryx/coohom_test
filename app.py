#!/usr/bin/env python3
"""
Manual Step-by-Step Streamlit application for Coohom 3D Model Upload Workflow.

This app provides a manual interface for uploading 3D models to Coohom,
with user-controlled progression through each of the 5 API endpoints.
"""

import streamlit as st
import os
import time
from pathlib import Path
import zipfile
import tempfile

# Import our custom API client
from coohom_api import CoohomUploader
from file_utils import get_status_description, estimate_upload_time

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Coohom 3D Model Upload - Manual",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏠 Coohom 3D Model Upload - Manual Step-by-Step")
    st.markdown("Manual control over each step of the 3D model upload workflow.")
    
    # Initialize session state
    if 'upload_task_id' not in st.session_state:
        st.session_state.upload_task_id = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'workflow_status' not in st.session_state:
        st.session_state.workflow_status = {}
    
    # Sidebar for credentials and configuration
    with st.sidebar:
        st.header("🔑 API Configuration")
        
        # Load credentials from file if available
        # Try credentials.txt first, then credential.txt (to match coohom_api.py logic)
        default_app_key = ""
        default_app_secret = ""
        
        credentials_loaded = False
        for filename in ['credentials.txt', 'credential.txt']:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.startswith('appKey='):
                                default_app_key = line.split('=')[1].strip()
                            elif line.startswith('appSecret='):
                                default_app_secret = line.split('=')[1].strip()
                    
                    # Check if we successfully loaded both credentials
                    if default_app_key and default_app_secret:
                        credentials_loaded = True
                        st.success(f"✅ Credentials loaded from {filename}")
                        break
                    else:
                        st.warning(f"⚠️ {filename} exists but is incomplete")
                        
                except Exception as e:
                    st.warning(f"⚠️ Could not load credentials from {filename}: {e}")
        
        if not credentials_loaded:
            st.warning("⚠️ No valid credentials file found. Please create credentials.txt or credential.txt")
        
        app_key = st.text_input("App Key", value=default_app_key, type="password")
        app_secret = st.text_input("App Secret", value=default_app_secret, type="password")
        
        if not app_key or not app_secret:
            st.warning("Please enter your API credentials to continue.")
            st.stop()
        
        # Initialize uploader
        try:
            uploader = CoohomUploader(app_key, app_secret)
            st.success("✅ API client initialized successfully")
        except Exception as e:
            st.error(f"❌ Failed to initialize API client: {e}")
            st.stop()
        
        st.header("⚙️ Workflow Settings")
        auto_poll = st.checkbox("Enable Auto-Polling", value=True, 
                               help="Automatically check status until completion")
        max_poll_attempts = st.slider("Max Polling Attempts", 3, 10, 5,
                                     help="Maximum number of status checks")
        poll_interval = st.slider("Polling Interval (minutes)", 1, 5, 2,
                                 help="Minutes between status checks")
        
        # Add debug mode toggle
        debug_mode = st.checkbox("🔍 Debug Mode", value=False,
                                help="Show detailed API debugging information")
        
        # Add API test button
        if st.button("🧪 Test API Connection", use_container_width=True):
            with st.spinner("Testing API connection..."):
                try:
                    test_result = uploader.get_sts_credentials("test.obj", show_debug=debug_mode, timeout=10)
                    if 'error' in test_result:
                        st.error(f"❌ API test failed: {test_result['error']}")
                    else:
                        st.success("✅ API connection test successful!")
                except Exception as e:
                    st.error(f"❌ API test exception: {str(e)}")
        
        st.header("📊 Current Status")
        if st.session_state.upload_task_id:
            st.info(f"Task ID: `{st.session_state.upload_task_id}`")
            if st.button("🔄 Refresh Status", use_container_width=True):
                st.rerun()
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Manual Workflow", "📊 Status Monitor", "🔍 Manual Operations", "📚 Documentation"])
    
    with tab1:
        st.header("🚀 Manual Step-by-Step Workflow")
        st.markdown("Control each step manually - proceed when ready.")
        
        # File upload section
        st.subheader("📁 Step 0: File Selection")
        
        uploaded_file = st.file_uploader(
            "Choose a 3D model file or ZIP archive",
            type=['obj', 'fbx', '3ds', 'dae', 'blend', 'zip'],
            help="Supported formats: OBJ, FBX, 3DS, DAE, BLEND, or ZIP containing these files"
        )
        
        if uploaded_file:
            file_size = len(uploaded_file.getvalue())
            file_size_mb = file_size / (1024 * 1024)
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ File selected: {uploaded_file.name}")
                st.info(f"📏 File size: {file_size_mb:.2f} MB")
                
                # Estimate upload time
                estimated_time = estimate_upload_time(file_size)
                st.info(f"⏱️ Estimated upload time: {estimated_time}")
            
            with col2:
                # Check if we need to create a ZIP file
                if not uploaded_file.name.lower().endswith('.zip'):
                    st.warning("⚠️ Non-ZIP file detected")
                    st.info("The app will automatically create a ZIP archive for you.")
                else:
                    st.success("✅ ZIP file detected")
            
            # Model configuration
            st.subheader("⚙️ Model Configuration")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                model_name = st.text_input("Model Name", 
                                         value=uploaded_file.name.split('.')[0],
                                         help="Name for your 3D model")
                pos_input = st.text_input("Position (Optional)", value="", 
                                        help="Position value for the model. Leave blank if not needed. For lighting design library use 99.")
                
                # Convert to integer if provided, otherwise None
                pos = None
                if pos_input.strip():
                    try:
                        pos = int(pos_input)
                        if pos < 1 or pos > 999:
                            st.warning("⚠️ Position should be between 1 and 999")
                            pos = None
                    except ValueError:
                        st.warning("⚠️ Position should be a valid number")
                        pos = None
            
            with col2:
                prod_cat = st.number_input("Product Category ID", value=288, min_value=1,
                                         help="Product category ID from Coohom")
                brand_good_code = st.text_input("Brand Good Code", value="code",
                                              help="Brand good code identifier")
            
            with col3:
                brand_cats_input = st.text_input("Brand Category IDs", value="3FO4JXABJ2W6",
                                               help="Comma-separated brand category IDs")
                brand_cats = [cat.strip() for cat in brand_cats_input.split(',') if cat.strip()]
            
            # Start workflow button - now starts manual step-by-step process
            if st.button("🚀 Start Manual Step-by-Step Workflow", type="primary", use_container_width=True):
                if not model_name:
                    st.error("Please enter a model name")
                    return
                
                # Start the workflow at step 1
                st.session_state.current_step = 1
                st.session_state.workflow_status = {}
                
                # Store model configuration in session state for later use
                st.session_state.model_name = model_name
                st.session_state.pos = pos
                st.session_state.prod_cat = prod_cat
                st.session_state.brand_cats = brand_cats
                st.session_state.brand_good_code = brand_good_code
                
                # Store uploaded file data in session state
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.uploaded_file_content = uploaded_file.getvalue()
                
                st.success("🚀 Manual workflow started! Ready for Step 1.")
                st.rerun()
            
            # Manual Step-by-Step Workflow
            if st.session_state.current_step > 0:
                st.subheader("📊 Manual Step-by-Step Progress")
                
                # Show progress overview
                steps = ["Ready", "Get STS Credentials", "Upload to OSS", "Parse File", "Submit Model"]
                for i, step in enumerate(steps):
                    if i < st.session_state.current_step:
                        st.success(f"✅ Step {i}: {step}")
                    elif i == st.session_state.current_step:
                        st.info(f"🔄 Step {i}: {step} (Current)")
                    else:
                        st.info(f"⏳ Step {i}: {step} (Pending)")
                
                st.markdown("---")
                
                # Step 1: Get STS Credentials
                if st.session_state.current_step == 1:
                    st.subheader("🔑 Step 1: Get STS Credentials")
                    st.info("Click the button below to get STS credentials from Coohom API")
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown("**What happens:** Request temporary upload credentials from Coohom")
                        st.markdown("**Timeout:** 20 seconds")
                    
                    with col2:
                        if st.button("🚀 Get STS Credentials", type="primary", use_container_width=True):
                            with st.spinner("🔄 Getting STS credentials from Coohom API..."):
                                try:
                                    sts_result = uploader.get_sts_credentials(
                                        st.session_state.uploaded_file_name, 
                                        show_debug=debug_mode, 
                                        timeout=20
                                    )
                                    
                                    if 'error' in sts_result:
                                        st.error(f"❌ STS credentials failed: {sts_result['error']}")
                                        
                                        with st.expander("🔍 Detailed Error Information"):
                                            st.json(sts_result)
                                        
                                        st.error("💡 Troubleshooting Tips:")
                                        st.markdown("""
                                        - Check your API credentials in the sidebar
                                        - Verify your internet connection
                                        - Try again in a few minutes if servers are busy
                                        """)
                                    else:
                                        st.success("✅ STS credentials obtained successfully!")
                                        st.session_state.workflow_status['sts'] = sts_result
                                        st.session_state.current_step = 2
                                        
                                        with st.expander("🔍 STS Credentials Details"):
                                            st.json(sts_result)
                                        
                                        st.info("🎉 **Step 1 Complete!** Ready for Step 2.")
                                        st.rerun()
                                        
                                except Exception as e:
                                    st.error(f"❌ Exception during STS credentials: {str(e)}")
                                    st.error("💡 This might be a timeout or connection issue. Please try again.")
                
                # Step 2: Upload to OSS
                elif st.session_state.current_step == 2:
                    st.subheader("☁️ Step 2: Upload to OSS")
                    st.info("Upload your file to Alibaba Cloud Object Storage Service")
                    
                    if 'sts' not in st.session_state.workflow_status:
                        st.error("❌ STS credentials not found. Please go back to Step 1.")
                        if st.button("🔙 Back to Step 1"):
                            st.session_state.current_step = 1
                            st.rerun()
                    else:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown("**What happens:** Upload your 3D model file to cloud storage")
                            st.markdown("**File processing:** Creates ZIP if needed")
                            
                            # Show file info
                            file_size_mb = len(st.session_state.uploaded_file_content) / (1024 * 1024)
                            st.markdown(f"**File:** {st.session_state.uploaded_file_name} ({file_size_mb:.2f} MB)")
                        
                        with col2:
                            if st.button("☁️ Upload to OSS", type="primary", use_container_width=True):
                                with st.spinner("☁️ Uploading to Alibaba Cloud OSS..."):
                                    try:
                                        # Create temporary ZIP if needed
                                        zip_path = None
                                        if not st.session_state.uploaded_file_name.lower().endswith('.zip'):
                                            st.info("📦 Creating ZIP archive...")
                                            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
                                                with zipfile.ZipFile(tmp_zip.name, 'w') as zipf:
                                                    zipf.writestr(st.session_state.uploaded_file_name, st.session_state.uploaded_file_content)
                                                zip_path = tmp_zip.name
                                        
                                        # Upload to OSS
                                        if zip_path:
                                            # Read ZIP file data
                                            with open(zip_path, 'rb') as f:
                                                file_data_to_upload = f.read()
                                            filename_to_upload = st.session_state.uploaded_file_name + '.zip'
                                        else:
                                            file_data_to_upload = st.session_state.uploaded_file_content
                                            filename_to_upload = st.session_state.uploaded_file_name
                                        
                                        upload_result = uploader.upload_to_oss(
                                            file_data=file_data_to_upload,
                                            sts_data=st.session_state.workflow_status['sts'],
                                            original_filename=filename_to_upload
                                        )
                                        
                                        # Clean up temporary file
                                        if zip_path and os.path.exists(zip_path):
                                            os.unlink(zip_path)
                                        
                                        if 'error' in upload_result:
                                            st.error(f"❌ OSS upload failed: {upload_result['error']}")
                                            
                                            with st.expander("🔍 OSS Upload Error Details"):
                                                st.json(upload_result)
                                        else:
                                            st.success("✅ File uploaded to OSS successfully!")
                                            st.session_state.workflow_status['oss_upload'] = upload_result
                                            st.session_state.current_step = 3
                                            
                                            st.info("🎉 **Step 2 Complete!** Ready for Step 3.")
                                            st.rerun()
                                    
                                    except Exception as e:
                                        st.error(f"❌ Exception during OSS upload: {str(e)}")
                
                # Step 3: Parse Uploaded File
                elif st.session_state.current_step == 3:
                    st.subheader("🔍 Step 3: Parse Uploaded File")
                    st.info("Parse the uploaded file to prepare it for submission")
                    
                    if 'oss_upload' not in st.session_state.workflow_status:
                        st.error("❌ OSS upload data not found. Please go back to Step 2.")
                        if st.button("🔙 Back to Step 2"):
                            st.session_state.current_step = 2
                            st.rerun()
                    else:
                        # Get the upload task ID from STS credentials
                        upload_task_id = st.session_state.workflow_status['sts'].get('uploadTaskId')
                        
                        if not upload_task_id:
                            st.error("❌ Upload Task ID not found in STS credentials.")
                            with st.expander("🔍 STS Data"):
                                st.json(st.session_state.workflow_status['sts'])
                            if st.button("🔙 Back to Step 1"):
                                st.session_state.current_step = 1
                                st.rerun()
                        else:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown("**What happens:** Parse the uploaded ZIP file for 3D model processing")
                                st.markdown("**Upload Task ID:** `" + upload_task_id + "`")
                                
                                # Show OSS upload info
                                if st.session_state.workflow_status['oss_upload'].get('success'):
                                    st.markdown("**OSS Upload:** ✅ File successfully uploaded")
                                    oss_path = st.session_state.workflow_status['oss_upload'].get('oss_path', 'N/A')
                                    st.markdown(f"**OSS Path:** `{oss_path[:50]}...`" if len(oss_path) > 50 else f"**OSS Path:** `{oss_path}`")
                            
                            with col2:
                                if st.button("🔍 Parse File", type="primary", use_container_width=True):
                                    with st.spinner("🔍 Parsing uploaded file..."):
                                        try:
                                            parse_result = uploader.parse_uploaded_file(upload_task_id)
                                            
                                            if 'error' in parse_result:
                                                st.error(f"❌ File parsing failed: {parse_result['error']}")
                                                
                                                with st.expander("🔍 Parse Error Details"):
                                                    st.json(parse_result)
                                            else:
                                                st.success("✅ File parsed successfully!")
                                                st.session_state.upload_task_id = upload_task_id
                                                st.session_state.workflow_status['parse_file'] = parse_result
                                                st.session_state.current_step = 4
                                                
                                                with st.expander("🔍 Parse Result Details"):
                                                    st.json(parse_result)
                                                
                                                st.info("🎉 **Step 3 Complete!** Ready for Step 4.")
                                                st.rerun()
                                        
                                        except Exception as e:
                                            st.error(f"❌ Exception during file parsing: {str(e)}")
                
                # Step 4: Submit Model
                elif st.session_state.current_step == 4:
                    st.subheader("🚀 Step 4: Submit Model")
                    st.info("Submit your parsed model to Coohom")
                    
                    if not st.session_state.upload_task_id:
                        st.error("❌ Task ID not found. Please go back to Step 3.")
                        if st.button("🔙 Back to Step 3"):
                            st.session_state.current_step = 3
                            st.rerun()
                    else:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown("**What happens:** Submit your model with configured parameters")
                            st.markdown(f"**Task ID:** `{st.session_state.upload_task_id}`")
                            st.markdown(f"**Model Name:** {st.session_state.model_name}")
                            pos_display = str(st.session_state.pos) if st.session_state.pos is not None else "Not set (optional)"
                            st.markdown(f"**Position:** {pos_display}")
                            st.markdown(f"**Product Category:** {st.session_state.prod_cat}")
                        
                        with col2:
                            # Option 1: Direct Submit
                            if st.button("🚀 Submit Model", type="primary", use_container_width=True):
                                with st.spinner("🚀 Submitting model..."):
                                    try:
                                        # Only pass pos if it's provided
                                        submit_kwargs = {
                                            'upload_task_id': st.session_state.upload_task_id,
                                            'model_name': st.session_state.model_name,
                                            'prod_cat': st.session_state.prod_cat,
                                            'brand_cats': st.session_state.brand_cats,
                                            'brand_good_code': st.session_state.brand_good_code
                                        }
                                        
                                        # Add pos only if it's not None
                                        if st.session_state.pos is not None:
                                            submit_kwargs['pos'] = st.session_state.pos
                                        
                                        submit_result = uploader.submit_parsed_model(**submit_kwargs)
                                        
                                        if 'error' in submit_result:
                                            st.error(f"❌ Model submission failed: {submit_result['error']}")
                                            
                                            with st.expander("🔍 Submission Error Details"):
                                                st.json(submit_result)
                                        else:
                                            st.success("🎉 Model submitted successfully!")
                                            st.session_state.workflow_status['submission'] = submit_result
                                            st.session_state.current_step = 5
                                            
                                            with st.expander("🔍 Submission Details"):
                                                st.json(submit_result)
                                            
                                            st.balloons()
                                            st.success("🎉 **Workflow Complete!** Your model has been submitted to Coohom.")
                                            st.rerun()
                                    
                                    except Exception as e:
                                        st.error(f"❌ Exception during model submission: {str(e)}")
                            
                            # Option 2: Safe Submit (with status checking)
                            st.markdown("**OR**")
                            if st.button("🛡️ Safe Submit", type="secondary", use_container_width=True):
                                with st.spinner("🛡️ Starting safe submission..."):
                                    try:
                                        # Only pass pos if it's provided
                                        safe_submit_kwargs = {
                                            'upload_task_id': st.session_state.upload_task_id,
                                            'model_name': st.session_state.model_name,
                                            'prod_cat': st.session_state.prod_cat,
                                            'brand_cats': st.session_state.brand_cats,
                                            'brand_good_code': st.session_state.brand_good_code,
                                            'auto_poll': auto_poll,
                                            'max_poll_attempts': max_poll_attempts,
                                            'poll_interval_minutes': poll_interval,
                                            'show_debug': debug_mode
                                        }
                                        
                                        # Add pos only if it's not None
                                        if st.session_state.pos is not None:
                                            safe_submit_kwargs['pos'] = st.session_state.pos
                                        
                                        safe_result = uploader.safe_submit_parsed_model(**safe_submit_kwargs)
                                        
                                        if safe_result.get('success'):
                                            if safe_result.get('submission_skipped'):
                                                st.warning(f"⚠️ {safe_result['message']}")
                                            else:
                                                st.success("🎉 Safe submission completed successfully!")
                                            
                                            st.session_state.workflow_status['submission'] = safe_result
                                            st.session_state.current_step = 5
                                            
                                            st.balloons()
                                            st.success("🎉 **Workflow Complete!** Your model has been submitted to Coohom.")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Safe submission failed: {safe_result.get('error')}")
                                            
                                            with st.expander("🔍 Safe Submission Error Details"):
                                                st.json(safe_result)
                                    
                                    except Exception as e:
                                        st.error(f"❌ Exception during safe submission: {str(e)}")
                
                # Step 5: Workflow Complete
                elif st.session_state.current_step == 5:
                    st.subheader("🎉 Workflow Complete!")
                    st.success("Your 3D model has been successfully submitted to Coohom!")
                    
                    # Show completion summary
                    with st.expander("📋 Workflow Summary"):
                        st.markdown("### Completed Steps:")
                        st.success("✅ Step 1: STS Credentials obtained")
                        st.success("✅ Step 2: File uploaded to OSS")
                        st.success("✅ Step 3: File parsed successfully")
                        st.success("✅ Step 4: Model submitted")
                        
                        if st.session_state.upload_task_id:
                            st.info(f"**Final Task ID:** `{st.session_state.upload_task_id}`")
                        
                        if 'submission' in st.session_state.workflow_status:
                            st.json(st.session_state.workflow_status['submission'])
                    
                    # Reset workflow option
                    if st.button("🔄 Start New Workflow", type="primary", use_container_width=True):
                        st.session_state.current_step = 0
                        st.session_state.workflow_status = {}
                        st.session_state.upload_task_id = None
                        # Clear stored file data
                        if 'uploaded_file_name' in st.session_state:
                            del st.session_state.uploaded_file_name
                        if 'uploaded_file_content' in st.session_state:
                            del st.session_state.uploaded_file_content
                        st.rerun()
                
                # Show current step status for debugging (if debug mode is on)
                if debug_mode:
                    st.markdown("---")
                    st.subheader("🔍 Debug Information")
                    st.info(f"Current Step: {st.session_state.current_step}")
                    st.info(f"Workflow Status Keys: {list(st.session_state.workflow_status.keys())}")
                    if st.session_state.upload_task_id:
                        st.info(f"Upload Task ID: {st.session_state.upload_task_id}")
                
                # Universal Reset Button
                st.markdown("---")
                if st.button("🔄 Reset Entire Workflow", type="secondary"):
                    st.session_state.current_step = 0
                    st.session_state.workflow_status = {}
                    st.session_state.upload_task_id = None
                    # Clear stored file data
                    if 'uploaded_file_name' in st.session_state:
                        del st.session_state.uploaded_file_name
                    if 'uploaded_file_content' in st.session_state:
                        del st.session_state.uploaded_file_content
                    st.success("🔄 Workflow reset successfully!")
                    st.rerun()
    
    with tab2:
        st.header("📊 Status Monitor")
        
        if st.session_state.upload_task_id:
            st.info(f"Monitoring Task ID: `{st.session_state.upload_task_id}`")
            
            # Status checking
            if st.button("🔍 Check Current Status", use_container_width=True):
                with st.spinner("Checking status..."):
                    status_result = uploader.check_upload_status(st.session_state.upload_task_id)
                    
                    if 'error' in status_result:
                        st.error(f"❌ Status check failed: {status_result['error']}")
                    else:
                        # Extract status
                        current_status = None
                        if isinstance(status_result, dict):
                            if 'status' in status_result:
                                current_status = status_result.get('status')
                            elif 'data' in status_result:
                                data = status_result['data']
                                if isinstance(data, dict):
                                    current_status = data.get('status')
                                elif isinstance(data, list) and len(data) > 0:
                                    current_status = data[0].get('status')
                        
                        if current_status is not None:
                            try:
                                current_status = int(current_status)
                                status_desc = get_status_description(current_status)
                                st.success(f"📊 Current Status: {current_status} - {status_desc}")
                                
                                # Show status-specific actions
                                if current_status == 3:
                                    st.success("✅ Model is ready to submit!")
                                elif current_status in [0, 1]:
                                    st.warning("⏳ Model is still being processed...")
                                elif current_status == 2:
                                    st.error("❌ Model parsing failed - cannot submit (terminal state)")
                                elif current_status == 4:
                                    st.success("🎉 Model already submitted successfully!")
                                elif current_status == 5:
                                    st.warning("⚠️ Previous submission failed - can retry")
                                elif current_status == 6:
                                    st.info("📊 Model analyzed offline - cannot submit")
                                
                            except (ValueError, TypeError):
                                st.warning(f"⚠️ Invalid status value: {current_status}")
                        else:
                            st.warning("⚠️ Could not determine status from response")
                        
                        # Show raw response
                        with st.expander("📋 Raw Status Response"):
                            st.json(status_result)
        else:
            st.info("No active upload task. Start a workflow in the Manual Workflow tab to monitor status.")
    
    with tab3:
        st.header("🔍 Manual Operations")
        
        # Manual task ID input
        manual_task_id = st.text_input("Enter Task ID for manual operations")
        
        if manual_task_id:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Check Status", use_container_width=True):
                    with st.spinner("Checking status..."):
                        status_result = uploader.check_upload_status(manual_task_id)
                        if 'error' in status_result:
                            st.error(f"❌ {status_result['error']}")
                        else:
                            st.success("✅ Status retrieved")
                            st.json(status_result)
                
                if st.button("🔄 Start Polling", use_container_width=True):
                    with st.spinner("Starting polling..."):
                        poll_result = uploader.poll_upload_status_until_complete(
                            manual_task_id,
                            max_attempts=max_poll_attempts,
                            interval_minutes=poll_interval,
                            show_debug=True
                        )
                        if poll_result.get('success'):
                            st.success("✅ Polling completed!")
                            st.json(poll_result)
                        else:
                            st.error(f"❌ Polling failed: {poll_result.get('error')}")
            
            with col2:
                if st.button("🚀 Submit Model", use_container_width=True):
                    with st.spinner("Submitting model..."):
                        submit_result = uploader.submit_parsed_model(
                            manual_task_id,
                            model_name="Manual Submission",
                            prod_cat=288
                        )
                        if 'error' in submit_result:
                            st.error(f"❌ {submit_result['error']}")
                        else:
                            st.success("✅ Model submitted!")
                            st.json(submit_result)
                
                if st.button("🛡️ Safe Submit", use_container_width=True):
                    with st.spinner("Starting safe submission..."):
                        safe_result = uploader.safe_submit_parsed_model(
                            manual_task_id,
                            model_name="Safe Manual Submission",
                            auto_poll=True,
                            max_poll_attempts=max_poll_attempts,
                            poll_interval_minutes=poll_interval,
                            show_debug=True
                        )
                        if safe_result.get('success'):
                            st.success("✅ Safe submission completed!")
                            st.json(safe_result)
                        else:
                            st.error(f"❌ Safe submission failed: {safe_result.get('error')}")
    
    with tab4:
        st.header("📚 Documentation & Help")
        
        st.subheader("🚀 Manual Workflow Guide")
        st.markdown("""
        1. **Enter your API credentials** in the sidebar
        2. **Select a 3D model file** (OBJ, FBX, 3DS, DAE, BLEND, or ZIP)
        3. **Configure model settings** (name, category, etc.)
           - **Position**: Optional field. Leave blank for product uploads, use 99 for lighting design library
        4. **Click 'Start Manual Step-by-Step Workflow'**
        5. **Complete each step manually:**
           - Step 1: Get STS Credentials
           - Step 2: Upload to OSS
           - Step 3: Parse File
           - Step 4: Submit Model
        6. **Monitor progress** in the Status Monitor tab
        """)
        
        st.subheader("📊 Status Codes")
        status_codes = {
            0: "🔄 Generating - Upload is being processed",
            1: "📦 Analyzing - ZIP file is being analyzed",
            2: "❌ Failed - Failed to analyze the ZIP file (terminal)",
            3: "✅ Ready - ZIP file analyzed and ready to submit",
            4: "🎉 Submitted - Model has been submitted successfully",
            5: "⚠️ Failed - Failed to submit the model",
            6: "📊 Offline - ZIP file analyzed offline"
        }
        
        for code, description in status_codes.items():
            st.markdown(f"**{code}**: {description}")
        
        st.subheader("🔧 API Endpoints")
        endpoints = [
            ("1. STS Credentials", "Get OSS upload credentials"),
            ("2. OSS Upload", "Upload file to Alibaba Cloud OSS"),
            ("3. Parse File", "Parse uploaded file for 3D processing"),
            ("4. Status Check", "Monitor parsing progress"),
            ("5. Submit Model", "Submit parsed model to Coohom")
        ]
        
        for endpoint, description in endpoints:
            st.markdown(f"**{endpoint}**: {description}")
        
        st.subheader("💡 Manual Workflow Benefits")
        st.markdown("""
        - **Full control** over each step timing
        - **Detailed feedback** after each operation
        - **Easy debugging** with step-by-step visibility
        - **Retry capability** for individual steps
        - **Error isolation** prevents cascading failures
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("*Coohom 3D Model Upload Workflow - Manual Step-by-Step Control*")

if __name__ == "__main__":
    main()
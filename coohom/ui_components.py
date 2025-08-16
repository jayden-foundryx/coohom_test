"""
UI components and interface functions for the Streamlit app.
"""
import streamlit as st
from datetime import datetime
from file_utils import get_file_info, get_status_description, estimate_upload_time


def render_sidebar(app_key):
    """
    Render the sidebar with upload guidelines and API status.
    
    Args:
        app_key (str): API key for display
    """
    with st.sidebar:
        st.header("📋 Complete Workflow")
        st.markdown("""
        **5-Step Upload Process:**
        
        1. **🔑 Get STS Credentials** (Endpoint #1)
           - Obtain secure upload credentials
        
        2. **☁️ Upload to OSS** (Endpoint #2)
           - Upload file to Alibaba Cloud OSS
        
        3. **🔍 Parse File** (Endpoint #3)
           - Parse and validate uploaded content
        
        4. **📊 Check Status** (Endpoint #4)
           - Monitor parsing progress
        
        5. **🎯 Submit Model** (Endpoint #5)
           - Finalize model submission
        
        **Supported file formats:**
        - ZIP files (recommended)
        - 3D model files (.obj, .fbx, .3ds, .stp, etc.)
        - Texture files (.jpg, .png, .tga, etc.)
        
        **Requirements:**
        - Files will be automatically zipped if not already
        - Maximum file size depends on your Coohom plan
        - Ensure your 3D models are properly formatted
        - **Note:** .stp (STEP) files may need conversion to .skp or .max formats for optimal compatibility
        """)
        
        st.header("🔑 API Status")
        st.success(f"App Key: {app_key[:8]}...")
        
        st.header("📚 Resources")
        st.markdown("""
        - [Coohom API Documentation](https://open.coohom.com/pub/saas/open-platform/document)
        - [Model Upload Requirements](https://www.coohom.com/en_US/helpcenter/article/how-to-upload-my-own-3d-models)
        """)


def render_file_upload_section():
    """
    Render the file upload section of the interface.
    
    Returns:
        uploaded_file: Streamlit uploaded file object or None
    """
    st.header("📁 File Upload")
    
    uploaded_file = st.file_uploader(
        "Choose a 3D model file or ZIP archive",
        type=['zip', 'obj', 'fbx', '3ds', 'dae', 'ply', 'stl', 'stp', 'jpg', 'png', 'tga', 'bmp', 'jpeg', 'tiff'],
        help="Upload your 3D model files. If not a ZIP, it will be automatically compressed."
    )
    
    if uploaded_file is not None:
        file_info = get_file_info(uploaded_file)
        
        if file_info['is_valid']:
            st.success(f"✅ File selected: {file_info['filename']}")
        else:
            st.error(f"❌ Unsupported file type: {file_info['extension']}")
            return None
        
        # Display file information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Size", file_info['size_formatted'])
        with col2:
            st.metric("Type", file_info['extension'].upper())
        with col3:
            est_time = estimate_upload_time(file_info['size_bytes'])
            st.metric("Est. Upload Time", est_time)
        
        # Show detailed file information in expander
        with st.expander("📊 Detailed File Information"):
            st.write(f"**Filename:** {file_info['filename']}")
            st.write(f"**Size:** {file_info['size_bytes']:,} bytes ({file_info['size_formatted']})")
            st.write(f"**MIME Type:** {file_info['type']}")
            st.write(f"**Extension:** {file_info['extension']}")
            st.write(f"**Is ZIP file:** {'Yes' if file_info['is_zip'] else 'No'}")
            
            if not file_info['is_zip']:
                st.info("📦 This file will be automatically compressed into a ZIP archive before upload.")
            
            # Special note for STEP files
            if file_info['extension'].lower() == '.stp':
                st.warning("⚠️ **STEP (.stp) files**: While accepted, Coohom officially supports .skp (SketchUp) and .max (3ds Max) formats for optimal compatibility. Consider converting your STEP file if you encounter processing issues.")
    
    return uploaded_file


def render_model_config_section():
    """
    Render the model configuration section for submission parameters.
    
    Returns:
        dict: Model configuration parameters
    """
    st.header("⚙️ Model Configuration")
    
    with st.expander("🔧 Advanced Model Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            model_name = st.text_input(
                "Model Name",
                value="3D Model",
                help="Name for the model submission"
            )
            
            pos = st.number_input(
                "Position",
                value=99,
                min_value=1,
                max_value=999,
                help="Position value for the model"
            )
            
            prod_cat = st.number_input(
                "Product Category ID",
                value=288,
                min_value=1,
                help="Product category identifier"
            )
        
        with col2:
            brand_good_code = st.text_input(
                "Brand Good Code",
                value="code",
                help="Brand good code identifier"
            )
            
            custom_lib_id = st.text_input(
                "Custom Library ID",
                value="3FO4K6E984C7",
                help="Custom library identifier"
            )
            
            business_cat_ids = st.text_input(
                "Business Category IDs",
                value="3FO4K6E984C7",
                help="Comma-separated business category IDs"
            )
        
        # Parse business category IDs
        business_cat_list = [cat.strip() for cat in business_cat_ids.split(",") if cat.strip()]
        if not business_cat_list:
            business_cat_list = ["3FO4K6E984C7"]
        
        # Brand categories (using the same as business categories for simplicity)
        brand_cats = business_cat_list
        
        st.info("💡 **Note**: Location is hardcoded to 1 as required by the API. Other values use sensible defaults but can be customized.")
    
    return {
        'model_name': model_name,
        'pos': pos,
        'prod_cat': prod_cat,
        'brand_cats': brand_cats,
        'brand_good_code': brand_good_code,
        'custom_lib_id': custom_lib_id,
        'business_cat_ids': business_cat_list
    }


def render_upload_button_section(uploaded_file, uploader, model_config=None):
    """
    Render the upload button and handle the upload process.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        uploader: CoohomUploader instance
        model_config: Model configuration parameters
        
    Returns:
        tuple: (success, upload_task_id)
    """
    if uploaded_file is None:
        st.info("👆 Please select a file to upload")
        return False, None
    
    if st.button("🚀 Upload to Coohom", type="primary", use_container_width=True):
        return handle_upload_process(uploaded_file, uploader, model_config)
    
    return False, None


def handle_upload_process(uploaded_file, uploader, model_config=None):
    """
    Handle the complete upload process with all 5 API endpoints.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        uploader: CoohomUploader instance
        model_config: Model configuration parameters
        
    Returns:
        tuple: (success, upload_task_id)
    """
    from file_utils import create_zip_from_file
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Prepare file
        status_text.text("📦 Preparing file for upload...")
        progress_bar.progress(10)
        
        if uploaded_file.name.lower().endswith('.zip'):
            file_data = uploaded_file.getvalue()
            filename = uploaded_file.name
        else:
            st.info("Creating ZIP archive...")
            file_data, filename = create_zip_from_file(uploaded_file)
        
        # Step 2: Get STS credentials (Endpoint #1)
        status_text.text("🔑 Obtaining upload credentials (Endpoint #1)...")
        progress_bar.progress(20)
        
        sts_data = uploader.get_sts_credentials(filename, show_debug=True)
        
        if not sts_data:
            st.error("❌ Failed to obtain upload credentials")
            # Check if sts_data contains error information
            if isinstance(sts_data, dict) and 'error' in sts_data:
                display_detailed_error(sts_data, "STS Credentials")
            else:
                # Show detailed error information if available
                with st.expander("🔍 Detailed Error Information", expanded=True):
                    st.error("**STS Credentials Error Details:**")
                    st.info("The API call to get STS credentials failed. This could be due to:")
                    st.markdown("""
                    - Invalid API credentials (appKey/appSecret)
                    - Network connectivity issues
                    - Coohom API server issues
                    - Invalid file parameters
                    """)
                    st.warning("Check your credentials.txt file and internet connection.")
            return False, None
        
        progress_bar.progress(30)
        upload_task_id = sts_data.get('uploadTaskId')
        
        # Step 3: Upload to OSS (Endpoint #2)
        status_text.text("☁️ Uploading file to OSS (Endpoint #2)...")
        progress_bar.progress(50)
        
        oss_result = uploader.upload_to_oss(file_data, sts_data, filename)
        
        if not oss_result.get('success'):
            st.error(f"❌ OSS upload failed: {oss_result.get('error')}")
            # Use comprehensive error display if available
            if isinstance(oss_result, dict) and 'error' in oss_result:
                display_detailed_error(oss_result, "OSS Upload")
            else:
                # Show detailed OSS error information
                with st.expander("🔍 OSS Upload Error Details", expanded=True):
                    st.error("**OSS Upload Error Details:**")
                    st.json(oss_result)
                    st.info("**Common OSS Upload Issues:**")
                    st.markdown("""
                    - Missing oss2 library: `pip install oss2`
                    - Invalid STS credentials
                    - Network connectivity issues
                    - File size or format restrictions
                    """)
            return False, None
        
        progress_bar.progress(60)
        
        # Step 4: Parse uploaded file (Endpoint #3)
        status_text.text("🔍 Parsing uploaded file (Endpoint #3)...")
        progress_bar.progress(70)
        
        parse_result = uploader.parse_uploaded_file(upload_task_id)
        
        if 'error' in parse_result:
            st.error(f"❌ File parsing failed: {parse_result['error']}")
            # Use comprehensive error display
            display_detailed_error(parse_result, "File Parsing")
            return False, None
        
        progress_bar.progress(80)
        
        # Step 5: Submit parsed model (Endpoint #5)
        status_text.text("🎯 Submitting parsed model (Endpoint #5)...")
        progress_bar.progress(90)
        
        # Use model configuration if provided, otherwise use defaults
        if model_config:
            submit_result = uploader.safe_submit_parsed_model(
                upload_task_id,
                model_name=model_config.get('model_name', '3D Model'),
                pos=model_config.get('pos', 99),
                prod_cat=model_config.get('prod_cat', 288),
                brand_cats=model_config.get('brand_cats', ["3FO4K6E984C7"]),
                brand_good_code=model_config.get('brand_good_code', 'code'),
                auto_poll=True,  # Enable auto-polling to wait for parsing
                max_poll_attempts=5,
                poll_interval_minutes=2,
                show_debug=True
            )
        else:
            submit_result = uploader.safe_submit_parsed_model(
                upload_task_id,
                auto_poll=True,  # Enable auto-polling to wait for parsing
                max_poll_attempts=5,
                poll_interval_minutes=2,
                show_debug=True
            )
        
        if 'error' in submit_result:
            st.error(f"❌ Model submission failed: {submit_result['error']}")
            # Use comprehensive error display
            display_detailed_error(submit_result, "Model Submission")
            return False, None
        
        # Complete!
        status_text.text("✅ Complete workflow finished successfully!")
        progress_bar.progress(100)
        
        st.success("🎉 Complete workflow finished successfully!")
        st.info(f"📋 Upload Task ID: `{upload_task_id}`")
        
        # Display workflow summary
        with st.expander("📊 Workflow Summary"):
            col1, col2 = st.columns(2)
            with col1:
                st.success("✅ STS Credentials obtained")
                st.success("✅ File uploaded to OSS")
                st.success("✅ File parsed successfully")
                st.success("✅ Model submitted successfully")
            with col2:
                st.info(f"**Task ID:** {upload_task_id}")
                st.info(f"**OSS Path:** {oss_result.get('oss_path', 'N/A')}")
                st.info(f"**Parse Status:** Success")
                st.info(f"**Submit Status:** Success")
        
        # Display all API responses
        with st.expander("🔐 STS Credentials (Endpoint #1)"):
            st.json(sts_data)
        
        with st.expander("☁️ OSS Upload Result (Endpoint #2)"):
            st.json(oss_result)
        
        with st.expander("🔍 Parse Result (Endpoint #3)"):
            st.json(parse_result)
        
        with st.expander("🎯 Submit Result (Endpoint #5)"):
            st.json(submit_result)
        
        return True, upload_task_id
        
    except Exception as e:
        st.error(f"❌ Upload failed: {str(e)}")
        with st.expander("🔍 Error Details"):
            import traceback
            st.text(traceback.format_exc())
        return False, None
    finally:
        progress_bar.empty()
        status_text.empty()


def display_detailed_error(error_data, step_name):
    """
    Display detailed error information in an expandable section.
    
    Args:
        error_data (dict): Error data from API response
        step_name (str): Name of the step that failed
    """
    with st.expander(f"🔍 {step_name} Error Details", expanded=True):
        st.error(f"**{step_name} Failed**")
        
        # Display error message prominently
        if 'error' in error_data:
            st.error(f"**Error:** {error_data['error']}")
        
        # Display error code if available
        if 'error_code' in error_data:
            st.info(f"**Error Code:** {error_data['error_code']}")
        
        # Display endpoint information
        if 'endpoint' in error_data:
            st.info(f"**Failed Endpoint:** {error_data['endpoint']}")
        
        # Display task ID if available
        if 'task_id' in error_data:
            st.info(f"**Task ID:** {error_data['task_id']}")
        
        # Create columns for request and response data
        if 'request_data' in error_data and ('full_response' in error_data or 'response_text' in error_data):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📤 Request Data")
                if 'url' in error_data['request_data']:
                    st.info(f"**URL:** {error_data['request_data']['url']}")
                
                if 'params' in error_data['request_data']:
                    st.json(error_data['request_data']['params'])
                
                if 'request_body' in error_data['request_data']:
                    st.subheader("📦 Request Body")
                    st.json(error_data['request_data']['request_body'])
                
                if 'timestamp' in error_data['request_data']:
                    st.info(f"**Timestamp:** {error_data['request_data']['timestamp']}")
                
                if 'filename' in error_data['request_data']:
                    st.info(f"**Filename:** {error_data['request_data']['filename']}")
            
            with col2:
                st.subheader("📥 Response Data")
                # Display full JSON response if available
                if 'full_response' in error_data:
                    st.json(error_data['full_response'])
                elif 'response_text' in error_data:
                    st.text(error_data['response_text'])
                else:
                    st.info("No response data available")
        else:
            # If no request data, just show response data
            if 'full_response' in error_data:
                st.subheader("📋 Full API Response")
                st.json(error_data['full_response'])
            
            if 'response_text' in error_data:
                st.subheader("📄 Response Text")
                st.text(error_data['response_text'])
        
        # Display additional context based on endpoint
        if 'endpoint' in error_data:
            endpoint = error_data['endpoint']
            if endpoint == 'sts_credentials':
                st.subheader("🔑 STS Credentials Troubleshooting")
                st.markdown("""
                **Common Issues:**
                - Invalid API credentials (appKey/appSecret)
                - Network connectivity issues
                - Coohom API server issues
                - Invalid file parameters
                
                **Solutions:**
                1. Check your `credentials.txt` file
                2. Verify internet connection
                3. Check Coohom API status
                4. Try again later if server issues
                """)
            
            elif endpoint == 'upload_status':
                st.subheader("📊 Status Check Troubleshooting")
                st.markdown("""
                **Common Issues:**
                - Invalid task ID
                - Task expired or not found
                - API server issues
                - Network connectivity problems
                
                **Solutions:**
                1. Verify the task ID is correct
                2. Check if task is still valid
                3. Try again later if server issues
                4. Contact support if persistent
                """)
            
            elif endpoint == 'parse_file':
                st.subheader("🔍 File Parse Troubleshooting")
                st.markdown("""
                **Common Issues:**
                - Invalid file format or corrupted ZIP
                - Missing required 3D model files
                - File size too large
                - Unsupported file types within ZIP
                
                **Solutions:**
                1. Check file format and integrity
                2. Ensure ZIP contains valid 3D models
                3. Reduce file size if too large
                4. Use supported file formats
                """)
            
            elif endpoint == 'submit_model':
                st.subheader("🎯 Model Submit Troubleshooting")
                st.markdown("""
                **Common Issues:**
                - Invalid model parameters (category, position, etc.)
                - Model not properly parsed
                - API validation errors
                - Server-side processing issues
                
                **Solutions:**
                1. Check model configuration parameters
                2. Ensure model was parsed successfully
                3. Verify parameter values are valid
                4. Try again later if server issues
                """)
        
        # Display retry information if available
        if 'retry_attempts' in error_data:
            st.warning(f"**Retry Attempts:** {error_data['retry_attempts']} attempts were made before failure.")
        
        # Display model configuration if available
        if 'model_name' in error_data:
            st.subheader("⚙️ Model Configuration Used")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Name:** {error_data.get('model_name', 'N/A')}")
            with col2:
                st.info(f"**Position:** {error_data.get('pos', 'N/A')}")
            with col3:
                st.info(f"**Category:** {error_data.get('prod_cat', 'N/A')}")
        
        # Add a copy button for debugging
        st.subheader("🔧 Debug Information")
        st.info("**Copy this error data for debugging:**")
        st.code(str(error_data), language="json")


def render_status_section(uploader):
    """
    Render the upload status checking section with all endpoints.
    
    Args:
        uploader: CoohomUploader instance
    """
    st.header("📊 Upload Status & Workflow")
    
    # Check for stored upload task ID
    if 'upload_task_id' in st.session_state:
        current_task_id = st.session_state.upload_task_id
        st.info(f"Current Task ID: `{current_task_id}`")
        
        # Create tabs for different status checks
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📤 Upload Status", "🔍 Parse Status", "🎯 Submit Status", "🔄 Auto Polling", "🛡️ Safe Submit", "📋 Workflow Summary"])
        
        with tab1:
            if st.button("🔍 Check Upload Status (Endpoint #4)", use_container_width=True):
                with st.spinner("Checking upload status..."):
                    status = uploader.check_upload_status(current_task_id)
                    
                    if 'error' in status:
                        st.error(f"❌ Error: {status['error']}")
                        # Use comprehensive error display
                        display_detailed_error(status, "Upload Status Check")
                    else:
                        st.success("✅ Status retrieved successfully")
                        
                        # Display status in a user-friendly way
                        if 'status' in status:
                            status_code = status['status']
                            status_desc = get_status_description(status_code)
                            st.markdown(f"**Status:** {status_desc}")
                        
                        # Show raw response in expander
                        with st.expander("📋 Raw Status Response"):
                            st.json(status)
        
        with tab2:
            if st.button("🔍 Check Parse Status (Endpoint #4)", use_container_width=True):
                with st.spinner("Checking parse status..."):
                    parse_status = uploader.check_upload_status(current_task_id)  # Same endpoint for parse status
                    
                    if 'error' in parse_status:
                        st.error(f"❌ Error: {parse_status['error']}")
                        # Use comprehensive error display
                        display_detailed_error(parse_status, "Parse Status Check")
                    else:
                        st.success("✅ Parse status retrieved successfully")
                        
                        # Show raw response in expander
                        with st.expander("📋 Raw Parse Status Response"):
                            st.json(parse_status)
        
        with tab3:
            if st.button("🎯 Check Submit Status", use_container_width=True):
                st.info("Submit status is typically checked through the main workflow. Use the upload button to see the complete process.")
        
        with tab4:
            st.markdown("""
            **🔄 Automatic Status Polling**
            
            This feature automatically checks the upload status every 2 minutes until it reaches a terminal state:
            - **Status 2**: ❌ Parsing failed (terminal)
            - **Status 4**: ✅ Model submitted successfully
            - **Status 5**: ❌ Model submission failed  
            - **Status 6**: 📊 Model analyzed offline
            
            The polling will stop early if a terminal status is reached, or continue for up to 5 attempts.
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                max_attempts = st.number_input("Max Attempts", min_value=1, max_value=10, value=5, help="Maximum number of status checks")
            with col2:
                interval_minutes = st.number_input("Interval (minutes)", min_value=1, max_value=10, value=2, help="Minutes between each status check")
            
            if st.button("🚀 Start Auto Polling", use_container_width=True, type="primary"):
                with st.spinner(f"🔄 Starting auto polling (every {interval_minutes} minutes, max {max_attempts} attempts)..."):
                    # Create a placeholder for real-time updates
                    status_placeholder = st.empty()
                    progress_placeholder = st.empty()
                    
                    try:
                        # Start the polling
                        result = uploader.poll_upload_status_until_complete(
                            upload_task_id=current_task_id,
                            max_attempts=max_attempts,
                            interval_minutes=interval_minutes,
                            show_debug=True
                        )
                        
                        # Display final results
                        if result.get('success'):
                            if result.get('completed_early'):
                                st.success(f"🎉 Polling completed early! Final status: {result.get('status')}")
                            else:
                                st.warning(f"⚠️ Polling completed after {result.get('final_attempt')} attempts")
                            
                            # Show status history
                            if 'status_history' in result:
                                st.markdown("**📋 Polling History:**")
                                for i, check in enumerate(result['status_history']):
                                    if 'error' in check:
                                        st.error(f"Attempt {i+1}: Error - {check['error']}")
                                    else:
                                        status = check.get('status', 'unknown')
                                        st.info(f"Attempt {i+1}: Status {status}")
                            
                            # Show final response
                            with st.expander("📡 Final Status Response"):
                                st.json(result.get('final_response', result))
                        else:
                            st.error(f"❌ Polling failed: {result.get('error')}")
                            
                    except Exception as e:
                        st.error(f"❌ An error occurred during polling: {str(e)}")
        
        with tab5:
            st.markdown("""
            **🛡️ Safe Model Submission**
            
            This feature prevents the "compressed package not parsed successfully" error by:
            - **Checking status first** before attempting submission
            - **Auto-waiting** for parsing to complete if needed
            - **Only submitting** when the model is ready (status = 3)
            - **Handling all edge cases** automatically
            
            **Status Flow:**
            - **Status 0-1**: Parsing in progress → Auto-wait enabled
            - **Status 2**: Parsing failed → Cannot submit
            - **Status 3**: Ready to submit → Submit immediately
            - **Status 4**: Already submitted → Skip submission
            - **Status 5**: Previous failed → Retry submission
            - **Status 6**: Offline analysis → Cannot submit
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                model_name = st.text_input("Model Name", value="3D Model", help="Name for the submitted model")
                pos_value = st.number_input("Position", min_value=1, max_value=999, value=99, help="Position value for the model")
            with col2:
                prod_cat = st.number_input("Product Category", min_value=1, max_value=999, value=288, help="Product category ID")
                auto_poll = st.checkbox("Auto-poll for parsing completion", value=True, help="Automatically wait for parsing to complete")
            
            if auto_poll:
                col3, col4 = st.columns(2)
                with col3:
                    max_poll_attempts = st.number_input("Max Poll Attempts", min_value=1, max_value=10, value=5, help="Maximum polling attempts")
                with col4:
                    poll_interval = st.number_input("Poll Interval (minutes)", min_value=1, max_value=10, value=2, help="Minutes between status checks")
            else:
                max_poll_attempts = 5
                poll_interval = 2
            
            if st.button("🛡️ Safe Submit Model", use_container_width=True, type="primary"):
                with st.spinner("🛡️ Starting safe submission workflow..."):
                    try:
                        # Start the safe submission
                        result = uploader.safe_submit_parsed_model(
                            upload_task_id=current_task_id,
                            model_name=model_name,
                            pos=pos_value,
                            prod_cat=prod_cat,
                            auto_poll=auto_poll,
                            max_poll_attempts=max_poll_attempts,
                            poll_interval_minutes=poll_interval,
                            show_debug=True
                        )
                        
                        # Display results
                        if result.get('success'):
                            if result.get('submission_skipped'):
                                st.info(f"ℹ️ {result.get('message')}")
                                if result.get('status') == 4:
                                    st.success("✅ Model was already submitted successfully!")
                                elif result.get('status') in [2, 5, 6]:
                                    st.warning(f"⚠️ Model reached terminal status {result.get('status')}")
                            else:
                                st.success("🎉 Model submitted successfully through safe workflow!")
                            
                            # Show workflow details
                            with st.expander("📋 Safe Submission Details"):
                                st.json(result)
                            
                            # Show status check result if available
                            if 'status_check_result' in result:
                                with st.expander("🔍 Initial Status Check"):
                                    st.json(result['status_check_result'])
                            
                            # Show submit result if available
                            if 'submit_result' in result:
                                with st.expander("🚀 Final Submission Result"):
                                    st.json(result['submit_result'])
                            
                            # Show polling result if available
                            if 'poll_result' in result:
                                with st.expander("🔄 Polling Results"):
                                    st.json(result['poll_result'])
                                    
                        else:
                            st.error(f"❌ Safe submission failed: {result.get('error')}")
                            
                            # Show detailed error information
                            with st.expander("🔍 Error Details"):
                                st.json(result)
                            
                            # Show specific error guidance
                            error_code = result.get('error_code')
                            if error_code == 'PARSING_NOT_COMPLETE':
                                st.info("💡 **Solution**: Enable auto-polling or wait for parsing to complete (status = 3)")
                            elif error_code == 'PARSING_FAILED':
                                st.error("💥 **Critical**: Parsing failed - check your ZIP file and try uploading again")
                            elif error_code == 'OFFLINE_ANALYSIS':
                                st.info("ℹ️ **Info**: Model was analyzed offline and cannot be submitted")
                            elif error_code == 'STATUS_CHECK_FAILED':
                                st.warning("⚠️ **Warning**: Could not check current status - verify your task ID")
                            
                    except Exception as e:
                        st.error(f"❌ An error occurred during safe submission: {str(e)}")
                        with st.expander("🔍 Exception Details"):
                            st.exception(e)
        
        with tab6:
            st.markdown("""
            **Complete Workflow Status:**
            
            This task ID represents a complete workflow execution including:
            
            1. ✅ **STS Credentials** (Endpoint #1) - Completed
            2. ✅ **OSS Upload** (Endpoint #2) - Completed  
            3. ✅ **File Parsing** (Endpoint #3) - Completed
            4. 📊 **Status Check** (Endpoint #4) - Available above
            5. ✅ **Model Submission** (Endpoint #5) - Completed
            
            **Next Steps:**
            - Monitor parsing progress using the status check tabs
            - Your 3D model is now available in Coohom's system
            - You can use the Task ID for future reference
            """)
    else:
        st.info("📤 Upload a file first to track status")
    
    # Manual task ID input
    with st.expander("🔍 Check Different Task ID"):
        manual_task_id = st.text_input("Enter Upload Task ID:")
        if manual_task_id and st.button("Check Manual Task ID"):
            with st.spinner("Checking status..."):
                status = uploader.check_upload_status(manual_task_id)
                if 'error' in status:
                    st.error(f"❌ Error: {status['error']}")
                    # Use comprehensive error display for manual check
                    display_detailed_error(status, "Manual Status Check")
                else:
                    st.success("✅ Status retrieved")
                    st.json(status)


def render_upload_history():
    """
    Render the upload history section.
    """
    st.header("📝 Upload History")
    
    if 'upload_history' not in st.session_state:
        st.session_state.upload_history = []
    
    if st.session_state.upload_history:
        # Show recent uploads
        for i, upload in enumerate(reversed(st.session_state.upload_history[-10:])):
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**{upload['filename']}**")
                with col2:
                    st.code(upload['task_id'])
                with col3:
                    st.write(upload['timestamp'])
                
                st.divider()
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.upload_history = []
            st.rerun()
    else:
        st.info("No upload history yet")


def add_to_upload_history(filename, task_id):
    """
    Add an upload record to the session history.
    
    Args:
        filename (str): Name of uploaded file
        task_id (str): Upload task ID
    """
    if 'upload_history' not in st.session_state:
        st.session_state.upload_history = []
    
    upload_record = {
        'filename': filename,
        'task_id': task_id,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    st.session_state.upload_history.append(upload_record)
    
    # Keep only last 20 uploads
    if len(st.session_state.upload_history) > 20:
        st.session_state.upload_history = st.session_state.upload_history[-20:]


def render_page_header():
    """
    Render the main page header and description.
    """
    st.title("🏠 Coohom 3D File Uploader - Complete Workflow")
    st.markdown("""
    Complete 5-step workflow for uploading 3D model files to Coohom's platform using their official API.
    This tool handles the entire process from credential acquisition to final model submission.
    """)
    
    # Add workflow overview
    st.info("""
    💡 **Complete Workflow:** This app implements all 5 Coohom API endpoints in sequence:
    
    1. **🔑 STS Credentials** → 2. **☁️ OSS Upload** → 3. **🔍 File Parsing** → 4. **📊 Status Check** → 5. **🎯 Model Submission**
    
    Your 3D models will be automatically processed and made available in Coohom's system.
    """)


def render_footer():
    """
    Render the footer with additional information.
    """
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        Built with Streamlit • Coohom API Integration • 
        <a href="https://open.coohom.com" target="_blank">Coohom Open Platform</a>
    </div>
    """, unsafe_allow_html=True)

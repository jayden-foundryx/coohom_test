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
        st.header("📋 Upload Guidelines")
        st.markdown("""
        **Supported file formats:**
        - ZIP files (recommended)
        - 3D model files (.obj, .fbx, .3ds, .stp, etc.)
        - Texture files (.jpg, .png, .tga, etc.)
        
        **Requirements:**
        - Files will be automatically zipped if not already
        - Maximum file size depends on your Coohom plan
        - Ensure your 3D models are properly formatted
        - **Note:** .stp (STEP) files may need conversion to .skp or .max formats for optimal compatibility
        
        **Upload Process:**
        1. Select your 3D model file
        2. File gets compressed to ZIP if needed
        3. Upload credentials are obtained
        4. File is uploaded to Coohom's cloud storage
        5. Model is parsed and processed
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


def render_upload_button_section(uploaded_file, uploader):
    """
    Render the upload button and handle the upload process.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        uploader: CoohomUploader instance
        
    Returns:
        tuple: (success, upload_task_id)
    """
    if uploaded_file is None:
        st.info("👆 Please select a file to upload")
        return False, None
    
    if st.button("🚀 Upload to Coohom", type="primary", use_container_width=True):
        return handle_upload_process(uploaded_file, uploader)
    
    return False, None


def handle_upload_process(uploaded_file, uploader):
    """
    Handle the complete upload process with progress indicators.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        uploader: CoohomUploader instance
        
    Returns:
        tuple: (success, upload_task_id)
    """
    from file_utils import create_zip_from_file
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Prepare file
        status_text.text("📦 Preparing file for upload...")
        progress_bar.progress(20)
        
        if uploaded_file.name.lower().endswith('.zip'):
            file_data = uploaded_file.getvalue()
            filename = uploaded_file.name
        else:
            st.info("Creating ZIP archive...")
            file_data, filename = create_zip_from_file(uploaded_file)
        
        # Step 2: Get STS credentials
        status_text.text("🔑 Obtaining upload credentials...")
        progress_bar.progress(40)
        
        sts_data = uploader.get_sts_credentials(filename, show_debug=True)
        
        if not sts_data:
            st.error("❌ Failed to obtain upload credentials")
            return False, None
        
        progress_bar.progress(60)
        upload_task_id = sts_data.get('uploadTaskId')
        
        # Step 3: Display success and credentials
        status_text.text("✅ Upload credentials obtained successfully!")
        progress_bar.progress(100)
        
        st.success("🎉 Upload credentials obtained successfully!")
        st.info(f"📋 Upload Task ID: `{upload_task_id}`")
        
        # Display STS credentials
        with st.expander("🔐 STS Credentials (for advanced users)"):
            st.json(sts_data)
        
        # Note about OSS upload
        st.info("""
        **Next Steps:**
        Upload credentials obtained successfully. To complete the upload:
        
        1. Ensure the OSS library is installed: `pip install oss2`
        2. File will be uploaded to Alibaba Cloud OSS using the provided credentials
        3. Check upload status using the Task ID provided
        """)
        
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


def render_status_section(uploader):
    """
    Render the upload status checking section.
    
    Args:
        uploader: CoohomUploader instance
    """
    st.header("📊 Upload Status")
    
    # Check for stored upload task ID
    if 'upload_task_id' in st.session_state:
        current_task_id = st.session_state.upload_task_id
        st.info(f"Current Task ID: `{current_task_id}`")
        
        if st.button("🔍 Check Status", use_container_width=True):
            with st.spinner("Checking upload status..."):
                status = uploader.check_upload_status(current_task_id)
                
                if 'error' in status:
                    st.error(f"❌ Error: {status['error']}")
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
    st.title("🏠 Coohom 3D File Uploader")
    st.markdown("""
    Upload your 3D model files to Coohom's platform using their official API.
    This tool handles the complete upload workflow including file preparation,
    credential acquisition, and status tracking.
    """)
    
    # Add some helpful info
    st.info("""
    💡 **How it works:** This app demonstrates the Coohom upload API workflow.
    Files are automatically packaged and credentials are obtained for secure upload
    to Coohom's cloud storage system.
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

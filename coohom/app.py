import streamlit as st

# Import our custom modules  
from coohom_api_production import CoohomUploader, load_credentials
from ui_components import (
    render_page_header, render_sidebar, render_file_upload_section,
    render_upload_button_section, render_status_section, 
    render_upload_history, render_footer, add_to_upload_history
)

def main():
    """Main application function with modular UI components."""
    st.set_page_config(
        page_title="Coohom 3D File Uploader",
        page_icon="🏠",
        layout="wide"
    )
    
    # Render page header
    render_page_header()
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        st.stop()
    
    app_key = creds.get('appKey')
    app_secret = creds.get('appSecret')
    
    if not app_key or not app_secret:
        st.error("Missing appKey or appSecret in credentials.txt")
        st.stop()
    
    # Initialize uploader
    uploader = CoohomUploader(app_key, app_secret)
    
    # Render sidebar
    render_sidebar(app_key)
    
    # Main interface layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File upload section
        uploaded_file = render_file_upload_section()
        
        # Upload button and process
        success, upload_task_id = render_upload_button_section(uploaded_file, uploader)
        
        if success and upload_task_id:
            # Store in session state and add to history
            st.session_state.upload_task_id = upload_task_id
            add_to_upload_history(uploaded_file.name, upload_task_id)
    
    with col2:
        # Status checking section
        render_status_section(uploader)
        
        # Upload history
        render_upload_history()
    
    # Render footer
    render_footer()

if __name__ == "__main__":
    main()

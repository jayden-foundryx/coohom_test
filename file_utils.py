"""
Utility functions for file operations and processing.
"""
import os
import tempfile
import zipfile
from datetime import datetime


def create_zip_from_file(uploaded_file):
    """
    Create a ZIP file from the uploaded file if it's not already a ZIP.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        tuple: (zip_data as bytes, zip_filename as string)
    """
    if uploaded_file.name.lower().endswith('.zip'):
        return uploaded_file.getvalue(), uploaded_file.name
    
    # Create a temporary ZIP file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(uploaded_file.name, uploaded_file.getvalue())
        
        temp_zip.seek(0)
        with open(temp_zip.name, 'rb') as f:
            zip_data = f.read()
        
        os.unlink(temp_zip.name)
        
        # Generate new filename
        base_name = os.path.splitext(uploaded_file.name)[0]
        zip_filename = f"{base_name}.zip"
        
        return zip_data, zip_filename


def format_file_size(size_bytes):
    """
    Format file size in human readable format.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = size_bytes
    
    while size >= 1024 and i < len(size_names) - 1:
        size = size / 1024.0
        i += 1
    
    return f"{size:.2f} {size_names[i]}"


def validate_file_type(filename, allowed_extensions=None):
    """
    Validate if file type is allowed for upload.
    
    Args:
        filename (str): Name of the file
        allowed_extensions (list): List of allowed extensions
        
    Returns:
        bool: True if file type is allowed
    """
    if allowed_extensions is None:
        allowed_extensions = [
            '.zip', '.obj', '.fbx', '.3ds', '.dae', '.ply', '.stl',
            '.jpg', '.png', '.tga', '.bmp', '.jpeg', '.tiff', '.stp'
        ]
    
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in allowed_extensions


def get_file_info(uploaded_file):
    """
    Get comprehensive file information for display.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        dict: File information dictionary
    """
    return {
        'filename': uploaded_file.name,
        'size_bytes': uploaded_file.size,
        'size_formatted': format_file_size(uploaded_file.size),
        'type': uploaded_file.type,
        'extension': os.path.splitext(uploaded_file.name)[1].lower(),
        'is_zip': uploaded_file.name.lower().endswith('.zip'),
        'is_valid': validate_file_type(uploaded_file.name)
    }


def create_upload_record(filename, task_id, status='initiated'):
    """
    Create an upload record for tracking.
    
    Args:
        filename (str): Name of uploaded file
        task_id (str): Upload task ID from Coohom
        status (str): Current upload status
        
    Returns:
        dict: Upload record
    """
    return {
        'filename': filename,
        'task_id': task_id,
        'status': status,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'upload_time': datetime.now().isoformat()
    }


def get_status_description(status_code):
    """
    Get human-readable description for Coohom upload status codes.
    
    Args:
        status_code (int): Status code from Coohom API
        
    Returns:
        str: Human-readable status description
    """
    status_descriptions = {
        0: "🔄 Generating - Upload is being processed",
        1: "📦 Analyzing - ZIP file is being analyzed",
        2: "❌ Failed - Failed to analyze the ZIP file",
        3: "✅ Ready - ZIP file analyzed and ready to submit",
        4: "🎉 Submitted - Model has been submitted successfully",
        5: "⚠️ Failed - Failed to submit the model",
        6: "📊 Offline - ZIP file analyzed offline"
    }
    
    return status_descriptions.get(status_code, f"❓ Unknown status: {status_code}")


def estimate_upload_time(file_size_bytes, connection_speed_mbps=10):
    """
    Estimate upload time based on file size and connection speed.
    
    Args:
        file_size_bytes (int): File size in bytes
        connection_speed_mbps (float): Connection speed in Mbps
        
    Returns:
        str: Estimated upload time
    """
    file_size_mb = file_size_bytes / (1024 * 1024)
    upload_time_seconds = (file_size_mb * 8) / connection_speed_mbps
    
    if upload_time_seconds < 60:
        return f"~{upload_time_seconds:.0f} seconds"
    elif upload_time_seconds < 3600:
        minutes = upload_time_seconds / 60
        return f"~{minutes:.1f} minutes"
    else:
        hours = upload_time_seconds / 3600
        return f"~{hours:.1f} hours"

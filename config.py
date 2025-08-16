"""
Configuration settings for the Coohom uploader application.
"""

# Supported file extensions for upload
SUPPORTED_EXTENSIONS = [
    '.zip', '.obj', '.fbx', '.3ds', '.dae', '.ply', '.stl',
    '.jpg', '.png', '.tga', '.bmp', '.jpeg', '.tiff', '.stp',
]

# File size limits (in bytes)
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB
WARN_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# API settings
API_BASE_URL = "https://api.coohom.com"
API_TIMEOUT = 30  # seconds

# Upload status codes and descriptions
UPLOAD_STATUS_CODES = {
    0: "🔄 Generating - Upload is being processed",
    1: "📦 Analyzing - ZIP file is being analyzed", 
    2: "❌ Failed - Failed to analyze the ZIP file",
    3: "✅ Ready - ZIP file analyzed and ready to submit",
    4: "🎉 Submitted - Model has been submitted successfully",
    5: "⚠️ Failed - Failed to submit the model",
    6: "📊 Offline - ZIP file analyzed offline"
}

# UI Configuration
PAGE_CONFIG = {
    "page_title": "Coohom 3D File Uploader",
    "page_icon": "🏠",
    "layout": "wide"
}

# Upload history settings
MAX_HISTORY_ITEMS = 20
DISPLAY_HISTORY_ITEMS = 10

# Default connection speed for upload time estimation (Mbps)
DEFAULT_CONNECTION_SPEED = 10

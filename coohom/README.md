# Coohom 3D File Uploader

A Streamlit web application for uploading 3D model files to the Coohom platform using their OpenAPI.

## Features

- 🏠 **Easy Upload Interface**: Drag and drop 3D files for upload
- 📦 **Auto-ZIP Creation**: Automatically creates ZIP archives from individual files
- 🔐 **Secure Authentication**: Uses your Coohom API credentials
- 📊 **Upload Status Tracking**: Monitor upload progress and status
- 🎯 **Multiple File Formats**: Supports various 3D model and texture formats

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Credentials**: 
   Ensure your `credentials.txt` file contains:
   ```
   appKey=your_app_key
   appSecret=your_app_secret
   api_doc=https://open.coohom.com/pub/saas/open-platform/doc-detail?app_id=1&tag_id=100&node_id=214&doc_tab=doc&node_type=1
   ```

3. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

## Supported File Formats

- **3D Models**: .obj, .fbx, .3ds, .dae, .ply, .stl
- **Textures**: .jpg, .png, .tga, .bmp
- **Archives**: .zip (recommended)

## How It Works

1. **Upload File**: Select your 3D model file or ZIP archive
2. **Auto-Processing**: If not a ZIP, the app automatically creates one
3. **Get Credentials**: Obtains temporary STS credentials from Coohom API
4. **Upload to OSS**: Uploads the file to Alibaba Cloud OSS
5. **Track Status**: Monitor upload progress with task ID

## API Integration

The app integrates with Coohom's OpenAPI endpoints:

- `GET /global/commodity/upload/sts` - Get upload credentials
- `GET /global/commodity/upload/status` - Check upload status

## Requirements

- Python 3.7+
- Streamlit
- Valid Coohom API credentials
- Internet connection for API calls

## Troubleshooting

- **Missing oss2 library**: Install with `pip install oss2`
- **Authentication errors**: Verify your API credentials in `credentials.txt`
- **"认证必传信息缺失" error**: Check that `appkey` and `timestamp` are included in request
- **"request time out" error**: API authentication is working, but the service may be having issues - contact Coohom support
- **Upload failures**: Check file format and size limits

## Authentication Status

✅ **Authentication Working**: The app successfully authenticates with Coohom API using the correct signature method.
⚠️ **API Timeouts**: The Coohom API occasionally returns timeout errors, which indicates server-side processing issues rather than authentication problems.

## Security Notes

- API credentials are loaded from local `credentials.txt`
- STS tokens are temporary and expire automatically
- Files are uploaded to Coohom's secure cloud storage

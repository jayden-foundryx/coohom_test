# Coohom 3D File Uploader - Complete Workflow

A comprehensive Streamlit application that implements the complete Coohom API workflow for uploading and processing 3D model files.

## 🎯 Complete 5-Step Workflow

This application implements all 5 Coohom API endpoints in sequence:

1. **🔑 Get STS Credentials** (Endpoint #1)
   - Obtain secure upload credentials from Coohom API
   - Generates authentication signature using app key and timestamp

2. **☁️ Upload to OSS** (Endpoint #2)
   - Upload file to Alibaba Cloud OSS using STS credentials
   - Handles file compression and secure transfer

3. **🔍 Parse File** (Endpoint #3)
   - Parse and validate uploaded ZIP file content
   - Extract 3D model and texture information

4. **📊 Check Status** (Endpoint #4)
   - Monitor parsing progress and status
   - Track workflow completion

5. **🎯 Submit Model** (Endpoint #5)
   - Finalize model submission to Coohom's system
   - Make 3D model available for use

## 🚀 Features

- **Complete API Integration**: Implements all 5 Coohom API endpoints
- **Streamlit UI**: Modern, responsive web interface
- **Progress Tracking**: Real-time progress indicators for each step
- **Error Handling**: Comprehensive error handling with retry logic
- **File Support**: Automatic ZIP compression for various 3D file formats
- **Status Monitoring**: Track upload and parsing progress
- **Workflow History**: Maintain upload history and task IDs

## 📋 Supported File Formats

- **3D Models**: .obj, .fbx, .3ds, .dae, .ply, .stl, .stp
- **Textures**: .jpg, .png, .tga, .bmp, .jpeg, .tiff
- **Archives**: .zip (recommended)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd coohom
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `credentials.txt` file:
```
appKey=your_app_key_here
appSecret=your_app_secret_here
```

4. Run the Streamlit app:
```bash
streamlit run app.py
```

## 🔧 Configuration

### Required Dependencies
- `streamlit>=1.28.0` - Web interface
- `requests>=2.31.0` - HTTP requests
- `oss2>=2.18.0` - Alibaba Cloud OSS integration

### API Credentials
- **App Key**: Your Coohom application key
- **App Secret**: Your Coohom application secret
- Store in `credentials.txt` file

## 📱 Usage

1. **Upload File**: Select your 3D model file
2. **Automatic Processing**: The app handles all 5 API endpoints automatically
3. **Monitor Progress**: Track each step with progress bars
4. **View Results**: Check detailed results for each endpoint
5. **Status Tracking**: Monitor parsing and submission status
6. **Auto Polling**: Automatically check status until completion

### Status Polling Usage

```python
from coohom_api import CoohomUploader

# Initialize uploader
uploader = CoohomUploader("your_app_key", "your_app_secret")

# Start automatic status polling
result = uploader.poll_upload_status_until_complete(
    upload_task_id="your_task_id",
    max_attempts=5,        # Check up to 5 times
    interval_minutes=2,     # Wait 2 minutes between checks
    show_debug=True         # Show detailed progress
)

# Check results
if result['success']:
    print(f"Final status: {result['status']}")
    print(f"Completed early: {result['completed_early']}")
    print(f"Total attempts: {result['final_attempt']}")

### Safe Submission Usage

```python
from coohom_api import CoohomUploader

# Initialize uploader
uploader = CoohomUploader("your_app_key", "your_app_secret")

# Safe submission with auto-polling
result = uploader.safe_submit_parsed_model(
    upload_task_id="your_task_id",
    model_name="My 3D Model",
    auto_poll=True,           # Automatically wait for parsing
    max_poll_attempts=5,      # Check up to 5 times
    poll_interval_minutes=2,  # Wait 2 minutes between checks
    show_debug=True           # Show detailed progress
)

# Check results
if result['success']:
    if result.get('submission_skipped'):
        print(f"Submission skipped: {result['message']}")
    else:
        print("Model submitted successfully!")
else:
    print(f"Error: {result['error']}")
```

## 🧪 Testing

Run the complete workflow test:
```bash
python3 test_complete_workflow.py
```

## 📊 API Endpoints Implemented

| Endpoint | Description | Method | Status |
|----------|-------------|---------|---------|
| #1 | Get STS credentials for OSS | `GET /global/commodity/upload/sts` | ✅ Implemented |
| #2 | Upload data to OSS | OSS SDK | ✅ Implemented |
| #3 | Parse uploaded ZIP file | `POST /global/commodity/upload/create` | ✅ Implemented |
| #4 | Query parsing status | `GET /global/commodity/upload/status` | ✅ Implemented |
| #4+ | Auto-status polling | `GET /global/commodity/upload/status` (polling) | ✅ Implemented |
| #5+ | Safe model submission | `POST /global/commodity/upload/submit` (safe) | ✅ Implemented |
| #5 | Submit parsed model | `POST /global/commodity/upload/submit` | ✅ Implemented |

## 🔍 Workflow Details

### Signature Generation
The app uses the simplified signature format:
```python
sign_string = f"{app_secret}{appkey}{timestamp}"
signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
```

### Timestamp Format
All timestamps are multiplied by 1000 (milliseconds) as required by the API.

### Error Handling
- Automatic retry logic for timeouts
- Comprehensive error messages
- Graceful fallbacks for failed steps

### Status Polling
- **Automatic Monitoring**: Polls upload status every 2 minutes until completion
- **Terminal States**: Stops when status reaches 2 (Parsing Failed), 4 (Submitted), 5 (Failed), or 6 (Offline)
- **Configurable**: Adjustable polling intervals and maximum attempts
- **Real-time Updates**: Live status tracking with detailed history
- **Early Termination**: Stops polling as soon as a terminal status is reached

### Safe Model Submission
- **Error Prevention**: Automatically prevents "compressed package not parsed successfully" errors
- **Status Validation**: Checks current status before attempting submission
- **Auto-waiting**: Automatically waits for parsing to complete when needed
- **Smart Handling**: Handles all status scenarios (0-6) appropriately
- **Configurable Polling**: Built-in status polling with customizable parameters

## 📚 Resources

- [Coohom API Documentation](https://open.coohom.com/pub/saas/open-platform/document)
- [Model Upload Requirements](https://www.coohom.com/en_US/helpcenter/article/how-to-upload-my-own-3d-models)
- [Alibaba Cloud OSS Documentation](https://www.alibabacloud.com/help/en/object-storage-service)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the complete workflow
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

# Coohom 3D File Uploader - Refactored Structure

## Project Structure

The Streamlit application has been refactored into a modular structure for better maintainability and organization:

```
coohom/
├── app.py                 # Main Streamlit application (simplified)
├── coohom_api.py         # Coohom API client and authentication
├── file_utils.py         # File processing and utility functions
├── ui_components.py      # Streamlit UI components and layouts
├── config.py             # Configuration settings and constants
├── credentials.txt       # API credentials (keep secure)
├── requirements.txt      # Python dependencies
└── README_STRUCTURE.md   # This file
```

## Module Descriptions

### `app.py` - Main Application
- **Purpose**: Entry point for the Streamlit app
- **Key Functions**: 
  - `main()` - Orchestrates the entire application flow
- **Dependencies**: Imports and uses all other custom modules
- **Size**: Reduced from 312 lines to ~67 lines

### `coohom_api.py` - API Client
- **Purpose**: Handles all Coohom API interactions
- **Key Classes**:
  - `CoohomUploader` - Main API client class
- **Key Functions**:
  - `generate_signature()` - API authentication
  - `get_sts_credentials()` - Obtain upload credentials
  - `upload_to_oss()` - Upload files to Alibaba Cloud OSS
  - `check_upload_status()` - Monitor upload progress
  - `submit_parsed_model()` - Final model submission
  - `load_credentials()` - Load API keys from file

### `file_utils.py` - File Operations
- **Purpose**: File processing and validation utilities
- **Key Functions**:
  - `create_zip_from_file()` - Convert files to ZIP format
  - `format_file_size()` - Human-readable file sizes
  - `validate_file_type()` - Check supported file extensions
  - `get_file_info()` - Extract comprehensive file metadata
  - `get_status_description()` - Human-readable status messages
  - `estimate_upload_time()` - Calculate estimated upload duration

### `ui_components.py` - UI Components
- **Purpose**: Streamlit interface components and layouts
- **Key Functions**:
  - `render_page_header()` - Main page title and description
  - `render_sidebar()` - Upload guidelines and API status
  - `render_file_upload_section()` - File selection interface
  - `render_upload_button_section()` - Upload process handling
  - `render_status_section()` - Upload status checking
  - `render_upload_history()` - Display recent uploads
  - `add_to_upload_history()` - Track upload records

### `config.py` - Configuration
- **Purpose**: Centralized configuration and constants
- **Contents**:
  - Supported file extensions
  - File size limits
  - API settings
  - Status code mappings
  - UI configuration
  - Default values

## Benefits of This Structure

### 1. **Maintainability**
- Each module has a single responsibility
- Easy to locate and modify specific functionality
- Reduced code duplication

### 2. **Testability**
- Individual modules can be tested independently
- Clear separation of concerns
- Easier to mock dependencies

### 3. **Readability**
- Main app.py file is now much cleaner
- Function purposes are immediately clear
- Better code organization

### 4. **Scalability**
- Easy to add new features to appropriate modules
- Simple to extend API functionality
- UI components can be reused

### 5. **Debugging**
- Issues can be isolated to specific modules
- Cleaner error tracking
- Better logging possibilities

## Usage

The application usage remains exactly the same. Run with:

```bash
streamlit run app.py
```

## Development

When making changes:

1. **API changes**: Modify `coohom_api.py`
2. **UI changes**: Modify `ui_components.py`
3. **File processing**: Modify `file_utils.py`
4. **Configuration**: Modify `config.py`
5. **Main flow**: Modify `app.py`

## Dependencies

No new dependencies were added. The refactoring only reorganized existing code into logical modules.

## Migration Notes

- All existing functionality is preserved
- Session state and user experience remain unchanged
- No breaking changes to the API or UI
- Credentials file format remains the same

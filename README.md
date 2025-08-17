# 🏠 Coohom Iframe Integration with Streamlit

A comprehensive demonstration of integrating Coohom design tools into your applications using iframe embedding with Single Sign-On (SSO) authentication.

## ✨ Features

- **🔐 SSO Authentication**: Seamless user authentication with Coohom
- **🖼️ Iframe Integration**: Embed Coohom design tools directly into your app
- **👥 User Management**: Register and manage users with unique identifiers
- **🎨 Multiple Design Tools**: Support for various Coohom design tools
- **🏷️ White Label Options**: Customize appearance and branding
- **📱 Responsive Design**: Mobile-friendly interface
- **🔒 Secure**: MD5 signature authentication and token management

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Coohom API credentials (`appkey` and `appsecret`)
- Internet connection for API calls

### Installation

1. **Clone or download the project files**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your credentials**:
   Create a `credentials.txt` file with your Coohom API credentials:
   ```
   appKey=your_app_key_here
   appSecret=your_app_secret_here
   ```

4. **Run the application**:
   ```bash
   streamlit run coohom_iframe_app.py
   ```

## 📖 How to Use

### 1. **Setup API Credentials**
   - Enter your Coohom API credentials in the sidebar
   - Or click "Load from credentials.txt" to load from file
   - Verify API client initialization

### 2. **User Registration**
   - Enter user details (AppUID, Name, Email)
   - Click "Register User" to create Coohom account
   - Verify successful registration

### 3. **Generate SSO Token**
   - Click "Generate SSO Token" for the registered user
   - Token is valid for 7 days
   - Store token securely for production use

### 4. **Iframe Integration**
   - Choose integration type (Project List, Design Tools, etc.)
   - Click "Generate Iframe" to create embeddable URL
   - Copy the generated HTML code for your application

## 🏗️ Integration Types

### **Project List**
- Display user's design projects
- URL: `https://www.coohom.com/pub/saas/apps/project/list`

### **Design Tool 4.0**
- Classic design tool interface
- URL: `https://www.coohom.com/pub/tool/yundesign/cloud?`

### **Design Tool 5.0**
- BIM design tool interface
- URL: `https://www.coohom.com/pub/tool/bim/cloud?`

### **Design Tool K&C**
- Kitchen & Bath design tool
- URL: `https://www.coohom.com/pub/tool/bim/cloud?&redirecturl=/pub/saas/apps/project/list&ctv=kb`

### **Custom URL**
- Embed any Coohom URL of your choice

## 🔧 API Integration

### **Coohom API Client**
The application includes a `CoohomAPI` class that handles:
- MD5 signature generation
- User registration
- SSO authentication
- Error handling

### **Key Methods**
```python
# Initialize API client
api_client = CoohomAPI(appkey, appsecret)

# Register user
result = api_client.register_user(appuid, name, email)

# Generate SSO token
result = api_client.login_user(appuid)
```

### **Authentication Flow**
1. Generate timestamp in milliseconds
2. Create MD5 hash: `md5(appsecret + appkey + appuid + timestamp)`
3. Call Coohom API with parameters
4. Handle response and store token

## 🎯 Use Cases

### **Web Applications**
- Embed Coohom design tools into your website
- Provide seamless design experience
- Maintain user context across sessions

### **Streamlit Apps**
- Create design-focused Streamlit applications
- Integrate 3D visualization capabilities
- Build project management dashboards

### **Enterprise Platforms**
- White-label Coohom tools for your brand
- Integrate with existing user management systems
- Synchronize design data across platforms

### **Mobile Applications**
- Responsive iframe integration
- Touch-friendly design tools
- Cross-platform compatibility

## 🔒 Security Features

- **MD5 Signature**: Secure API authentication
- **Token Expiration**: 7-day token validity
- **User Isolation**: Unique appuid for each user
- **HTTPS Required**: Secure communication
- **Input Validation**: Sanitized user inputs
- **Error Handling**: Secure error messages

## 📱 Responsive Design

The application is designed to work on:
- Desktop computers
- Tablets
- Mobile phones
- Various screen resolutions

## 🛠️ Customization

### **Styling**
- Custom CSS classes for consistent appearance
- Gradient headers and feature cards
- Responsive iframe containers

### **Configuration**
- Configurable API endpoints
- Customizable user management
- Flexible integration options

### **White Labeling**
- Custom domain support
- Brand customization options
- Comprehensive white label features

## 📊 Monitoring and Analytics

### **Performance Metrics**
- API response times
- Iframe loading performance
- User interaction tracking
- Error rate monitoring

### **User Analytics**
- User registration success rates
- Feature adoption metrics
- Session duration tracking
- User satisfaction scores

## 🔍 Troubleshooting

### **Common Issues**

1. **API Credentials Invalid**
   - Verify appkey and appsecret
   - Check Coohom Console access
   - Contact Coohom support

2. **User Registration Fails**
   - Ensure unique appuid
   - Check email format
   - Verify API permissions

3. **SSO Token Generation Fails**
   - Confirm user is registered
   - Check timestamp format
   - Verify signature generation

4. **Iframe Not Loading**
   - Check token validity
   - Verify URL encoding
   - Test redirect URL directly

### **Debug Steps**
1. Check browser console for errors
2. Verify API responses
3. Test API endpoints independently
4. Monitor network requests
5. Check token expiration

## 📚 Documentation

- **`COOHOM_IFRAME_INTEGRATION.md`**: Comprehensive integration guide
- **`TASKS.md`**: Implementation task list
- **Coohom API Docs**: [https://open.coohom.com/pub/saas/open-platform/document](https://open.coohom.com/pub/saas/open-platform/document)

## 🤝 Support

### **Technical Support**
- Review troubleshooting section
- Check API documentation
- Contact Coohom support team

### **Feature Requests**
- Submit through Coohom sales team
- Request API consultation
- Discuss custom integrations

## 📄 License

This project is for demonstration purposes. Follow Coohom's API usage terms and maintain proper security practices.

## 🔄 Updates

- **v1.0**: Initial release with basic integration
- **Future**: Enhanced features and optimizations

---

**Built with ❤️ using Streamlit and Coohom APIs**

*For questions or support, contact the Coohom sales team*

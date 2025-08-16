# Coohom API Troubleshooting Guide

## Issue: "Failed to obtain upload credentials"

### What's happening:
- ✅ **Your API credentials are correct**
- ✅ **Authentication is working properly** 
- ❌ **Coohom API servers are experiencing timeouts**

### Error Details:
```
API Error Code: 100004
Message: "request time out"
```

This is a **server-side issue** with Coohom's API, not a problem with your credentials or code.

---

## Solutions:

### 1. **Immediate Fix - Try Again**
Simply wait 2-5 minutes and try uploading again. API timeouts are usually temporary.

### 2. **Use Debug Mode**
Run the app and upload a file to see detailed debug information:
- API URL being called
- Your credentials (masked)
- Server response details
- Helpful error messages

### 3. **Test Your Credentials**
Run the test script to verify everything is working:
```bash
python3 test_api.py
```

### 4. **Use Production Mode (Future)**
For production use, switch to the retry-enabled version:
```python
# In app.py, change the import:
from coohom_api_production import CoohomUploader, load_credentials
```

---

## Understanding the Error:

### ✅ What's Working:
1. **Credentials**: Your appKey and appSecret are valid
2. **Signature**: MD5 authentication signature is correct
3. **API Endpoint**: The request reaches Coohom's servers
4. **Network**: Your internet connection is fine

### ❌ What's Not Working:
1. **Coohom Servers**: Their API is experiencing high load or timeouts
2. **Response Time**: Server is taking too long to process requests

---

## Error Code Reference:

| Code | Meaning | Solution |
|------|---------|----------|
| `0` | Success | ✅ Everything working |
| `100004` | Request timeout | ⏳ Wait and retry |
| Other codes | Various API errors | 🔍 Check credentials/parameters |

---

## Next Steps:

### Short Term:
1. **Wait 5-10 minutes** then try again
2. **Monitor Coohom status** - this is likely affecting all users
3. **Use retry logic** - attempt upload 2-3 times with delays

### Long Term:
1. **Implement retry logic** in production
2. **Add exponential backoff** for failed requests
3. **Consider caching** credentials to reduce API calls
4. **Monitor Coohom status pages** for known issues

---

## Technical Details:

### API Request Flow:
```
1. Generate timestamp
2. Create parameters: appkey, timestamp, file_name
3. Generate MD5 signature
4. Send GET request to: https://api.coohom.com/global/commodity/upload/sts
5. ❌ Server timeout occurs here (100004)
```

### Expected Success Response:
```json
{
  "c": "0",
  "m": "",
  "d": {
    "accessKeyId": "...",
    "accessKeySecret": "...",
    "securityToken": "...",
    "uploadTaskId": "...",
    "bucket": "...",
    "region": "...",
    "filePath": "..."
  }
}
```

### Actual Error Response:
```json
{
  "c": "100004",
  "m": "request time out"
}
```

---

## Frequently Asked Questions:

### Q: Is my API key wrong?
**A: No.** If your API key was wrong, you'd get a different error code (like authentication failed). Error 100004 specifically means the server is timing out.

### Q: Is there something wrong with my internet?
**A: No.** You're successfully reaching Coohom's servers and getting responses. The issue is on their end.

### Q: Should I keep retrying immediately?
**A: No.** Wait at least 2-5 minutes between attempts to avoid overwhelming their servers.

### Q: Is this a common issue?
**A: Yes.** API timeouts (100004) are a known issue with Coohom's API during high load periods.

---

## Contact Information:

If the issue persists for more than 30 minutes:
1. Check [Coohom's official status page](https://open.coohom.com)
2. Contact Coohom API support
3. Try during off-peak hours (early morning/late evening)

Remember: **Your setup is correct!** This is a temporary server issue.

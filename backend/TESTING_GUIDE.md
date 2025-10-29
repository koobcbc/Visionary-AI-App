# 🧪 Healthcare Diagnostic API Testing Guide

This guide provides comprehensive testing tools for the Healthcare Diagnostic API using your chat ID: `GkV9vizfg2bCTDLRxDtT`

## 📋 Available Testing Tools

### 1. **Postman Collection** (`postman_collection.json`)
Complete Postman collection with 10 test scenarios covering the entire API flow.

### 2. **Python Test Script** (`test_complete_flow.py`)
Comprehensive Python testing script with detailed logging and error handling.

### 3. **Test Runner** (`run_tests.sh`)
Bash script to easily run all tests with custom parameters.

### 4. **Postman Environment** (`postman_environment.json`)
Pre-configured environment variables for Postman.

## 🚀 Quick Start

### Option 1: Using Postman
1. Import `postman_collection.json` into Postman
2. Import `postman_environment.json` as environment
3. Run the collection to test all scenarios

### Option 2: Using Python Script
```bash
# Run with default settings
python3 test_complete_flow.py

# Run with custom parameters
python3 test_complete_flow.py --url http://localhost:3000 --chat-id GkV9vizfg2bCTDLRxDtT
```

### Option 3: Using Test Runner
```bash
# Run with default settings
./run_tests.sh

# Run with custom parameters
./run_tests.sh --url http://localhost:3000 --chat-id GkV9vizfg2bCTDLRxDtT
```

## 📊 Test Scenarios

### 1. **Health Check**
- **Endpoint**: `GET /health`
- **Purpose**: Verify API is running
- **Expected**: Status 200, health status response

### 2. **Text Conversation Flow**
- **Endpoint**: `POST /api/v1/chat/process`
- **Purpose**: Test complete text-based conversation
- **Flow**:
  1. Initial greeting about skin concern
  2. Provide age (25 years old)
  3. Provide gender (female)
  4. Describe symptoms (growing mole, itching, no family history)
  5. Verify AI requests image upload

### 3. **Image Analysis**
- **Endpoint**: `POST /api/v1/chat/process`
- **Purpose**: Test image upload and CV analysis
- **Payload**: Test image URL with skin mole
- **Expected**: CV analysis results, warning/report status

### 4. **Final Report Generation**
- **Endpoint**: `POST /api/v1/chat/process`
- **Purpose**: Generate comprehensive final report
- **Trigger**: Message "generate_report"
- **Expected**: Status "report", comprehensive analysis

### 5. **Dental Flow**
- **Endpoint**: `POST /api/v1/chat/process`
- **Purpose**: Test dental/oral health speciality
- **Payload**: Oral health concern with speciality="dental"
- **Expected**: Dental-specific responses

### 6. **Error Handling**
- **Scenarios**:
  - Invalid chat ID
  - Invalid image URL
  - Malformed requests
- **Expected**: Graceful error handling

## 🔧 API Parameters

### Main API Endpoint: `POST /api/v1/chat/process`

**Required Parameters**:
```json
{
  "message": "string (empty or text)",
  "image_url": "string (empty or URL)",
  "user_id": "string",
  "chat_id": "string",
  "type": "text" or "image",
  "speciality": "dental" or "skin"
}
```

**Response Format**:
```json
{
  "response": "string (markdown format)",
  "status": "response" | "warning" | "report",
  "metadata": {
    "cv_result": {...},
    "extracted_metadata": {...},
    "session_info": {...}
  }
}
```

## 📈 Expected Test Results

### ✅ **Successful Flow**:
1. **Health Check**: 200 OK
2. **Text Messages**: Status "response", proper conversation flow
3. **Image Upload**: Status "warning" or "report", CV analysis present
4. **Final Report**: Status "report", comprehensive analysis
5. **Dental Flow**: Status "response", dental-specific content
6. **Error Handling**: Graceful degradation, informative messages

### 📊 **Test Metrics**:
- **Response Time**: < 5 seconds per request
- **Success Rate**: > 95%
- **Error Handling**: All errors handled gracefully
- **Data Quality**: Responses contain relevant medical information

## 🐛 Troubleshooting

### Common Issues:

1. **API Not Running**:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

2. **Missing Dependencies**:
   ```bash
   pip install requests
   ```

3. **Firebase Connection Issues**:
   - Check `.env` file configuration
   - Verify Firebase credentials
   - Ensure service account JSON is present

4. **CV Model Issues**:
   - Check `SKIN_CV_API` endpoint
   - Verify image URL accessibility
   - Check CV model service status

### Debug Mode:
```bash
# Run with debug output
python3 test_complete_flow.py --url http://localhost:8080 --verbose
```

## 📝 Test Data

### Test Chat ID: `GkV9vizfg2bCTDLRxDtT`
### Test User ID: `capstone_user_123`
### Test Image URL: `https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400`

## 🎯 Success Criteria

- [ ] All health checks pass
- [ ] Text conversation flows naturally
- [ ] Image analysis returns CV results
- [ ] Final report is comprehensive
- [ ] Dental flow works correctly
- [ ] Error handling is graceful
- [ ] Response times are acceptable
- [ ] All status codes are correct

## 📞 Support

If tests fail:
1. Check API server logs
2. Verify environment configuration
3. Test individual endpoints
4. Check Firebase/Firestore connectivity
5. Verify CV model endpoints

---

**Happy Testing! 🚀**

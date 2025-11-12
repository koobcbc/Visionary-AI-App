# Supervisor Agent - End-to-End Testing Guide

This guide covers testing the Supervisor Agent using both Python scripts and Postman collections.

## Table of Contents
1. [Python Test Script](#python-test-script)
2. [Postman Collection](#postman-collection)
3. [Test Scenarios](#test-scenarios)
4. [Troubleshooting](#troubleshooting)

---

## Python Test Script

### Quick Start

```bash
# Basic test suite (health checks + text flow)
python test_e2e_flow.py --url http://localhost:8080

# Test with image upload
python test_e2e_flow.py --url https://supervisor-agent.uc.a.run.app \
    --image-url gs://your-bucket/path/to/image.jpg

# Complete end-to-end flow only
python test_e2e_flow.py --url http://localhost:8080 --e2e-only \
    --image-url gs://your-bucket/image.jpg

# Custom user and chat IDs
python test_e2e_flow.py --url http://localhost:8080 \
    --user-id user123 --chat-id chat456
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url` | Supervisor agent URL | `http://localhost:8080` |
| `--user-id` | User ID for testing | Auto-generated |
| `--chat-id` | Chat ID for testing | Auto-generated |
| `--image-url` | Image URL (gs:// or https://) for image tests | None |
| `--e2e-only` | Run only complete end-to-end flow | False |
| `--include-image` | Include image upload tests in full suite | False |

### Test Suites

The script includes the following test suites:

1. **Health Checks** - Tests `/health` and `/ready` endpoints
2. **Text Flow (Skin)** - Complete conversation flow for skin specialty
3. **Text Flow (Oral)** - Complete conversation flow for oral specialty
4. **Image Upload Flow** - Tests Vision Agent → Reporting Agent pipeline
5. **Security Features** - Tests domain grounding, prompt injection detection
6. **Error Handling** - Tests validation and error responses

### Example Output

```
================================================================================
🧪 SUPERVISOR AGENT COMPREHENSIVE TEST SUITE
================================================================================
Timestamp: 2024-01-15T10:30:00.000Z
Supervisor URL: http://localhost:8080
User ID: test_user_1234567890
Chat ID: test_chat_1234567890
================================================================================

================================================================================
Running test suite: Health Checks
================================================================================

✅ PASS Health Check
    Status: ok

✅ PASS Ready Check
    Status: ready

================================================================================
Running test suite: Text Flow (Skin)
================================================================================

✅ PASS Initial Message
✅ PASS Age/Gender Response
✅ PASS Location Response
✅ PASS Symptoms Response
✅ PASS Medical History Response
✅ PASS Image Request Ready

================================================================================
📊 TEST SUMMARY
================================================================================
Total Tests: 8
✅ Passed: 8
❌ Failed: 0
Success Rate: 100.0%

🎉 ALL TESTS PASSED!
```

---

## Postman Collection

### Importing the Collection

1. Open Postman
2. Click **Import** button
3. Select `Supervisor_Agent_Tests.postman_collection.json`
4. The collection will appear in your workspace

### Setting Up Environment Variables

Create a Postman environment with the following variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `supervisor_url` | Base URL of supervisor agent | `http://localhost:8080` |
| `user_id` | User ID for testing | `test_user_123` |
| `chat_id` | Chat ID for testing | `test_chat_456` |
| `image_url` | Image URL for image tests | `gs://bucket/image.jpg` |

**Note:** `user_id` and `chat_id` are auto-generated if not set.

### Running Tests

#### Manual Execution

1. Select a request from the collection
2. Ensure environment variables are set
3. Click **Send**
4. Check the **Test Results** tab for automated assertions

#### Collection Runner

1. Click on the collection name
2. Click **Run** button
3. Select which requests to run
4. Click **Run Supervisor Agent - End-to-End Tests**
5. View results in the test run summary

### Test Folders

The collection is organized into folders:

1. **Health Checks**
   - Health Check
   - Ready Check

2. **Text Message Flow - Skin**
   - 1. Initial Complaint
   - 2. Provide Age and Gender
   - 3. Describe Body Location
   - 4. Describe Symptoms
   - 5. Medical History

3. **Image Upload Flow**
   - Upload Image (tests Vision → Reporting pipeline)

4. **Oral Health Flow**
   - Initial Oral Complaint

5. **Security Tests**
   - Domain Grounding - Off Topic
   - Valid Medical Message
   - Prompt Injection Attempt

6. **Error Handling**
   - Invalid Request Type
   - Missing Required Fields
   - Invalid Image URL

### Automated Assertions

Each request includes automated tests that verify:
- HTTP status code
- Response structure
- Required fields presence
- Business logic (e.g., diagnosis present for images)

---

## Test Scenarios

### Scenario 1: Complete Skin Consultation Flow

**Objective:** Test the full journey from initial complaint to report generation.

**Steps:**
1. Send initial complaint about skin issue
2. Provide age and gender
3. Describe body location
4. Describe symptoms (itch, pain, growth)
5. Provide medical history
6. Upload image when system is ready
7. Verify diagnosis and report are generated

**Expected Results:**
- All text messages are processed successfully
- System requests image after gathering required information
- Image upload triggers Vision Agent → Reporting Agent flow
- Final response includes diagnosis and structured report

### Scenario 2: Security Features

**Objective:** Verify security guardrails are working.

**Tests:**
1. **Domain Grounding:** Send off-topic message (e.g., "How do I fix my computer?")
   - Expected: Rejected with `off_topic` error

2. **Valid Medical:** Send valid medical question
   - Expected: Processed normally

3. **Prompt Injection:** Attempt prompt injection
   - Expected: Rejected with security error

### Scenario 3: Error Handling

**Objective:** Ensure proper error responses for invalid inputs.

**Tests:**
1. Invalid request type
2. Missing required fields
3. Invalid image URL format

**Expected:** All should return appropriate HTTP error codes (400+)

### Scenario 4: Oral Health Flow

**Objective:** Test oral/dental specialty routing.

**Steps:**
1. Send oral health complaint with `speciality: "oral"`
2. Verify routing to Oral Agent instead of Skin Agent
3. Verify response is contextually appropriate for oral health

---

## Troubleshooting

### Common Issues

#### 1. Connection Errors

**Symptom:** `Connection refused` or timeout errors

**Solution:**
- Verify supervisor agent is running
- Check the URL is correct (include protocol: `http://` or `https://`)
- Check firewall/network settings
- For local testing, ensure agent is listening on correct port

#### 2. Authentication Errors

**Symptom:** 401 or 403 responses

**Solution:**
- If authentication is required, add headers to requests
- Check API keys or tokens in environment variables

#### 3. Agent URL Not Configured

**Symptom:** `502 Bad Gateway` or downstream agent errors

**Solution:**
- Verify all agent URLs are set in environment variables:
  - `SKIN_AGENT_URL`
  - `ORAL_AGENT_URL`
  - `VISION_AGENT_URL`
  - `REPORTING_AGENT_URL`
- Test downstream agents independently

#### 4. Image Upload Fails

**Symptom:** Image upload returns error

**Possible Causes:**
- Invalid image URL format (must be `gs://` or `https://`)
- Image doesn't exist or isn't accessible
- Gemini validation fails (image not suitable for skin/oral)
- Vision Agent or Reporting Agent not responding

**Debugging:**
- Check image URL is accessible
- Verify image is actually a skin/oral health image
- Check logs of Vision and Reporting agents

#### 5. History Not Persisting

**Symptom:** Agent doesn't remember previous messages

**Solution:**
- Ensure `history` array is being sent with each request
- Check that history is in correct format: `[{"role": "user", "content": "..."}, ...]`
- Verify chat_id is consistent across requests

#### 6. Domain Grounding (Updated - Context-Aware)

**Current Behavior:** Domain grounding is now context-aware and will allow personal information (age, gender, etc.) when it's part of an ongoing medical conversation.

**How it works:**
- If a message contains personal information keywords (age, gender, height, weight, etc.)
- And there's medical context in the recent conversation history
- Then the personal information is allowed

**Examples that now work:**
- ✅ After "I have a rash on my arm" → "I'm 35 years old, male" (allowed)
- ✅ After "My gums are bleeding" → "I'm 28 years old, female" (allowed)
- ❌ "I'm 35 years old, male" (standalone, no medical context - rejected)

**Note:** The system still blocks truly off-topic messages. Personal information is only allowed when part of an active medical conversation.

### Debug Mode

Enable verbose logging in the Python script by modifying:

```python
# Add debug prints
print(f"📤 Sending payload: {json.dumps(payload, indent=2)}")
print(f"📥 Received response: {json.dumps(result, indent=2)}")
```

### Checking Logs

**Supervisor Agent Logs:**
```bash
# Local (if using uvicorn)
# Check terminal output

# Cloud Run
gcloud run services logs read supervisor-agent --limit 100
```

**Agent Response Inspection:**

In the test script, responses are logged. Look for:
- `success: false` - Request failed
- `error` field - Error details
- `metadata.error_type` - Type of error (security, validation, etc.)

---

## Best Practices

1. **Start Small:** Test health checks first, then progress to full flows
2. **Use Consistent IDs:** Use the same `chat_id` and `user_id` for related tests
3. **Check Responses:** Always verify response structure matches expected format
4. **Test Error Cases:** Don't just test happy paths - test error handling too
5. **Clean Up:** After testing, consider cleaning up test data in Firestore

---

## Integration with CI/CD

### Example GitHub Actions

```yaml
name: Test Supervisor Agent

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install requests
      
      - name: Run tests
        env:
          SUPERVISOR_URL: ${{ secrets.SUPERVISOR_URL }}
        run: |
          python backend/agents/supervisor_agent/test_e2e_flow.py \
            --url $SUPERVISOR_URL
```

---

## Additional Resources

- **API Documentation:** See `start_guide.md` for API details
- **Deployment:** See deployment docs for environment setup
- **Architecture:** See project structure docs for system overview

---

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Review this guide's troubleshooting section
3. Verify all environment variables are set correctly
4. Test downstream agents independently

Happy Testing! 🚀


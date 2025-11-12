"""
Test Script for Supervisor Agent
Tests the complete flow: text messages → image upload → diagnosis
"""

import requests
import time
import json
from datetime import datetime

# Configuration
SUPERVISOR_URL = "http://localhost:8080"  # Change to your deployed URL
USER_ID = f"test_user_{int(time.time())}"
CHAT_ID = f"test_chat_{int(time.time())}"
SPECIALITY = "skin"

def print_separator():
    print("\n" + "="*80 + "\n")

def print_response(step, response_json):
    """Pretty print API response"""
    print(f"📨 STEP {step} RESPONSE:")
    print(f"Success: {response_json.get('success')}")
    print(f"Response: {response_json.get('response')[:200]}...")
    
    metadata = response_json.get('metadata', {})
    print(f"\nMetadata:")
    print(f"  • State: {metadata.get('message_state')}")
    print(f"  • Ready for images: {metadata.get('ready_for_images')}")
    print(f"  • Completeness: {metadata.get('information_completeness'):.0%}")
    print(f"  • Messages: {metadata.get('messages_count')}")
    print_separator()

def test_health_check():
    """Test health endpoint"""
    print("🏥 Testing Health Check...")
    try:
        response = requests.get(f"{SUPERVISOR_URL}/health")
        response.raise_for_status()
        print("✅ Health check passed!")
        print(json.dumps(response.json(), indent=2))
        print_separator()
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def send_text_message(message, step):
    """Send a text message"""
    print(f"💬 STEP {step}: Sending message...")
    print(f"Message: {message}")
    
    payload = {
        "message": message,
        "image_url": "",
        "user_id": USER_ID,
        "chat_id": CHAT_ID,
        "type": "text",
        "speciality": SPECIALITY
    }
    
    try:
        response = requests.post(
            f"{SUPERVISOR_URL}/api/v1/main",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        print_response(step, result)
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None

def send_image(image_url, step):
    """Send an image"""
    print(f"📸 STEP {step}: Uploading image...")
    print(f"Image URL: {image_url}")
    
    payload = {
        "message": "",
        "image_url": image_url,
        "user_id": USER_ID,
        "chat_id": CHAT_ID,
        "type": "image",
        "speciality": SPECIALITY
    }
    
    try:
        response = requests.post(
            f"{SUPERVISOR_URL}/api/v1/main",
            json=payload,
            timeout=90
        )
        response.raise_for_status()
        result = response.json()
        print_response(step, result)
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None

def get_session_state():
    """Get current session state"""
    print("📊 Fetching session state...")
    try:
        response = requests.get(f"{SUPERVISOR_URL}/api/v1/session/{CHAT_ID}")
        response.raise_for_status()
        result = response.json()
        print("✅ Session state retrieved:")
        print(json.dumps(result, indent=2))
        print_separator()
        return result
    except Exception as e:
        print(f"❌ Error getting session: {e}")
        return None

def run_complete_flow():
    """Run complete test flow"""
    print("🚀 Starting Complete Flow Test")
    print(f"Supervisor URL: {SUPERVISOR_URL}")
    print(f"User ID: {USER_ID}")
    print(f"Chat ID: {CHAT_ID}")
    print_separator()
    
    # 1. Health check
    if not test_health_check():
        print("⚠️ Health check failed. Is the server running?")
        return
    
    # 2. Initial message
    step = 1
    result = send_text_message(
        "I have a rash on my arm that appeared 3 days ago",
        step
    )
    if not result or not result.get('success'):
        print("❌ Flow stopped at step 1")
        return
    
    time.sleep(2)
    
    # 3. Provide age and gender
    step += 1
    result = send_text_message(
        "I'm 35 years old, male",
        step
    )
    if not result:
        return
    
    time.sleep(2)
    
    # 4. Describe body region
    step += 1
    result = send_text_message(
        "It's on my left forearm, about halfway up",
        step
    )
    if not result:
        return
    
    time.sleep(2)
    
    # 5. Describe symptoms
    step += 1
    result = send_text_message(
        "It's very itchy, hurts a bit, and seems to be growing",
        step
    )
    if not result:
        return
    
    time.sleep(2)
    
    # 6. Additional information
    step += 1
    result = send_text_message(
        "No skin cancer history, no family history of cancer",
        step
    )
    if not result:
        return
    
    time.sleep(2)
    
    # 7. Duration
    step += 1
    result = send_text_message(
        "It's been there for about 3 days now and getting worse",
        step
    )
    if not result:
        return
    
    time.sleep(2)
    
    # Check if ready for image
    metadata = result.get('metadata', {})
    if not metadata.get('ready_for_images'):
        print("⚠️ Not yet ready for images, continue conversation...")
        
        step += 1
        result = send_text_message(
            "Should I upload a picture?",
            step
        )
        time.sleep(2)
        metadata = result.get('metadata', {})
    
    if metadata.get('ready_for_images'):
        print("✅ System is ready for image upload!")
        
        # 8. Upload image (using test image from chat)
        step += 1
        # Note: Replace with actual Firebase Storage URL from your chat
        image_url = "gs://your-bucket/test-image.jpg"
        print(f"\n⚠️  IMPORTANT: Replace image_url with actual Firebase Storage URL")
        print(f"Current URL: {image_url}")
        print(f"Example: gs://healthcare-images/chats/{CHAT_ID}/image.jpg")
        print_separator()
        
        proceed = input("Do you have an image URL ready? (y/n): ")
        if proceed.lower() == 'y':
            custom_url = input("Enter Firebase Storage URL (or press Enter to skip): ")
            if custom_url:
                image_url = custom_url
                result = send_image(image_url, step)
        else:
            print("⚠️ Skipping image upload step")
    else:
        print("❌ System not ready for images after conversation")
    
    # Get final session state
    print_separator()
    get_session_state()
    
    print("\n✅ Complete flow test finished!")
    print(f"Chat ID: {CHAT_ID}")
    print(f"You can view this chat in Firestore: chats/{CHAT_ID}")

def run_quick_test():
    """Quick test of basic functionality"""
    print("⚡ Running Quick Test")
    print_separator()
    
    # Health check
    if not test_health_check():
        return
    
    # Single message
    result = send_text_message("I have a rash", 1)
    if result and result.get('success'):
        print("✅ Quick test passed!")
    else:
        print("❌ Quick test failed")

if __name__ == "__main__":
    print("="*80)
    print("SUPERVISOR AGENT TEST SCRIPT")
    print("="*80)
    print("\nOptions:")
    print("1. Quick Test (health check + single message)")
    print("2. Complete Flow Test (full conversation + image)")
    print("3. Health Check Only")
    print("4. Custom Test")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        run_quick_test()
    elif choice == "2":
        run_complete_flow()
    elif choice == "3":
        test_health_check()
    elif choice == "4":
        print("\nCustom test mode")
        custom_message = input("Enter your message: ")
        send_text_message(custom_message, 1)
    else:
        print("Invalid choice")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
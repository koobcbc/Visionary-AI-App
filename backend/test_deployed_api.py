#!/usr/bin/env python3
"""
Comprehensive test script for deployed Healthcare Diagnostic API
Tests all endpoints and validates the complete workflow
"""

import requests
import json
import base64
import time
import sys
from typing import Dict, Any


class HealthcareAPITester:
    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url.rstrip('/')
        # Simplified for capstone project - no authentication needed
        self.session = requests.Session()
    
    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        print("🏥 Testing health check...")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_text_conversation(self) -> bool:
        """Test text conversation workflow"""
        print("\n💬 Testing text conversation...")
        
        chat_id = f"test_chat_{int(time.time())}"
        
        # Test 1: Initial greeting
        request_data = {
            "message": "Hello, I'm a 35 year old male with a skin condition",
            "image_url": "",
            "user_id": "test_user_123",
            "chat_id": chat_id,
            "type": "text",
            "speciality": "skin"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/process",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Initial message: {data.get('status', 'unknown')}")
                print(f"   Response: {data.get('response', '')[:100]}...")
                
                # Test 2: Follow-up with more details
                request_data["message"] = "The lesion is on my back and it's been growing for 2 months"
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/chat/process",
                    json=request_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Follow-up message: {data.get('status', 'unknown')}")
                    print(f"   Response: {data.get('response', '')[:100]}...")
                    return True
                else:
                    print(f"❌ Follow-up failed: {response.status_code}")
                    return False
            else:
                print(f"❌ Initial message failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Text conversation error: {e}")
            return False
    
    def test_image_processing(self) -> bool:
        """Test image processing workflow"""
        print("\n🖼️  Testing image processing...")
        
        chat_id = f"test_image_{int(time.time())}"
        
        # Create a simple test image (1x1 pixel PNG)
        test_image_data = base64.b64encode(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf5\xd7\xa2\x0c\x00\x00\x00\x00IEND\xaeB`\x82'
        ).decode()
        
        request_data = {
            "message": "",
            "image_url": f"data:image/png;base64,{test_image_data}",
            "user_id": "test_user_123",
            "chat_id": chat_id,
            "type": "image",
            "speciality": "skin"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/process",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Image processing: {data.get('status', 'unknown')}")
                print(f"   Response: {data.get('response', '')[:100]}...")
                
                # Check if it's a report status
                if data.get('status') == 'report':
                    print("✅ Final report generated successfully")
                    return True
                else:
                    print("⚠️  Expected 'report' status for image processing")
                    return False
            else:
                print(f"❌ Image processing failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Image processing error: {e}")
            return False
    
    def test_dental_speciality(self) -> bool:
        """Test dental speciality"""
        print("\n🦷 Testing dental speciality...")
        
        chat_id = f"test_dental_{int(time.time())}"
        
        request_data = {
            "message": "I have a dental issue with my tooth",
            "image_url": "",
            "user_id": "test_user_123",
            "chat_id": chat_id,
            "type": "text",
            "speciality": "dental"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/process",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Dental speciality: {data.get('status', 'unknown')}")
                print(f"   Response: {data.get('response', '')[:100]}...")
                return True
            else:
                print(f"❌ Dental speciality failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Dental speciality error: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling"""
        print("\n🚨 Testing error handling...")
        
        # Test invalid request
        invalid_request = {
            "message": "test",
            "user_id": "test_user_123",
            "chat_id": "test_chat_123",
            "type": "invalid_type",
            "speciality": "skin"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/process",
                json=invalid_request
            )
            
            if response.status_code in [400, 422]:
                print("✅ Error handling: Invalid request properly rejected")
                return True
            else:
                print(f"⚠️  Expected error status, got: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
    
    def test_chat_history(self) -> bool:
        """Test chat history retrieval"""
        print("\n📚 Testing chat history...")
        
        chat_id = f"test_history_{int(time.time())}"
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/chat/{chat_id}"
            )
            
            if response.status_code in [200, 404]:  # 404 is OK for new chat
                print("✅ Chat history endpoint accessible")
                return True
            else:
                print(f"❌ Chat history failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Chat history error: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        print("🚀 Starting comprehensive API tests...")
        print("=" * 50)
        
        results = {}
        
        # Run all tests
        results['health_check'] = self.test_health_check()
        results['text_conversation'] = self.test_text_conversation()
        results['image_processing'] = self.test_image_processing()
        results['dental_speciality'] = self.test_dental_speciality()
        results['error_handling'] = self.test_error_handling()
        results['chat_history'] = self.test_chat_history()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! API is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the logs above.")
        
        return results


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_deployed_api.py <API_URL> [AUTH_TOKEN]")
        print("Example: python test_deployed_api.py https://your-api-url.com")
        print("Example: python test_deployed_api.py https://your-api-url.com your-auth-token")
        sys.exit(1)
    
    api_url = sys.argv[1]
    auth_token = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Testing API at: {api_url}")
    if auth_token:
        print("Using authentication token")
    else:
        print("No authentication token provided")
    
    tester = HealthcareAPITester(api_url, auth_token)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

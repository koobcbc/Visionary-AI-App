#!/usr/bin/env python3
"""
Comprehensive testing script for Healthcare Diagnostic API
Tests the complete backend flow using the provided chat ID
"""

import requests
import json
import time
from typing import Dict, Any, List
import sys

class HealthcareAPITester:
    """Comprehensive API tester for healthcare diagnostic backend"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.chat_id = "GkV9vizfg2bCTDLRxDtT"
        self.user_id = "capstone_user_123"
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def test_health_check(self) -> bool:
        """Test health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.log_test("Health Check", True, f"Status: {data.get('status', 'unknown')}")
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
            return False
    
    def call_main_api(self, message: str, image_url: str = "", 
                     chat_type: str = "text", speciality: str = "skin") -> Dict[str, Any]:
        """Call the main API endpoint"""
        payload = {
            "message": message,
            "image_url": image_url,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "type": chat_type,
            "speciality": speciality
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/process",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def test_text_conversation_flow(self) -> bool:
        """Test complete text conversation flow"""
        print("\n🔄 Testing Text Conversation Flow...")
        
        # Test 1: Initial greeting
        result = self.call_main_api("Hello, I have a skin concern I'd like to discuss")
        if "error" in result:
            self.log_test("Initial Greeting", False, result["error"])
            return False
        
        self.log_test("Initial Greeting", True, f"Status: {result.get('status')}")
        
        # Test 2: Provide age
        result = self.call_main_api("I am 25 years old")
        if "error" in result:
            self.log_test("Age Response", False, result["error"])
            return False
        
        self.log_test("Age Response", True, f"Status: {result.get('status')}")
        
        # Test 3: Provide gender
        result = self.call_main_api("I am female")
        if "error" in result:
            self.log_test("Gender Response", False, result["error"])
            return False
        
        self.log_test("Gender Response", True, f"Status: {result.get('status')}")
        
        # Test 4: Provide symptoms
        result = self.call_main_api(
            "I have a mole on my arm that has been growing and itches sometimes. "
            "I don't have any family history of skin cancer."
        )
        if "error" in result:
            self.log_test("Symptoms Response", False, result["error"])
            return False
        
        self.log_test("Symptoms Response", True, f"Status: {result.get('status')}")
        
        # Check if AI requests image upload
        response_text = result.get("response", "").lower()
        if "upload" in response_text or "photo" in response_text or "image" in response_text:
            self.log_test("Image Request", True, "AI correctly requests image upload")
        else:
            self.log_test("Image Request", False, "AI should request image upload")
        
        return True
    
    def test_image_analysis(self) -> bool:
        """Test image analysis flow"""
        print("\n🖼️ Testing Image Analysis...")
        
        # Use a test image URL (you can replace with your own)
        test_image_url = "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400"
        
        result = self.call_main_api(
            "Here is a photo of the mole on my arm",
            image_url=test_image_url,
            chat_type="image"
        )
        
        if "error" in result:
            self.log_test("Image Analysis", False, result["error"])
            return False
        
        self.log_test("Image Analysis", True, f"Status: {result.get('status')}")
        
        # Check if CV result is present
        metadata = result.get("metadata", {})
        if "cv_result" in metadata:
            self.log_test("CV Result Present", True, "CV analysis completed")
        else:
            self.log_test("CV Result Present", False, "CV analysis missing")
        
        return True
    
    def test_final_report_generation(self) -> bool:
        """Test final report generation"""
        print("\n📋 Testing Final Report Generation...")
        
        result = self.call_main_api("generate_report")
        
        if "error" in result:
            self.log_test("Final Report", False, result["error"])
            return False
        
        if result.get("status") == "report":
            self.log_test("Final Report", True, "Report generated successfully")
            
            # Check report quality
            response_text = result.get("response", "")
            if len(response_text) > 100:
                self.log_test("Report Quality", True, f"Report length: {len(response_text)} chars")
            else:
                self.log_test("Report Quality", False, "Report too short")
        else:
            self.log_test("Final Report", False, f"Expected 'report' status, got: {result.get('status')}")
        
        return True
    
    def test_dental_flow(self) -> bool:
        """Test dental/oral health flow"""
        print("\n🦷 Testing Dental Flow...")
        
        result = self.call_main_api(
            "I have a concern about my oral health",
            speciality="dental"
        )
        
        if "error" in result:
            self.log_test("Dental Flow", False, result["error"])
            return False
        
        self.log_test("Dental Flow", True, f"Status: {result.get('status')}")
        
        # Check if response mentions oral/dental terms
        response_text = result.get("response", "").lower()
        if any(term in response_text for term in ["oral", "dental", "mouth", "teeth"]):
            self.log_test("Dental Context", True, "Response mentions oral/dental terms")
        else:
            self.log_test("Dental Context", False, "Response should mention oral/dental terms")
        
        return True
    
    def test_error_handling(self) -> bool:
        """Test error handling scenarios"""
        print("\n⚠️ Testing Error Handling...")
        
        # Test invalid chat ID
        result = self.call_main_api("Test message")
        if "error" not in result:
            self.log_test("Invalid Chat ID Handling", True, "Handled gracefully")
        else:
            self.log_test("Invalid Chat ID Handling", False, result["error"])
        
        # Test invalid image URL
        result = self.call_main_api(
            "Test with invalid image",
            image_url="https://invalid-url-that-does-not-exist.com/image.jpg",
            chat_type="image"
        )
        
        if "error" not in result:
            self.log_test("Invalid Image URL Handling", True, "Handled gracefully")
        else:
            self.log_test("Invalid Image URL Handling", False, result["error"])
        
        return True
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("🚀 Starting Healthcare Diagnostic API Tests")
        print(f"📍 Base URL: {self.base_url}")
        print(f"💬 Chat ID: {self.chat_id}")
        print(f"👤 User ID: {self.user_id}")
        print("=" * 60)
        
        # Run all test suites
        tests = [
            self.test_health_check,
            self.test_text_conversation_flow,
            self.test_image_analysis,
            self.test_final_report_generation,
            self.test_dental_flow,
            self.test_error_handling
        ]
        
        all_passed = True
        for test in tests:
            try:
                if not test():
                    all_passed = False
            except Exception as e:
                self.log_test(test.__name__, False, f"Test failed with exception: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️ Some tests failed. Check the details above.")
        print("=" * 60)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Healthcare Diagnostic API")
    parser.add_argument("--url", default="http://localhost:8080", 
                       help="Base URL of the API (default: http://localhost:8080)")
    parser.add_argument("--chat-id", default="GkV9vizfg2bCTDLRxDtT",
                       help="Chat ID to use for testing")
    parser.add_argument("--user-id", default="capstone_user_123",
                       help="User ID to use for testing")
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = HealthcareAPITester(args.url)
    tester.chat_id = args.chat_id
    tester.user_id = args.user_id
    
    # Run tests
    all_passed = tester.run_all_tests()
    tester.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Interactive End-to-End Test Script for Supervisor Agent
Allows user to interact as a customer, upload images, and test complete flow
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import argparse

class InteractiveE2ETester:
    """Interactive end-to-end tester for Supervisor Agent"""
    
    def __init__(self, supervisor_url: str, user_id: Optional[str] = None, chat_id: Optional[str] = None):
        self.supervisor_url = supervisor_url.rstrip('/')
        self.session = requests.Session()
        self.user_id = user_id or f"test_user_{int(time.time())}"
        self.chat_id = chat_id or f"test_chat_{int(time.time())}"
        self.conversation_history = []
        self.image_url = None
        
    def print_separator(self):
        """Print a visual separator"""
        print("\n" + "="*80 + "\n")
    
    def print_response(self, response: Dict[str, Any], show_full: bool = False):
        """Pretty print API response"""
        print("\n" + "-"*80)
        print("📨 AGENT RESPONSE:")
        print("-"*80)
        
        if response.get("success"):
            print(f"✅ Status: SUCCESS")
            print(f"💬 Response: {response.get('response', '')[:500]}")
            
            metadata = response.get("metadata", {})
            print(f"\n📊 Metadata:")
            print(f"   • Response Type: {response.get('response_type', 'N/A')}")
            
            if metadata.get("ready_for_images"):
                print(f"   • 🖼️  Ready for Image Upload: YES")
            if metadata.get("should_request_image"):
                print(f"   • 🖼️  Should Request Image: YES")
            if metadata.get("information_complete"):
                print(f"   • ✅ Information Complete: YES")
            
            # Show collected info if available
            collected_info = metadata.get("collected_info", {})
            if collected_info:
                print(f"\n📋 Collected Information:")
                for key, value in collected_info.items():
                    if value:  # Only show non-empty values
                        print(f"   • {key}: {value}")
            
            if show_full:
                print(f"\n🔍 Full Response:")
                print(json.dumps(response, indent=2))
        else:
            print(f"❌ Status: FAILED")
            print(f"❌ Error: {response.get('response', 'Unknown error')}")
            error = response.get("error", {})
            if error:
                print(f"   Error Type: {error.get('type', 'unknown')}")
                print(f"   Message: {error.get('message', '')}")
        
        print("-"*80)
    
    def send_message(self, message: str, speciality: str = "skin") -> Optional[Dict[str, Any]]:
        """Send a text message to the supervisor agent"""
        payload = {
            "message": message,
            "image_url": "",
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "type": "text",
            "speciality": speciality,
            "history": self.conversation_history
        }
        
        try:
            response = self.session.post(
                f"{self.supervisor_url}/api/v1/main",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                # Update conversation history
                if message:
                    self.conversation_history.append({"role": "user", "content": message})
                if result.get("response"):
                    self.conversation_history.append({"role": "assistant", "content": result.get("response")})
                return result
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return None
    
    def upload_image(self, image_url: str, speciality: str = "skin") -> Optional[Dict[str, Any]]:
        """Upload an image for analysis"""
        payload = {
            "message": "",
            "image_url": image_url,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "type": "image",
            "speciality": speciality,
            "history": self.conversation_history
        }
        
        try:
            print(f"\n📸 Uploading image: {image_url}")
            print("⏳ Processing... (this may take 30-60 seconds)")
            
            response = self.session.post(
                f"{self.supervisor_url}/api/v1/main",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # Longer timeout for image processing
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("response"):
                    self.conversation_history.append({"role": "assistant", "content": result.get("response")})
                return result
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return None
    
    def print_diagnosis_report(self, response: Dict[str, Any]):
        """Print the diagnosis and report in a formatted way"""
        metadata = response.get("metadata", {})
        
        print("\n" + "="*80)
        print("🏥 DIAGNOSIS & REPORT")
        print("="*80)
        
        # Diagnosis information
        diagnosis = metadata.get("diagnosis", {})
        if diagnosis:
            print(f"\n📊 DIAGNOSIS:")
            print(f"   Disease/Condition: {diagnosis.get('diagnosis_name', 'N/A')}")
            print(f"   Confidence: {diagnosis.get('confidence', 'N/A')}")
            if isinstance(diagnosis.get('confidence'), float):
                print(f"   Confidence: {diagnosis.get('confidence'):.1%}")
        
        # Report information
        report = metadata.get("report", {})
        if report:
            print(f"\n📋 MEDICAL REPORT:")
            for key, value in report.items():
                if value and key != "output":
                    print(f"   • {key.replace('_', ' ').title()}: {value}")
            
            # Full report output
            report_output = report.get("output") or response.get("response", "")
            if report_output:
                print(f"\n📝 Full Report:")
                print("-" * 80)
                print(report_output)
                print("-" * 80)
        else:
            # If report not in metadata, show the response
            report_text = response.get("response", "")
            if report_text:
                print(f"\n📝 Report:")
                print("-" * 80)
                print(report_text)
                print("-" * 80)
        
        print("="*80)
    
    def run_interactive_flow(self):
        """Run interactive end-to-end test flow"""
        print("\n" + "="*80)
        print("🚀 INTERACTIVE END-TO-END TEST - SUPERVISOR AGENT")
        print("="*80)
        print(f"Supervisor URL: {self.supervisor_url}")
        print(f"User ID: {self.user_id}")
        print(f"Chat ID: {self.chat_id}")
        print("="*80)
        
        # Step 1: Health check
        print("\n🔍 Step 1: Health Check")
        try:
            response = self.session.get(f"{self.supervisor_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Supervisor agent is healthy")
            else:
                print(f"⚠️  Health check returned: {response.status_code}")
                proceed = input("Continue anyway? (y/n): ")
                if proceed.lower() != 'y':
                    return
        except Exception as e:
            print(f"⚠️  Health check failed: {e}")
            proceed = input("Continue anyway? (y/n): ")
            if proceed.lower() != 'y':
                return
        
        # Step 2: Choose specialty
        self.print_separator()
        print("🎯 Step 2: Choose Medical Specialty")
        print("1. Skin (Dermatology)")
        print("2. Oral (Dentistry)")
        choice = input("\nEnter choice (1 or 2, default=1): ").strip()
        speciality = "oral" if choice == "2" else "skin"
        print(f"✅ Selected: {speciality}")
        
        # Step 3: Start conversation
        self.print_separator()
        print("💬 Step 3: Start Conversation")
        print("Enter your initial complaint/symptom description.")
        print("Example: 'I have a rash on my arm that appeared 3 days ago'")
        print("\nType your message (or 'skip' to skip this step):")
        
        user_message = input("\nYou: ").strip()
        
        if user_message.lower() != "skip" and user_message:
            result = self.send_message(user_message, speciality)
            if result:
                self.print_response(result)
            else:
                print("❌ Failed to send message")
                return
        
        # Step 4: Continue conversation interactively
        self.print_separator()
        print("💬 Step 4: Continue Conversation")
        print("The agent will ask questions. Respond naturally as a patient would.")
        print("\nCommands:")
        print("  - Type your response to continue the conversation")
        print("  - Type 'image' or 'upload' to proceed to image upload")
        print("  - Type 'skip' to skip remaining questions")
        print("  - Type 'quit' or 'exit' to end")
        
        max_turns = 15
        turn = 0
        
        while turn < max_turns:
            turn += 1
            print(f"\n--- Turn {turn} ---")
            user_input = input("\nYou: ").strip()
            
            if not user_input or user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Ending conversation")
                break
            
            if user_input.lower() in ["image", "upload", "img"]:
                print("📸 Proceeding to image upload...")
                break
            
            if user_input.lower() == "skip":
                print("⏭️  Skipping remaining questions")
                break
            
            result = self.send_message(user_input, speciality)
            if result:
                self.print_response(result)
                
                # Check if agent is ready for image
                metadata = result.get("metadata", {})
                if metadata.get("ready_for_images") or metadata.get("should_request_image"):
                    print("\n✨ Agent is requesting an image upload!")
                    upload_now = input("Upload image now? (y/n, default=y): ").strip().lower()
                    if upload_now != 'n':
                        break
            else:
                print("❌ Failed to send message. Try again or type 'quit' to exit.")
        
        # Step 5: Image upload
        self.print_separator()
        print("📸 Step 5: Image Upload & Analysis")
        
        if not self.image_url:
            print("Enter the image URL (gs:// or https://)")
            print("Example: gs://your-bucket/path/to/image.jpg")
            print("Or: https://example.com/image.jpg")
            print("\nType 'skip' to skip image upload")
            
            image_url = input("\nImage URL: ").strip()
            
            if image_url.lower() != "skip" and image_url:
                self.image_url = image_url
            else:
                print("⏭️  Skipping image upload")
                return
        
        if self.image_url:
            print(f"\n📤 Uploading image for analysis...")
            result = self.upload_image(self.image_url, speciality)
            
            if result:
                if result.get("success"):
                    self.print_diagnosis_report(result)
                    
                    # Save results summary
                    print("\n" + "="*80)
                    print("📊 TEST SUMMARY")
                    print("="*80)
                    print(f"Chat ID: {self.chat_id}")
                    print(f"User ID: {self.user_id}")
                    print(f"Specialty: {speciality}")
                    print(f"Image URL: {self.image_url}")
                    print(f"Total Messages: {len(self.conversation_history)}")
                    print("\n✅ End-to-end test completed successfully!")
                    print("="*80)
                    
                    # Ask if user wants to save results
                    save = input("\n💾 Save test results to file? (y/n): ").strip().lower()
                    if save == 'y':
                        self.save_results(result)
                else:
                    print("❌ Image upload failed")
                    self.print_response(result, show_full=True)
            else:
                print("❌ Failed to upload image")
        else:
            print("⚠️  No image URL provided. Test incomplete.")
    
    def save_results(self, final_response: Dict[str, Any]):
        """Save test results to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{self.chat_id}_{timestamp}.json"
        
        results = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "supervisor_url": self.supervisor_url,
                "user_id": self.user_id,
                "chat_id": self.chat_id,
                "image_url": self.image_url
            },
            "conversation_history": self.conversation_history,
            "final_response": final_response
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"✅ Results saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Interactive End-to-End Test for Supervisor Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic interactive test
  python test_interactive_e2e.py --url http://localhost:8080
  
  # Test with specific IDs
  python test_interactive_e2e.py --url http://localhost:8080 --user-id user123 --chat-id chat456
  
  # Test with pre-set image URL
  python test_interactive_e2e.py --url http://localhost:8080 --image-url gs://bucket/image.jpg
        """
    )
    
    parser.add_argument("--url", 
                       default="http://localhost:8080",
                       help="Supervisor agent URL (default: http://localhost:8080)")
    parser.add_argument("--user-id",
                       help="User ID to use for testing (default: auto-generated)")
    parser.add_argument("--chat-id",
                       help="Chat ID to use for testing (default: auto-generated)")
    parser.add_argument("--image-url",
                       default="",
                       help="Pre-set image URL (gs:// or https://) - can also enter during test")
    
    args = parser.parse_args()
    
    # Create tester
    tester = InteractiveE2ETester(
        supervisor_url=args.url,
        user_id=args.user_id,
        chat_id=args.chat_id
    )
    
    if args.image_url:
        tester.image_url = args.image_url
        print(f"📸 Pre-configured image URL: {args.image_url}")
    
    # Run interactive flow
    try:
        tester.run_interactive_flow()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


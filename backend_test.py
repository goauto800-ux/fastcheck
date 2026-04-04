#!/usr/bin/env python3
"""
FAST App Backend API Testing - Aggressive Auto-Threading Scaling
Tests all backend endpoints with focus on the new dynamic threading configuration
"""

import requests
import sys
import json
import io
from datetime import datetime
from typing import Dict, List, Any

class FASTAPITester:
    def __init__(self, base_url="https://verify-mail-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")

    def test_health_endpoint(self) -> bool:
        """Test /api/health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    # Check for required fields
                    required_fields = ["email_platforms", "phone_platforms", "total_platforms", "threading"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        total_platforms = data.get("total_platforms", 0)
                        threading_info = data.get("threading", {})
                        self.log_test("Health Check", True, f"Status: healthy, Total platforms: {total_platforms}, Threading: {threading_info}")
                        return True
                    else:
                        self.log_test("Health Check", False, f"Missing fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Health Check", False, f"Invalid response format: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Request failed: {str(e)}")
            return False

    def test_platforms_endpoint(self) -> bool:
        """Test /api/platforms endpoint"""
        try:
            response = requests.get(f"{self.api_url}/platforms", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "platforms" in data and "email_total" in data and "phone_total" in data:
                    email_count = data.get("email_total", 0)
                    phone_count = data.get("phone_total", 0)
                    self.log_test("Platforms Endpoint", True, f"Email platforms: {email_count}, Phone platforms: {phone_count}")
                    return True
                else:
                    self.log_test("Platforms Endpoint", False, f"Missing required fields: {data}")
                    return False
            else:
                self.log_test("Platforms Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Platforms Endpoint", False, f"Request failed: {str(e)}")
            return False

    def test_thread_config_no_params(self) -> bool:
        """Test GET /api/config/threads (no total param) - should work with defaults"""
        try:
            response = requests.get(f"{self.api_url}/config/threads", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["max_concurrent_identifiers", "max_concurrent_platforms", "recommended_batch_size", "mode"]
                
                missing_fields = [field for field in required_fields if field not in data]
                if not missing_fields:
                    identifiers = data.get("max_concurrent_identifiers", 0)
                    batch_size = data.get("recommended_batch_size", 0)
                    mode = data.get("mode", "unknown")
                    self.log_test("Thread Config (no params)", True, 
                                f"Identifiers: {identifiers}, Batch: {batch_size}, Mode: {mode}")
                    return True
                else:
                    self.log_test("Thread Config (no params)", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Thread Config (no params)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Thread Config (no params)", False, f"Request failed: {str(e)}")
            return False

    def test_aggressive_thread_scaling(self) -> bool:
        """Test aggressive auto-threading scaling with different total values"""
        # First check if we have active proxies to determine expected values
        try:
            health_response = requests.get(f"{self.api_url}/health", timeout=10)
            has_proxies = False
            if health_response.status_code == 200:
                health_data = health_response.json()
                proxies_active = health_data.get("proxies_active", 0)
                has_proxies = proxies_active > 0
                print(f"    Active proxies detected: {proxies_active}")
        except:
            has_proxies = False
        
        # Test cases based on actual implementation logic
        # Values depend on whether proxies are active
        if has_proxies:
            test_cases = [
                {"total": 10, "expected_identifiers": 10, "expected_batch": 10, "tolerance": 2},
                {"total": 50, "expected_identifiers": 25, "expected_batch": 30, "tolerance": 5},
                {"total": 100, "expected_identifiers": 50, "expected_batch": 30, "tolerance": 5},
                {"total": 500, "expected_identifiers": 80, "expected_batch": 80, "tolerance": 10},
                {"total": 1000, "expected_identifiers": 100, "expected_batch": 80, "tolerance": 10},
                {"total": 5000, "expected_identifiers": 100, "expected_batch": 100, "tolerance": 10},
            ]
        else:
            test_cases = [
                {"total": 10, "expected_identifiers": 10, "expected_batch": 10, "tolerance": 2},
                {"total": 50, "expected_identifiers": 20, "expected_batch": 15, "tolerance": 5},
                {"total": 100, "expected_identifiers": 30, "expected_batch": 25, "tolerance": 5},
                {"total": 500, "expected_identifiers": 50, "expected_batch": 60, "tolerance": 10},
                {"total": 1000, "expected_identifiers": 60, "expected_batch": 60, "tolerance": 10},
                {"total": 5000, "expected_identifiers": 60, "expected_batch": 80, "tolerance": 10},
            ]
        
        all_passed = True
        
        for case in test_cases:
            try:
                response = requests.get(f"{self.api_url}/config/threads?total={case['total']}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    identifiers = data.get("max_concurrent_identifiers", 0)
                    batch_size = data.get("recommended_batch_size", 0)
                    
                    # Check if values are within expected range
                    identifiers_ok = abs(identifiers - case["expected_identifiers"]) <= case["tolerance"]
                    batch_ok = abs(batch_size - case["expected_batch"]) <= case["tolerance"]
                    
                    if identifiers_ok and batch_ok:
                        self.log_test(f"Thread Scaling (total={case['total']})", True,
                                    f"Identifiers: {identifiers} (expected ~{case['expected_identifiers']}), Batch: {batch_size} (expected ~{case['expected_batch']})")
                    else:
                        self.log_test(f"Thread Scaling (total={case['total']})", False,
                                    f"Scaling mismatch - Identifiers: {identifiers} (expected ~{case['expected_identifiers']}), Batch: {batch_size} (expected ~{case['expected_batch']})")
                        all_passed = False
                else:
                    self.log_test(f"Thread Scaling (total={case['total']})", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Thread Scaling (total={case['total']})", False, f"Request failed: {str(e)}")
                all_passed = False
        
        return all_passed
    def test_verify_endpoint(self) -> bool:
        """Test POST /api/verify endpoint with small batch to verify dynamic threading works"""
        test_identifiers = ["test@example.com"]
        
        try:
            payload = {"identifiers": test_identifiers}
            response = requests.post(
                f"{self.api_url}/verify", 
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if "total" in data and "results" in data:
                    results = data["results"]
                    
                    if len(results) == len(test_identifiers):
                        # Check each result structure
                        all_valid = True
                        for result in results:
                            required_fields = ["id", "identifier", "identifier_type", "platforms", "timestamp"]
                            if not all(field in result for field in required_fields):
                                all_valid = False
                                break
                            
                            # Check platforms
                            platforms = result["platforms"]
                            if len(platforms) == 0:  # Should have some platforms
                                all_valid = False
                                break
                            
                            for platform in platforms:
                                if not all(field in platform for field in ["platform", "status"]):
                                    all_valid = False
                                    break
                                # Allow more status types including unverifiable
                                if platform["status"] not in ["found", "not_found", "unverifiable", "rate_limited", "error"]:
                                    all_valid = False
                                    break
                        
                        if all_valid:
                            platforms_count = len(results[0]["platforms"]) if results else 0
                            self.log_test("Verify Endpoint", True, f"Verified {len(results)} identifier(s), {platforms_count} platforms checked")
                            return True
                        else:
                            self.log_test("Verify Endpoint", False, "Invalid result structure")
                            return False
                    else:
                        self.log_test("Verify Endpoint", False, f"Expected {len(test_identifiers)} results, got {len(results)}")
                        return False
                else:
                    self.log_test("Verify Endpoint", False, f"Invalid response format: {data}")
                    return False
            else:
                self.log_test("Verify Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Verify Endpoint", False, f"Request failed: {str(e)}")
            return False

    def test_verify_file_endpoint(self) -> bool:
        """Test /api/verify/file endpoint with CSV upload"""
        # Create test CSV content
        csv_content = """email,phone
test1@example.com,+33612345678
user@domain.fr,+33687654321
admin@test.com,+33698765432"""
        
        try:
            # Create file-like object
            files = {
                'file': ('test_data.csv', io.StringIO(csv_content), 'text/csv')
            }
            
            response = requests.post(
                f"{self.api_url}/verify/file",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "total" in data and "results" in data:
                    results = data["results"]
                    
                    # Should extract at least the emails and phones from CSV
                    if len(results) >= 4:  # At least 4 identifiers (3 emails + 3 phones)
                        self.log_test("File Upload Endpoint", True, f"Processed file with {len(results)} identifiers")
                        return True
                    else:
                        self.log_test("File Upload Endpoint", False, f"Expected at least 4 identifiers, got {len(results)}")
                        return False
                else:
                    self.log_test("File Upload Endpoint", False, f"Invalid response format: {data}")
                    return False
            else:
                self.log_test("File Upload Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("File Upload Endpoint", False, f"Request failed: {str(e)}")
            return False

    def test_verify_single_endpoint(self) -> bool:
        """Test /api/verify/single endpoint"""
        test_email = "single@test.com"
        
        try:
            response = requests.post(
                f"{self.api_url}/verify/single",
                params={"identifier": test_email},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate single result structure
                required_fields = ["id", "identifier", "identifier_type", "platforms", "timestamp"]
                if all(field in data for field in required_fields):
                    if data["identifier"] == test_email and len(data["platforms"]) == 5:
                        self.log_test("Single Verify Endpoint", True, f"Verified single identifier: {test_email}")
                        return True
                    else:
                        self.log_test("Single Verify Endpoint", False, "Invalid result data")
                        return False
                else:
                    self.log_test("Single Verify Endpoint", False, f"Missing required fields: {data}")
                    return False
            else:
                self.log_test("Single Verify Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Single Verify Endpoint", False, f"Request failed: {str(e)}")
            return False

    def test_error_handling(self) -> bool:
        """Test error handling for invalid requests"""
        tests_passed = 0
        total_tests = 2
        
        # Test 1: Empty identifiers list
        try:
            response = requests.post(
                f"{self.api_url}/verify",
                json={"identifiers": []},
                timeout=10
            )
            if response.status_code == 400:
                tests_passed += 1
                print("    ✅ Empty identifiers handled correctly")
            else:
                print(f"    ❌ Empty identifiers: Expected 400, got {response.status_code}")
        except Exception as e:
            print(f"    ❌ Empty identifiers test failed: {e}")

        # Test 2: Invalid file type for parse-file
        try:
            files = {'file': ('test.exe', b'invalid content', 'application/octet-stream')}
            response = requests.post(f"{self.api_url}/parse-file", files=files, timeout=10)
            if response.status_code == 400:
                tests_passed += 1
                print("    ✅ Invalid file type handled correctly")
            else:
                print(f"    ❌ Invalid file type: Expected 400, got {response.status_code}")
        except Exception as e:
            print(f"    ❌ Invalid file type test failed: {e}")

        success = tests_passed == total_tests
        self.log_test("Error Handling", success, f"Passed {tests_passed}/{total_tests} error handling tests")
        return success

    def test_parse_file_endpoint(self) -> bool:
        """Test /api/parse-file endpoint with various file types and content"""
        all_tests_passed = True
        
        # Test 1: Mixed emails and phone numbers
        mixed_content = """test@example.com
user@gmail.com
+33612345678
0612345679
another@test.fr
+44771234567"""
        
        try:
            files = {'file': ('mixed_data.txt', mixed_content, 'text/plain')}
            response = requests.post(f"{self.api_url}/parse-file", files=files, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["filename", "total", "emails", "phones", "email_count", "phone_count", "preview"]
                
                if all(field in data for field in required_fields):
                    if data["email_count"] > 0 and data["phone_count"] > 0:
                        self.log_test("Parse File - Mixed Content", True, 
                                    f"Found {data['email_count']} emails, {data['phone_count']} phones")
                    else:
                        self.log_test("Parse File - Mixed Content", False, 
                                    f"Expected both emails and phones, got emails: {data['email_count']}, phones: {data['phone_count']}")
                        all_tests_passed = False
                else:
                    self.log_test("Parse File - Mixed Content", False, f"Missing required fields: {data}")
                    all_tests_passed = False
            else:
                self.log_test("Parse File - Mixed Content", False, f"HTTP {response.status_code}: {response.text}")
                all_tests_passed = False
        except Exception as e:
            self.log_test("Parse File - Mixed Content", False, f"Request failed: {str(e)}")
            all_tests_passed = False
        
        # Test 2: CSV with only emails
        csv_emails_only = """email,name
user1@example.com,John
user2@gmail.com,Jane
admin@company.fr,Admin"""
        
        try:
            files = {'file': ('emails_only.csv', csv_emails_only, 'text/csv')}
            response = requests.post(f"{self.api_url}/parse-file", files=files, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data["email_count"] > 0 and data["phone_count"] == 0:
                    self.log_test("Parse File - Emails Only", True, 
                                f"Found {data['email_count']} emails, {data['phone_count']} phones")
                else:
                    self.log_test("Parse File - Emails Only", False, 
                                f"Expected only emails, got emails: {data['email_count']}, phones: {data['phone_count']}")
                    all_tests_passed = False
            else:
                self.log_test("Parse File - Emails Only", False, f"HTTP {response.status_code}: {response.text}")
                all_tests_passed = False
        except Exception as e:
            self.log_test("Parse File - Emails Only", False, f"Request failed: {str(e)}")
            all_tests_passed = False
        
        # Test 3: Text file with only phone numbers
        phones_only = """+33612345678
+44771234567
0687654321
+1234567890"""
        
        try:
            files = {'file': ('phones_only.txt', phones_only, 'text/plain')}
            response = requests.post(f"{self.api_url}/parse-file", files=files, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data["phone_count"] > 0 and data["email_count"] == 0:
                    self.log_test("Parse File - Phones Only", True, 
                                f"Found {data['email_count']} emails, {data['phone_count']} phones")
                else:
                    self.log_test("Parse File - Phones Only", False, 
                                f"Expected only phones, got emails: {data['email_count']}, phones: {data['phone_count']}")
                    all_tests_passed = False
            else:
                self.log_test("Parse File - Phones Only", False, f"HTTP {response.status_code}: {response.text}")
                all_tests_passed = False
        except Exception as e:
            self.log_test("Parse File - Phones Only", False, f"Request failed: {str(e)}")
            all_tests_passed = False
        
        # Test 4: Empty file
        try:
            files = {'file': ('empty.txt', '', 'text/plain')}
            response = requests.post(f"{self.api_url}/parse-file", files=files, timeout=15)
            
            if response.status_code == 400:
                self.log_test("Parse File - Empty File", True, "Empty file correctly rejected with 400")
            else:
                self.log_test("Parse File - Empty File", False, f"Expected 400 for empty file, got {response.status_code}")
                all_tests_passed = False
        except Exception as e:
            self.log_test("Parse File - Empty File", False, f"Request failed: {str(e)}")
            all_tests_passed = False
        
        # Test 5: File with invalid content (no emails/phones)
        invalid_content = """This is just some random text
with no emails or phone numbers
just words and sentences
nothing useful for parsing"""
        
        try:
            files = {'file': ('invalid.txt', invalid_content, 'text/plain')}
            response = requests.post(f"{self.api_url}/parse-file", files=files, timeout=15)
            
            if response.status_code == 400:
                self.log_test("Parse File - Invalid Content", True, "Invalid content correctly rejected with 400")
            else:
                self.log_test("Parse File - Invalid Content", False, f"Expected 400 for invalid content, got {response.status_code}")
                all_tests_passed = False
        except Exception as e:
            self.log_test("Parse File - Invalid Content", False, f"Request failed: {str(e)}")
            all_tests_passed = False
        
        return all_tests_passed

    def test_cors_headers(self) -> bool:
        """Test CORS headers are present"""
        try:
            response = requests.options(f"{self.api_url}/health", timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            present_headers = [header for header in cors_headers if header in response.headers]
            
            if len(present_headers) >= 1:  # At least one CORS header should be present
                self.log_test("CORS Headers", True, f"CORS headers present: {present_headers}")
                return True
            else:
                self.log_test("CORS Headers", False, "No CORS headers found")
                return False
                
        except Exception as e:
            self.log_test("CORS Headers", False, f"Request failed: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend tests with focus on aggressive auto-threading scaling"""
        print("🚀 Starting FAST Backend API Tests - Aggressive Auto-Threading Scaling")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Test basic endpoints first
        self.test_health_endpoint()
        self.test_platforms_endpoint()
        
        # Test aggressive auto-threading scaling (main focus)
        print("\n🎯 AGGRESSIVE AUTO-THREADING SCALING TESTS")
        print("-" * 50)
        self.test_thread_config_no_params()
        self.test_aggressive_thread_scaling()
        
        # Test verification with new dynamic threading
        print("\n🔍 VERIFICATION WITH DYNAMIC THREADING")
        print("-" * 50)
        self.test_verify_endpoint()
        
        # Test other endpoints
        print("\n📁 FILE PROCESSING TESTS")
        print("-" * 50)
        self.test_parse_file_endpoint()
        
        print("\n⚠️  ERROR HANDLING TESTS")
        print("-" * 50)
        self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Aggressive auto-threading scaling is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result["success"]]
            if failed_tests:
                print("\n❌ FAILED TESTS:")
                for test in failed_tests:
                    print(f"  - {test['test']}: {test['details']}")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": success_rate,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = FASTAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["passed_tests"] == results["total_tests"] else 1

if __name__ == "__main__":
    sys.exit(main())
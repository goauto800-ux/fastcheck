#!/usr/bin/env python3
"""
FAST App Backend API Testing
Tests all backend endpoints for the identity verification tool
"""

import requests
import sys
import json
import io
from datetime import datetime
from typing import Dict, List, Any

class FASTAPITester:
    def __init__(self, base_url="https://order-checker-2.preview.emergentagent.com"):
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
                if data.get("status") == "healthy" and "platforms" in data:
                    platforms = data.get("platforms", [])
                    expected_platforms = ["uber_eats", "amazon", "netflix", "binance", "coinbase"]
                    
                    if set(platforms) == set(expected_platforms):
                        self.log_test("Health Check", True, f"Status: healthy, Platforms: {platforms}")
                        return True
                    else:
                        self.log_test("Health Check", False, f"Missing platforms. Got: {platforms}")
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

    def test_verify_endpoint(self) -> bool:
        """Test /api/verify endpoint with text input"""
        test_identifiers = [
            "test@example.com",
            "+33612345678",
            "user@domain.fr"
        ]
        
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
                            if len(platforms) != 5:  # Should have 5 platforms
                                all_valid = False
                                break
                            
                            for platform in platforms:
                                if not all(field in platform for field in ["platform", "status"]):
                                    all_valid = False
                                    break
                                if platform["status"] not in ["found", "not_found"]:
                                    all_valid = False
                                    break
                        
                        if all_valid:
                            self.log_test("Verify Endpoint", True, f"Verified {len(results)} identifiers successfully")
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
        total_tests = 3
        
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

        # Test 2: Invalid file type
        try:
            files = {'file': ('test.exe', b'invalid content', 'application/octet-stream')}
            response = requests.post(f"{self.api_url}/verify/file", files=files, timeout=10)
            if response.status_code == 400:
                tests_passed += 1
                print("    ✅ Invalid file type handled correctly")
            else:
                print(f"    ❌ Invalid file type: Expected 400, got {response.status_code}")
        except Exception as e:
            print(f"    ❌ Invalid file type test failed: {e}")

        # Test 3: Empty single identifier
        try:
            response = requests.post(f"{self.api_url}/verify/single", params={"identifier": ""}, timeout=10)
            if response.status_code == 400:
                tests_passed += 1
                print("    ✅ Empty single identifier handled correctly")
            else:
                print(f"    ❌ Empty single identifier: Expected 400, got {response.status_code}")
        except Exception as e:
            print(f"    ❌ Empty single identifier test failed: {e}")

        success = tests_passed == total_tests
        self.log_test("Error Handling", success, f"Passed {tests_passed}/{total_tests} error handling tests")
        return success

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
        """Run all backend tests"""
        print("🚀 Starting FAST Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run all tests
        self.test_health_endpoint()
        self.test_verify_endpoint()
        self.test_verify_file_endpoint()
        self.test_verify_single_endpoint()
        self.test_error_handling()
        self.test_cors_headers()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Backend is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
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
#!/usr/bin/env python3
"""
Background Job System Testing for Massive File Processing
Tests the new job system endpoints for handling millions of emails
"""

import requests
import sys
import json
import io
import time
from datetime import datetime
from typing import Dict, List, Any

class JobSystemTester:
    def __init__(self, base_url="https://app-kickoff-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_jobs = []  # Track jobs for cleanup

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

    def create_test_file_content(self, num_emails: int = 15) -> str:
        """Create test file content with realistic emails"""
        emails = []
        domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "protonmail.com", 
                  "icloud.com", "aol.com", "live.com", "mail.com", "zoho.com"]
        
        for i in range(num_emails):
            domain = domains[i % len(domains)]
            email = f"testuser{i+1}@{domain}"
            emails.append(email)
        
        return "\n".join(emails)

    def test_job_creation(self) -> bool:
        """Test POST /api/jobs/create endpoint"""
        try:
            # Create test file with 15 emails
            test_content = self.create_test_file_content(15)
            
            files = {
                'file': ('test_emails.txt', test_content, 'text/plain')
            }
            
            response = requests.post(
                f"{self.api_url}/jobs/create",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["job_id", "total", "status", "message"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    job_id = data["job_id"]
                    total = data["total"]
                    status = data["status"]
                    
                    # Validate values
                    if status == "pending" and total == 15 and job_id:
                        self.created_jobs.append(job_id)
                        self.log_test("Job Creation", True, 
                                    f"Job {job_id[:8]}... created with {total} identifiers, status: {status}")
                        return True
                    else:
                        self.log_test("Job Creation", False, 
                                    f"Invalid values - status: {status}, total: {total}, job_id: {bool(job_id)}")
                        return False
                else:
                    self.log_test("Job Creation", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Job Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Job Creation", False, f"Request failed: {str(e)}")
            return False

    def test_job_status_tracking(self) -> tuple[bool, str]:
        """Test GET /api/jobs/{job_id} endpoint and wait for completion"""
        if not self.created_jobs:
            self.log_test("Job Status Tracking", False, "No jobs created to track")
            return False, ""
        
        job_id = self.created_jobs[-1]  # Use the most recent job
        
        try:
            # Poll job status until completion or timeout
            max_wait_time = 120  # 2 minutes max
            start_time = time.time()
            last_status = "unknown"
            
            while time.time() - start_time < max_wait_time:
                response = requests.get(f"{self.api_url}/jobs/{job_id}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check required fields
                    required_fields = ["id", "status", "total", "processed", "progress", 
                                     "found", "not_found", "unverifiable", "errors", 
                                     "filename", "created_at", "started_at", "completed_at"]
                    
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        self.log_test("Job Status Tracking", False, f"Missing fields: {missing_fields}")
                        return False, job_id
                    
                    status = data["status"]
                    processed = data["processed"]
                    total = data["total"]
                    progress = data["progress"]
                    
                    # Log progress if status changed
                    if status != last_status:
                        print(f"    Job {job_id[:8]}... status: {status}, progress: {progress}%, processed: {processed}/{total}")
                        last_status = status
                    
                    if status == "completed":
                        # Validate completion data
                        if processed == total and progress == 100.0:
                            found = data["found"]
                            not_found = data["not_found"]
                            unverifiable = data["unverifiable"]
                            errors = data["errors"]
                            
                            self.log_test("Job Status Tracking", True, 
                                        f"Job completed - Found: {found}, Not found: {not_found}, Unverifiable: {unverifiable}, Errors: {errors}")
                            return True, job_id
                        else:
                            self.log_test("Job Status Tracking", False, 
                                        f"Job marked complete but data inconsistent - processed: {processed}/{total}, progress: {progress}%")
                            return False, job_id
                    
                    elif status == "failed":
                        error = data.get("error", "Unknown error")
                        self.log_test("Job Status Tracking", False, f"Job failed: {error}")
                        return False, job_id
                    
                    elif status in ["pending", "running"]:
                        # Continue polling
                        time.sleep(2)
                        continue
                    
                    else:
                        self.log_test("Job Status Tracking", False, f"Unknown job status: {status}")
                        return False, job_id
                
                else:
                    self.log_test("Job Status Tracking", False, f"HTTP {response.status_code}: {response.text}")
                    return False, job_id
            
            # Timeout reached
            self.log_test("Job Status Tracking", False, f"Job did not complete within {max_wait_time} seconds")
            return False, job_id
            
        except Exception as e:
            self.log_test("Job Status Tracking", False, f"Request failed: {str(e)}")
            return False, job_id

    def test_job_list(self) -> bool:
        """Test GET /api/jobs endpoint"""
        try:
            response = requests.get(f"{self.api_url}/jobs", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "jobs" in data:
                    jobs = data["jobs"]
                    
                    if len(jobs) > 0:
                        # Check structure of first job
                        job = jobs[0]
                        required_fields = ["id", "status", "total", "processed", "progress", "filename", "created_at"]
                        missing_fields = [field for field in required_fields if field not in job]
                        
                        if not missing_fields:
                            self.log_test("Job List", True, f"Found {len(jobs)} jobs in list")
                            return True
                        else:
                            self.log_test("Job List", False, f"Job missing fields: {missing_fields}")
                            return False
                    else:
                        self.log_test("Job List", True, "Job list is empty (no jobs created yet)")
                        return True
                else:
                    self.log_test("Job List", False, f"Missing 'jobs' field in response: {data}")
                    return False
            else:
                self.log_test("Job List", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Job List", False, f"Request failed: {str(e)}")
            return False

    def test_csv_download(self, job_id: str) -> bool:
        """Test GET /api/jobs/{job_id}/results/csv endpoint"""
        if not job_id:
            self.log_test("CSV Download", False, "No job ID provided")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/jobs/{job_id}/results/csv", timeout=30)
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get('content-type', '')
                if 'csv' in content_type.lower() or 'text' in content_type.lower():
                    
                    # Check content disposition header
                    content_disposition = response.headers.get('content-disposition', '')
                    if 'attachment' in content_disposition and 'filename' in content_disposition:
                        
                        # Check content
                        content = response.text
                        lines = content.strip().split('\n')
                        
                        if len(lines) > 0:
                            # Should have header line
                            header = lines[0]
                            if 'Identifiant' in header or 'identifier' in header.lower():
                                self.log_test("CSV Download", True, 
                                            f"CSV downloaded successfully, {len(lines)} lines (including header)")
                                return True
                            else:
                                self.log_test("CSV Download", False, f"Invalid CSV header: {header}")
                                return False
                        else:
                            self.log_test("CSV Download", True, "CSV downloaded but empty (no valid identifiers found)")
                            return True
                    else:
                        self.log_test("CSV Download", False, f"Missing attachment headers: {content_disposition}")
                        return False
                else:
                    self.log_test("CSV Download", False, f"Invalid content type: {content_type}")
                    return False
            else:
                self.log_test("CSV Download", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("CSV Download", False, f"Request failed: {str(e)}")
            return False

    def test_txt_download(self, job_id: str) -> bool:
        """Test GET /api/jobs/{job_id}/results/txt endpoint"""
        if not job_id:
            self.log_test("TXT Download", False, "No job ID provided")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/jobs/{job_id}/results/txt", timeout=30)
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get('content-type', '')
                if 'text' in content_type.lower() or 'plain' in content_type.lower():
                    
                    # Check content disposition header
                    content_disposition = response.headers.get('content-disposition', '')
                    if 'attachment' in content_disposition and 'filename' in content_disposition:
                        
                        # Check content format (should be one identifier per line)
                        content = response.text.strip()
                        if content:
                            lines = content.split('\n')
                            # Each line should be a valid identifier
                            valid_lines = [line.strip() for line in lines if line.strip()]
                            self.log_test("TXT Download", True, 
                                        f"TXT downloaded successfully, {len(valid_lines)} valid identifiers")
                            return True
                        else:
                            self.log_test("TXT Download", True, "TXT downloaded but empty (no valid identifiers found)")
                            return True
                    else:
                        self.log_test("TXT Download", False, f"Missing attachment headers: {content_disposition}")
                        return False
                else:
                    self.log_test("TXT Download", False, f"Invalid content type: {content_type}")
                    return False
            else:
                self.log_test("TXT Download", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("TXT Download", False, f"Request failed: {str(e)}")
            return False

    def test_jsonl_download(self, job_id: str) -> bool:
        """Test GET /api/jobs/{job_id}/results/jsonl endpoint"""
        if not job_id:
            self.log_test("JSONL Download", False, "No job ID provided")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/jobs/{job_id}/results/jsonl", timeout=30)
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get('content-type', '')
                if 'jsonl' in content_type.lower() or 'json' in content_type.lower():
                    
                    # Check content disposition header
                    content_disposition = response.headers.get('content-disposition', '')
                    if 'attachment' in content_disposition and 'filename' in content_disposition:
                        
                        # Check JSONL format
                        content = response.text.strip()
                        if content:
                            lines = content.split('\n')
                            valid_json_lines = 0
                            
                            for line in lines:
                                if line.strip():
                                    try:
                                        json.loads(line)
                                        valid_json_lines += 1
                                    except json.JSONDecodeError:
                                        pass
                            
                            if valid_json_lines > 0:
                                self.log_test("JSONL Download", True, 
                                            f"JSONL downloaded successfully, {valid_json_lines} valid JSON lines")
                                return True
                            else:
                                self.log_test("JSONL Download", False, "JSONL contains no valid JSON lines")
                                return False
                        else:
                            self.log_test("JSONL Download", True, "JSONL downloaded but empty (no results)")
                            return True
                    else:
                        self.log_test("JSONL Download", False, f"Missing attachment headers: {content_disposition}")
                        return False
                else:
                    self.log_test("JSONL Download", False, f"Invalid content type: {content_type}")
                    return False
            else:
                self.log_test("JSONL Download", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("JSONL Download", False, f"Request failed: {str(e)}")
            return False

    def test_verify_endpoint_still_works(self) -> bool:
        """Test that the existing /api/verify endpoint still works for small batches"""
        try:
            test_identifiers = ["testuser@gmail.com", "sample@yahoo.com"]
            
            payload = {"identifiers": test_identifiers}
            response = requests.post(
                f"{self.api_url}/verify", 
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "total" in data and "results" in data:
                    results = data["results"]
                    
                    if len(results) == len(test_identifiers):
                        # Check basic structure
                        for result in results:
                            if not all(field in result for field in ["id", "identifier", "platforms"]):
                                self.log_test("Verify Endpoint Compatibility", False, "Invalid result structure")
                                return False
                        
                        self.log_test("Verify Endpoint Compatibility", True, 
                                    f"Verified {len(results)} identifiers using existing endpoint")
                        return True
                    else:
                        self.log_test("Verify Endpoint Compatibility", False, 
                                    f"Expected {len(test_identifiers)} results, got {len(results)}")
                        return False
                else:
                    self.log_test("Verify Endpoint Compatibility", False, f"Invalid response format: {data}")
                    return False
            else:
                self.log_test("Verify Endpoint Compatibility", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Verify Endpoint Compatibility", False, f"Request failed: {str(e)}")
            return False

    def test_invalid_job_requests(self) -> bool:
        """Test error handling for invalid job requests"""
        tests_passed = 0
        total_tests = 3
        
        # Test 1: Invalid file type
        try:
            files = {'file': ('test.exe', b'invalid content', 'application/octet-stream')}
            response = requests.post(f"{self.api_url}/jobs/create", files=files, timeout=10)
            if response.status_code == 400:
                tests_passed += 1
                print("    ✅ Invalid file type rejected correctly")
            else:
                print(f"    ❌ Invalid file type: Expected 400, got {response.status_code}")
        except Exception as e:
            print(f"    ❌ Invalid file type test failed: {e}")

        # Test 2: Empty file
        try:
            files = {'file': ('empty.txt', '', 'text/plain')}
            response = requests.post(f"{self.api_url}/jobs/create", files=files, timeout=10)
            if response.status_code == 400:
                tests_passed += 1
                print("    ✅ Empty file rejected correctly")
            else:
                print(f"    ❌ Empty file: Expected 400, got {response.status_code}")
        except Exception as e:
            print(f"    ❌ Empty file test failed: {e}")

        # Test 3: Non-existent job ID
        try:
            fake_job_id = "00000000-0000-0000-0000-000000000000"
            response = requests.get(f"{self.api_url}/jobs/{fake_job_id}", timeout=10)
            if response.status_code == 404:
                tests_passed += 1
                print("    ✅ Non-existent job ID handled correctly")
            else:
                print(f"    ❌ Non-existent job ID: Expected 404, got {response.status_code}")
        except Exception as e:
            print(f"    ❌ Non-existent job ID test failed: {e}")

        success = tests_passed == total_tests
        self.log_test("Invalid Job Requests", success, f"Passed {tests_passed}/{total_tests} error handling tests")
        return success

    def run_full_job_system_test(self) -> Dict[str, Any]:
        """Run complete job system test flow"""
        print("🚀 Starting Background Job System Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Test 1: Job creation
        print("\n📝 JOB CREATION TEST")
        print("-" * 50)
        job_created = self.test_job_creation()
        
        # Test 2: Job status tracking (wait for completion)
        print("\n⏱️  JOB STATUS TRACKING TEST")
        print("-" * 50)
        job_completed, completed_job_id = self.test_job_status_tracking()
        
        # Test 3: Job list
        print("\n📋 JOB LIST TEST")
        print("-" * 50)
        self.test_job_list()
        
        # Test 4-6: Download endpoints (only if job completed)
        if job_completed and completed_job_id:
            print("\n📥 DOWNLOAD ENDPOINTS TESTS")
            print("-" * 50)
            self.test_csv_download(completed_job_id)
            self.test_txt_download(completed_job_id)
            self.test_jsonl_download(completed_job_id)
        else:
            print("\n⚠️  Skipping download tests - no completed job available")
        
        # Test 7: Verify existing endpoint still works
        print("\n🔄 COMPATIBILITY TEST")
        print("-" * 50)
        self.test_verify_endpoint_still_works()
        
        # Test 8: Error handling
        print("\n⚠️  ERROR HANDLING TESTS")
        print("-" * 50)
        self.test_invalid_job_requests()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All job system tests passed! Background processing is working correctly.")
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
            "test_results": self.test_results,
            "created_jobs": self.created_jobs
        }

def main():
    """Main test execution"""
    tester = JobSystemTester()
    results = tester.run_full_job_system_test()
    
    # Return appropriate exit code
    return 0 if results["passed_tests"] == results["total_tests"] else 1

if __name__ == "__main__":
    sys.exit(main())
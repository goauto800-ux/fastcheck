#!/usr/bin/env python3
"""
Uber Eats Checker Backend API Test Suite
Tests all API endpoints for the Uber Eats email checker service.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://test-runner-60.preview.emergentagent.com/api"

class UberEatsAPITester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=120)  # 2 minutes timeout
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
    
    async def test_health_endpoint(self):
        """Test GET /api/health"""
        try:
            async with self.session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check required fields
                    if data.get("status") == "healthy" and "browser_ready" in data:
                        browser_ready = data.get("browser_ready")
                        self.log_test(
                            "Health Check", 
                            True, 
                            f"Status: {data.get('status')}, Browser Ready: {browser_ready}",
                            data
                        )
                        return True
                    else:
                        self.log_test(
                            "Health Check", 
                            False, 
                            "Missing required fields or incorrect status",
                            data
                        )
                        return False
                else:
                    self.log_test(
                        "Health Check", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False
    
    async def test_root_endpoint(self):
        """Test GET /api/"""
        try:
            async with self.session.get(f"{BACKEND_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for service info
                    if "service" in data and "version" in data:
                        self.log_test(
                            "Root Endpoint", 
                            True, 
                            f"Service: {data.get('service')}, Version: {data.get('version')}",
                            data
                        )
                        return True
                    else:
                        self.log_test(
                            "Root Endpoint", 
                            False, 
                            "Missing service info fields",
                            data
                        )
                        return False
                else:
                    self.log_test(
                        "Root Endpoint", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_proxy_add(self):
        """Test POST /api/proxies/add"""
        try:
            payload = {
                "proxies": ["http://123.45.67.89:8080"],
                "proxy_type": "auto"
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/proxies/add",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check response structure
                    if "success" in data and "added" in data:
                        self.log_test(
                            "Add Proxy", 
                            True, 
                            f"Added: {data.get('added')}, Success: {data.get('success')}",
                            data
                        )
                        return True
                    else:
                        self.log_test(
                            "Add Proxy", 
                            False, 
                            "Missing required response fields",
                            data
                        )
                        return False
                else:
                    self.log_test(
                        "Add Proxy", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Add Proxy", False, f"Exception: {str(e)}")
            return False
    
    async def test_proxy_list(self):
        """Test GET /api/proxies"""
        try:
            async with self.session.get(f"{BACKEND_URL}/proxies") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check response structure
                    if "proxies" in data and "total" in data and "active" in data:
                        self.log_test(
                            "List Proxies", 
                            True, 
                            f"Total: {data.get('total')}, Active: {data.get('active')}",
                            data
                        )
                        return True
                    else:
                        self.log_test(
                            "List Proxies", 
                            False, 
                            "Missing required response fields",
                            data
                        )
                        return False
                else:
                    self.log_test(
                        "List Proxies", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("List Proxies", False, f"Exception: {str(e)}")
            return False
    
    async def test_proxy_clear(self):
        """Test DELETE /api/proxies"""
        try:
            async with self.session.delete(f"{BACKEND_URL}/proxies") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check response structure
                    if "success" in data and "message" in data:
                        self.log_test(
                            "Clear Proxies", 
                            True, 
                            f"Success: {data.get('success')}, Message: {data.get('message')}",
                            data
                        )
                        return True
                    else:
                        self.log_test(
                            "Clear Proxies", 
                            False, 
                            "Missing required response fields",
                            data
                        )
                        return False
                else:
                    self.log_test(
                        "Clear Proxies", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Clear Proxies", False, f"Exception: {str(e)}")
            return False
    
    async def test_email_check(self):
        """Test POST /api/check with 90s timeout"""
        try:
            payload = {
                "emails": ["testfake12345@gmail.com"]
            }
            
            print("🔍 Starting email check (this may take up to 90 seconds)...")
            start_time = time.time()
            
            # Use 90 second timeout for this specific request
            timeout = aiohttp.ClientTimeout(total=90)
            async with aiohttp.ClientSession(timeout=timeout) as check_session:
                async with check_session.post(
                    f"{BACKEND_URL}/check",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    elapsed = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check response structure
                        required_fields = ["total", "results"]
                        if all(field in data for field in required_fields):
                            results = data.get("results", [])
                            if results and len(results) > 0:
                                result = results[0]
                                required_result_fields = ["email", "status", "exists", "details", "platform"]
                                
                                if all(field in result for field in required_result_fields):
                                    self.log_test(
                                        "Email Check", 
                                        True, 
                                        f"Status: {result.get('status')}, Exists: {result.get('exists')}, Platform: {result.get('platform')}, Time: {elapsed:.1f}s",
                                        data
                                    )
                                    return True
                                else:
                                    self.log_test(
                                        "Email Check", 
                                        False, 
                                        f"Missing required result fields. Time: {elapsed:.1f}s",
                                        data
                                    )
                                    return False
                            else:
                                self.log_test(
                                    "Email Check", 
                                    False, 
                                    f"No results returned. Time: {elapsed:.1f}s",
                                    data
                                )
                                return False
                        else:
                            self.log_test(
                                "Email Check", 
                                False, 
                                f"Missing required response fields. Time: {elapsed:.1f}s",
                                data
                            )
                            return False
                    else:
                        self.log_test(
                            "Email Check", 
                            False, 
                            f"HTTP {response.status}, Time: {elapsed:.1f}s",
                            await response.text()
                        )
                        return False
        except asyncio.TimeoutError:
            self.log_test("Email Check", False, "Request timed out after 90 seconds")
            return False
        except Exception as e:
            self.log_test("Email Check", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting Uber Eats Checker API Tests")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("Root Endpoint", self.test_root_endpoint),
            ("Add Proxy", self.test_proxy_add),
            ("List Proxies", self.test_proxy_list),
            ("Clear Proxies", self.test_proxy_clear),
            ("Email Check", self.test_email_check),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                success = await test_func()
                if success:
                    passed += 1
                # Small delay between tests
                await asyncio.sleep(1)
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
        
        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        # Summary of failures
        failures = [r for r in self.test_results if not r["success"]]
        if failures:
            print("\n❌ Failed Tests:")
            for failure in failures:
                print(f"   • {failure['test']}: {failure['details']}")
        
        return passed, total, self.test_results

async def main():
    """Main test runner"""
    async with UberEatsAPITester() as tester:
        passed, total, results = await tester.run_all_tests()
        
        # Write detailed results to file
        with open("/app/test_results_detailed.json", "w") as f:
            json.dump({
                "summary": {"passed": passed, "total": total, "success_rate": passed/total},
                "tests": results,
                "backend_url": BACKEND_URL
            }, f, indent=2)
        
        print(f"\n📝 Detailed results saved to /app/test_results_detailed.json")
        return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
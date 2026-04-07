#!/usr/bin/env python3
"""
Backend API Testing for Email Checker
Tests the 7 platform email checker backend API
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://app-kickoff-6.preview.emergentagent.com/api"

# Expected platforms (exactly 7)
EXPECTED_PLATFORMS = [
    "netflix", "amazon", "coinbase", "binance", 
    "spotify", "twitter", "disney_plus"
]

class BackendTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self.test_results = []
        self.failed_tests = []
        
    async def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success:
            self.failed_tests.append(test_name)
    
    async def test_platforms_endpoint(self):
        """Test GET /api/platforms - should return exactly 7 email and 7 phone platforms"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/platforms")
            
            if response.status_code != 200:
                await self.log_test("GET /api/platforms", False, f"Status code: {response.status_code}")
                return
            
            data = response.json()
            
            # Check email platforms count
            email_total = data.get("email_total", 0)
            if email_total != 7:
                await self.log_test("Email platforms count", False, f"Expected 7, got {email_total}")
                return
            
            # Check phone platforms count
            phone_total = data.get("phone_total", 0)
            if phone_total != 7:
                await self.log_test("Phone platforms count", False, f"Expected 7, got {phone_total}")
                return
            
            # Extract platform names from the nested structure
            email_platforms = [p["name"] for p in data.get("platforms", {}).get("email", [])]
            phone_platforms = [p["name"] for p in data.get("platforms", {}).get("phone", [])]
            
            # Check exact platform names
            email_set = set(email_platforms)
            expected_set = set(EXPECTED_PLATFORMS)
            
            if email_set != expected_set:
                missing = expected_set - email_set
                extra = email_set - expected_set
                await self.log_test("Email platforms content", False, f"Missing: {missing}, Extra: {extra}")
                return
            
            # Check phone platforms match email platforms
            phone_set = set(phone_platforms)
            if phone_set != expected_set:
                missing = expected_set - phone_set
                extra = phone_set - expected_set
                await self.log_test("Phone platforms content", False, f"Missing: {missing}, Extra: {extra}")
                return
            
            await self.log_test("GET /api/platforms", True, f"Email: {email_platforms}, Phone: {phone_platforms}")
            
        except Exception as e:
            await self.log_test("GET /api/platforms", False, f"Exception: {str(e)}")
    
    async def test_health_endpoint(self):
        """Test GET /api/health - verify custom_platforms_need_proxy is empty and all platforms listed"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/health")
            
            if response.status_code != 200:
                await self.log_test("GET /api/health", False, f"Status code: {response.status_code}")
                return
            
            data = response.json()
            
            # Check custom_platforms_need_proxy is empty array
            custom_proxy_needed = data.get("custom_platforms_need_proxy", None)
            if custom_proxy_needed != []:
                await self.log_test("custom_platforms_need_proxy", False, f"Expected [], got {custom_proxy_needed}")
                return
            
            # Check proxies_count is 0 (no proxy required)
            proxies_count = data.get("proxies_count", None)
            if proxies_count != 0:
                await self.log_test("proxies_count", False, f"Expected 0, got {proxies_count}")
                return
            
            # Check email_platforms contains all 7
            email_platforms = data.get("email_platforms", [])
            if set(email_platforms) != set(EXPECTED_PLATFORMS):
                await self.log_test("health email_platforms", False, f"Expected {EXPECTED_PLATFORMS}, got {email_platforms}")
                return
            
            # Check phone_platforms contains all 7
            phone_platforms = data.get("phone_platforms", [])
            if set(phone_platforms) != set(EXPECTED_PLATFORMS):
                await self.log_test("health phone_platforms", False, f"Expected {EXPECTED_PLATFORMS}, got {phone_platforms}")
                return
            
            await self.log_test("GET /api/health", True, f"Proxy count: {proxies_count}, Custom proxy needed: {custom_proxy_needed}")
            
        except Exception as e:
            await self.log_test("GET /api/health", False, f"Exception: {str(e)}")
    
    async def test_email_verification(self):
        """Test POST /api/verify with email for all 7 platforms"""
        test_email = "test@example.com"
        
        try:
            payload = {
                "identifiers": [test_email],
                "platforms": EXPECTED_PLATFORMS
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/verify",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                await self.log_test("POST /api/verify (email)", False, f"Status code: {response.status_code}, Response: {response.text}")
                return
            
            data = response.json()
            
            # Check response structure
            if "results" not in data or len(data["results"]) == 0:
                await self.log_test("Email verification structure", False, "Missing 'results' in response or empty results")
                return
            
            result = data["results"][0]
            platforms_results = result.get("platforms", [])
            
            # Check all 7 platforms returned results
            returned_platforms = [p.get("platform") for p in platforms_results]
            if len(returned_platforms) != 7:
                await self.log_test("Email verification platform count", False, f"Expected 7 platforms, got {len(returned_platforms)}: {returned_platforms}")
                return
            
            # Check no platform crashed/errored
            failed_platforms = []
            for platform_result in platforms_results:
                platform_name = platform_result.get("platform", "unknown")
                
                # Check required fields exist
                if "status" not in platform_result:
                    failed_platforms.append(f"{platform_name}: missing status")
                elif "domain" not in platform_result:
                    failed_platforms.append(f"{platform_name}: missing domain")
                elif platform_result.get("status") == "error":
                    failed_platforms.append(f"{platform_name}: error status")
            
            if failed_platforms:
                await self.log_test("Email verification platform results", False, f"Failed platforms: {failed_platforms}")
                return
            
            await self.log_test("POST /api/verify (email)", True, f"All 7 platforms responded successfully for {test_email}")
            
        except Exception as e:
            await self.log_test("POST /api/verify (email)", False, f"Exception: {str(e)}")
    
    async def test_phone_verification(self):
        """Test POST /api/verify with phone for all 7 platforms"""
        test_phone = "+33612345678"
        
        try:
            payload = {
                "identifiers": [test_phone],
                "platforms": EXPECTED_PLATFORMS
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/verify",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                await self.log_test("POST /api/verify (phone)", False, f"Status code: {response.status_code}, Response: {response.text}")
                return
            
            data = response.json()
            
            # Check response structure
            if "results" not in data or len(data["results"]) == 0:
                await self.log_test("Phone verification structure", False, "Missing 'results' in response or empty results")
                return
            
            result = data["results"][0]
            platforms_results = result.get("platforms", [])
            
            # Check all 7 platforms returned results
            returned_platforms = [p.get("platform") for p in platforms_results]
            if len(returned_platforms) != 7:
                await self.log_test("Phone verification platform count", False, f"Expected 7 platforms, got {len(returned_platforms)}: {returned_platforms}")
                return
            
            # Check no platform crashed
            crashed_platforms = []
            for platform_result in platforms_results:
                platform_name = platform_result.get("platform", "unknown")
                
                # Check for crash indicators
                if platform_result.get("status") == "error":
                    crashed_platforms.append(f"{platform_name}: error status")
                elif "exception" in str(platform_result).lower():
                    crashed_platforms.append(f"{platform_name}: exception detected")
            
            if crashed_platforms:
                await self.log_test("Phone verification platform stability", False, f"Crashed platforms: {crashed_platforms}")
                return
            
            await self.log_test("POST /api/verify (phone)", True, f"All 7 platforms responded for {test_phone}")
            
        except Exception as e:
            await self.log_test("POST /api/verify (phone)", False, f"Exception: {str(e)}")
    
    async def test_no_old_platforms(self):
        """Verify that old platforms like uber_eats, deliveroo, etc. are not present"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/platforms")
            
            if response.status_code != 200:
                await self.log_test("Old platforms check", False, f"Could not get platforms list: {response.status_code}")
                return
            
            data = response.json()
            
            # Extract platform names from the nested structure
            email_platforms = [p["name"] for p in data.get("platforms", {}).get("email", [])]
            phone_platforms = [p["name"] for p in data.get("platforms", {}).get("phone", [])]
            all_platforms = email_platforms + phone_platforms
            
            # Old platforms that should NOT exist
            old_platforms = [
                "uber_eats", "deliveroo", "ebay", "discord", "instagram", 
                "facebook", "linkedin", "github", "reddit", "tiktok"
            ]
            
            found_old = []
            for old_platform in old_platforms:
                if old_platform in all_platforms:
                    found_old.append(old_platform)
            
            if found_old:
                await self.log_test("Old platforms removed", False, f"Found old platforms that should be removed: {found_old}")
                return
            
            await self.log_test("Old platforms removed", True, "No old platforms found - cleanup successful")
            
        except Exception as e:
            await self.log_test("Old platforms check", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test 1: Platform list verification
        await self.test_platforms_endpoint()
        
        # Test 2: Health check
        await self.test_health_endpoint()
        
        # Test 3: Email verification
        await self.test_email_verification()
        
        # Test 4: Phone verification  
        await self.test_phone_verification()
        
        # Test 5: Verify old platforms removed
        await self.test_no_old_platforms()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = len(self.failed_tests)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for failed_test in self.failed_tests:
                print(f"  - {failed_test}")
        else:
            print(f"\n✅ ALL TESTS PASSED!")
        
        await self.client.aclose()
        
        return failed_tests == 0

async def main():
    """Main test runner"""
    tester = BackendTester()
    success = await tester.run_all_tests()
    
    if not success:
        sys.exit(1)
    
    print("\n🎉 Backend API testing completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
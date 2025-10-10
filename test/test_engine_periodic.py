#!/usr/bin/env python3
"""
Sasya Arogya Engine Periodic Test Suite

This script tests various engine functionalities including:
- CNN classification for disease diagnosis
- Prescription recommendations
- Insurance premium calculation and certificate generation
- General crop care advice
- Non-crop intent handling

The script is designed to run periodically in OpenShift Kubernetes cluster
and includes session management, test case randomization, and proper sequencing.
"""

import asyncio
import aiohttp
import json
import random
import time
import base64
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SasyaArogyaEngineTester:
    """Test suite for Sasya Arogya Engine"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session_id = self._generate_session_id()
        self.test_results = []
        self.classification_results = {}  # Store classification results for prescription tests
        
    def _generate_session_id(self) -> str:
        """Generate session ID with timestamp format: fsm_session_dd_mm_yyyy_hh_mm"""
        now = datetime.now()
        timestamp = now.strftime("%d_%m_%Y_%H_%M")
        return f"fsm_session_{timestamp}"
    
    async def _make_request(self, message: str, image_b64: Optional[str] = None) -> Dict[str, Any]:
        """Make HTTP request to the engine"""
        url = f"{self.base_url}/sasya-chikitsa/chat-stream"
        payload = {
            "message": message,
            "session_id": self.session_id
        }
        
        if image_b64:
            payload["image_b64"] = image_b64
            
        try:
            # Set timeout for the entire request
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"HTTP {response.status}: {await response.text()}")
                        return {"error": f"HTTP {response.status}"}
        except asyncio.TimeoutError:
            logger.error("Request timed out after 30 seconds")
            return {"error": "Request timeout"}
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return {"error": str(e)}
    
    def _load_test_image(self, image_path: str) -> Optional[str]:
        """Load and encode test image"""
        try:
            if os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            else:
                logger.warning(f"Test image not found: {image_path}")
                return None
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {str(e)}")
            return None
    
    async def test_cnn_classification(self) -> List[Dict[str, Any]]:
        """Test CNN disease classification functionality"""
        logger.info("🧪 Testing CNN Classification...")
        
        test_cases = [
            {
                "name": "Rice Leaf Blight Classification",
                "message": "Please diagnose this plant disease",
                "image_path": "resources/images_for_test/rice_leaf_blight.jpg",
                "expected_disease": "rice_leaf_blight"
            },
            {
                "name": "Apple Leaf Disease Classification", 
                "message": "What disease is affecting this apple tree?",
                "image_path": "resources/images_for_test/apple_leaf_disease.jpg",
                "expected_disease": "apple_scab"
            },
            {
                "name": "Tomato Disease Classification",
                "message": "Identify the disease in this tomato plant",
                "image_path": "resources/images_for_test/tomato_disease.jpg",
                "expected_disease": "tomato_blight"
            },
            {
                "name": "Wheat Rust Classification",
                "message": "Please analyze this wheat plant disease",
                "image_path": "resources/images_for_test/wheat_rust.jpg",
                "expected_disease": "wheat_rust"
            }
        ]
        
        results = []
        for test_case in test_cases:
            logger.info(f"  Testing: {test_case['name']}")
            
            # Load test image
            image_b64 = self._load_test_image(test_case["image_path"])
            
            # Make request
            response = await self._make_request(test_case["message"], image_b64)
            
            # Store classification result for prescription tests
            if not response.get("error") and "disease" in response.get("response", "").lower():
                self.classification_results[test_case["expected_disease"]] = {
                    "disease": test_case["expected_disease"],
                    "response": response.get("response", ""),
                    "confidence": response.get("confidence_scores", {}).get("classification", 0.0)
                }
            
            results.append({
                "test_name": test_case["name"],
                "expected_disease": test_case["expected_disease"],
                "response": response,
                "success": not response.get("error") and "disease" in response.get("response", "").lower(),
                "timestamp": datetime.now().isoformat()
            })
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        return results
    
    async def test_prescription_recommendations(self) -> List[Dict[str, Any]]:
        """Test prescription recommendation functionality"""
        logger.info("🧪 Testing Prescription Recommendations...")
        
        # Only run if we have classification results
        if not self.classification_results:
            logger.warning("No classification results available, skipping prescription tests")
            return []
        
        test_cases = []
        
        # Generate prescription test cases based on classification results
        for disease, classification_data in self.classification_results.items():
            test_cases.append({
                "name": f"Prescription for {disease.replace('_', ' ').title()}",
                "message": f"Give me treatment recommendations for {disease.replace('_', ' ')}",
                "expected_disease": disease,
                "classification_data": classification_data
            })
        
        # Add some general prescription test cases
        test_cases.extend([
            {
                "name": "General Disease Treatment",
                "message": "What treatment should I use for leaf blight?",
                "expected_disease": "general",
                "classification_data": None
            },
            {
                "name": "Organic Treatment Request",
                "message": "I want organic treatment options for my crops",
                "expected_disease": "organic",
                "classification_data": None
            }
        ])
        
        results = []
        for test_case in test_cases:
            logger.info(f"  Testing: {test_case['name']}")
            
            response = await self._make_request(test_case["message"])
            
            results.append({
                "test_name": test_case["name"],
                "expected_disease": test_case["expected_disease"],
                "response": response,
                "success": not response.get("error") and any(keyword in response.get("response", "").lower() 
                    for keyword in ["treatment", "prescription", "medicine", "spray", "dose"]),
                "timestamp": datetime.now().isoformat()
            })
            
            await asyncio.sleep(1)
        
        return results
    
    async def test_insurance_premium_calculation(self) -> List[Dict[str, Any]]:
        """Test insurance premium calculation functionality"""
        logger.info("🧪 Testing Insurance Premium Calculation...")
        
        test_cases = [
            {
                "name": "Wheat Premium Calculation",
                "message": "What is the cost of premium for my 5 hectare wheat farm in Punjab?",
                "expected_crop": "wheat",
                "expected_area": 5,
                "expected_state": "Punjab"
            },
            {
                "name": "Rice Premium Calculation",
                "message": "Calculate insurance premium for my 3 hectare rice farm in Tamil Nadu",
                "expected_crop": "rice",
                "expected_area": 3,
                "expected_state": "Tamil Nadu"
            },
            {
                "name": "Tomato Premium Calculation",
                "message": "How much will insurance cost for my 2 hectare tomato farm in Maharashtra?",
                "expected_crop": "tomato",
                "expected_area": 2,
                "expected_state": "Maharashtra"
            },
            {
                "name": "Cotton Premium Calculation",
                "message": "What's the premium for cotton insurance in Gujarat for 4 hectares?",
                "expected_crop": "cotton",
                "expected_area": 4,
                "expected_state": "Gujarat"
            }
        ]
        
        results = []
        for test_case in test_cases:
            logger.info(f"  Testing: {test_case['name']}")
            
            response = await self._make_request(test_case["message"])
            
            results.append({
                "test_name": test_case["name"],
                "expected_crop": test_case["expected_crop"],
                "expected_area": test_case["expected_area"],
                "expected_state": test_case["expected_state"],
                "response": response,
                "success": not response.get("error") and any(keyword in response.get("response", "").lower() 
                    for keyword in ["premium", "cost", "rupees", "₹", "subsidy"]),
                "timestamp": datetime.now().isoformat()
            })
            
            await asyncio.sleep(1)
        
        return results
    
    async def test_insurance_certificate_generation(self) -> List[Dict[str, Any]]:
        """Test insurance certificate generation functionality"""
        logger.info("🧪 Testing Insurance Certificate Generation...")
        
        test_cases = [
            {
                "name": "Wheat Insurance Purchase",
                "message": "Help me apply for crop insurance for my 5 hectare wheat farm in Punjab",
                "expected_crop": "wheat",
                "expected_area": 5,
                "expected_state": "Punjab"
            },
            {
                "name": "Rice Insurance Purchase",
                "message": "I want to buy crop insurance for my 3 hectare rice farm in Tamil Nadu",
                "expected_crop": "rice",
                "expected_area": 3,
                "expected_state": "Tamil Nadu"
            },
            {
                "name": "Tomato Insurance Purchase",
                "message": "Generate insurance certificate for my 2 hectare tomato farm in Maharashtra",
                "expected_crop": "tomato",
                "expected_area": 2,
                "expected_state": "Maharashtra"
            }
        ]
        
        results = []
        for test_case in test_cases:
            logger.info(f"  Testing: {test_case['name']}")
            
            response = await self._make_request(test_case["message"])
            
            results.append({
                "test_name": test_case["name"],
                "expected_crop": test_case["expected_crop"],
                "expected_area": test_case["expected_area"],
                "expected_state": test_case["expected_state"],
                "response": response,
                "success": not response.get("error") and any(keyword in response.get("response", "").lower() 
                    for keyword in ["certificate", "policy", "purchase", "generated", "pdf"]),
                "timestamp": datetime.now().isoformat()
            })
            
            await asyncio.sleep(1)
        
        return results
    
    async def test_general_crop_care(self) -> List[Dict[str, Any]]:
        """Test general crop care advice functionality"""
        logger.info("🧪 Testing General Crop Care...")
        
        test_cases = [
            {
                "name": "Soil Watering Tips",
                "message": "How often should I water my tomato plants?",
                "category": "watering"
            },
            {
                "name": "Weather Tips for Rice",
                "message": "What weather conditions are best for rice cultivation?",
                "category": "weather"
            },
            {
                "name": "Soil Preparation",
                "message": "How should I prepare soil for wheat farming?",
                "category": "soil"
            },
            {
                "name": "Fertilizer Advice",
                "message": "What fertilizer should I use for my crops?",
                "category": "fertilizer"
            },
            {
                "name": "Pest Control",
                "message": "How can I control pests in my garden naturally?",
                "category": "pest_control"
            },
            {
                "name": "Harvesting Tips",
                "message": "When is the best time to harvest wheat?",
                "category": "harvesting"
            },
            {
                "name": "Crop Rotation",
                "message": "What crops should I rotate with rice?",
                "category": "crop_rotation"
            },
            {
                "name": "Seasonal Care",
                "message": "How should I care for my crops during monsoon season?",
                "category": "seasonal"
            }
        ]
        
        results = []
        for test_case in test_cases:
            logger.info(f"  Testing: {test_case['name']}")
            
            response = await self._make_request(test_case["message"])
            
            results.append({
                "test_name": test_case["name"],
                "category": test_case["category"],
                "response": response,
                "success": not response.get("error") and len(response.get("response", "")) > 50,
                "timestamp": datetime.now().isoformat()
            })
            
            await asyncio.sleep(1)
        
        return results
    
    async def test_non_crop_intent(self) -> List[Dict[str, Any]]:
        """Test non-crop intent handling"""
        logger.info("🧪 Testing Non-Crop Intent Handling...")
        
        test_cases = [
            {
                "name": "Weather Query",
                "message": "What's the weather like today?",
                "expected_handling": "redirect_or_inform"
            },
            {
                "name": "General Chat",
                "message": "Hello, how are you?",
                "expected_handling": "polite_response"
            },
            {
                "name": "Off-topic Question",
                "message": "What's the capital of India?",
                "expected_handling": "redirect_to_agriculture"
            },
            {
                "name": "Technical Support",
                "message": "I'm having trouble with the app",
                "expected_handling": "support_response"
            },
            {
                "name": "Random Text",
                "message": "asdfghjkl",
                "expected_handling": "clarification_request"
            }
        ]
        
        results = []
        for test_case in test_cases:
            logger.info(f"  Testing: {test_case['name']}")
            
            response = await self._make_request(test_case["message"])
            
            results.append({
                "test_name": test_case["name"],
                "expected_handling": test_case["expected_handling"],
                "response": response,
                "success": not response.get("error"),
                "timestamp": datetime.now().isoformat()
            })
            
            await asyncio.sleep(1)
        
        return results
    
    def _randomize_test_cases(self, test_cases: List[Dict[str, Any]], max_cases: int = None) -> List[Dict[str, Any]]:
        """Randomize test cases and optionally limit the number"""
        if max_cases and len(test_cases) > max_cases:
            return random.sample(test_cases, max_cases)
        return random.shuffle(test_cases) or test_cases
    
    async def run_periodic_tests(self, max_tests_per_category: int = 3):
        """Run periodic tests with randomization"""
        logger.info(f"🚀 Starting periodic tests for session: {self.session_id}")
        logger.info(f"📊 Max tests per category: {max_tests_per_category}")
        
        start_time = time.time()
        
        # Test categories and their functions
        test_categories = [
            ("CNN Classification", self.test_cnn_classification, False),  # Don't randomize - needed for prescriptions
            ("Prescription Recommendations", self.test_prescription_recommendations, False),  # Don't randomize - depends on classification
            ("Insurance Premium Calculation", self.test_insurance_premium_calculation, True),
            ("Insurance Certificate Generation", self.test_insurance_certificate_generation, True),
            ("General Crop Care", self.test_general_crop_care, True),
            ("Non-Crop Intent", self.test_non_crop_intent, True)
        ]
        
        all_results = {}
        
        for category_name, test_function, should_randomize in test_categories:
            logger.info(f"\n{'='*50}")
            logger.info(f"Testing Category: {category_name}")
            logger.info(f"{'='*50}")
            
            try:
                results = await test_function()
                
                if should_randomize and len(results) > max_tests_per_category:
                    results = random.sample(results, max_tests_per_category)
                
                all_results[category_name] = results
                self.test_results.extend(results)
                
                # Log category summary
                success_count = sum(1 for r in results if r.get("success", False))
                total_count = len(results)
                logger.info(f"✅ {category_name}: {success_count}/{total_count} tests passed")
                
            except Exception as e:
                logger.error(f"❌ Error in {category_name}: {str(e)}")
                all_results[category_name] = [{"error": str(e), "test_name": category_name}]
        
        # Calculate overall statistics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success", False))
        failed_tests = total_tests - successful_tests
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Log final summary
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 PERIODIC TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful: {successful_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(successful_tests/total_tests*100):.1f}%")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"{'='*60}")
        
        # Save results to file
        self._save_test_results(all_results, duration)
        
        return all_results
    
    def _save_test_results(self, results: Dict[str, List[Dict[str, Any]]], duration: float):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        summary = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "total_tests": len(self.test_results),
            "successful_tests": sum(1 for r in self.test_results if r.get("success", False)),
            "failed_tests": len(self.test_results) - sum(1 for r in self.test_results if r.get("success", False)),
            "success_rate": (sum(1 for r in self.test_results if r.get("success", False)) / len(self.test_results) * 100) if self.test_results else 0,
            "results": results
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"📄 Test results saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save test results: {str(e)}")

async def main():
    """Main function to run periodic tests"""
    # Get engine URL from environment variable or use default
    engine_url = os.getenv("SASYA_ENGINE_URL", "http://localhost:8080")
    
    logger.info(f"🌾 Sasya Arogya Engine Periodic Test Suite")
    logger.info(f"🔗 Engine URL: {engine_url}")
    
    # Create tester instance
    tester = SasyaArogyaEngineTester(engine_url)
    
    # Get max tests per category from environment variable
    max_tests = int(os.getenv("MAX_TESTS_PER_CATEGORY", "3"))
    
    # Set overall timeout for the entire test suite (5 minutes)
    try:
        await asyncio.wait_for(
            tester.run_periodic_tests(max_tests_per_category=max_tests),
            timeout=300  # 5 minutes total timeout
        )
    except asyncio.TimeoutError:
        logger.error("❌ Test suite timed out after 5 minutes")
        return 1
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())

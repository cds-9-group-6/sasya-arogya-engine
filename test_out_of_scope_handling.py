#!/usr/bin/env python3
"""
Test script for out-of-scope question handling
Tests the complete flow of detecting and responding to non-agricultural questions
"""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, List
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OutOfScopeTestSuite:
    """Test suite for out-of-scope question handling"""
    
    def __init__(self, api_base_url: str = "http://localhost:9080"):
        self.api_base_url = api_base_url
        self.prometheus_url = "http://localhost:9090"
        self.test_results = []
        
        # Test cases organized by category
        self.test_cases = {
            "technology": [
                "What's the best smartphone to buy?",
                "How do I fix my computer?",
                "Which laptop is good for programming?",
                "Can you help me with my internet connection?",
                "How to install software on my phone?"
            ],
            "medical": [
                "I have a headache, what medicine should I take?", 
                "How to treat high blood pressure?",
                "What are the symptoms of diabetes?",
                "Should I see a doctor for my back pain?",
                "How to lose weight quickly?"
            ],
            "automotive": [
                "How do I fix my car engine?",
                "What's the best car insurance?",
                "How to change car tires?",
                "Which car should I buy?",
                "How to improve car mileage?"
            ],
            "cooking": [
                "How do I make chocolate cake?",
                "What's the best recipe for pasta?",
                "How to cook rice properly?",
                "Which spices go well with chicken?",
                "How to make homemade bread?"
            ],
            "weather": [
                "What's the weather like today?",
                "Will it rain tomorrow?",
                "How hot will it get this week?",
                "What's the humidity level?",
                "When will the monsoon arrive?"
            ],
            "agricultural": [
                "What disease does my tomato plant have?",
                "How to treat wheat rust?",
                "What pesticide should I use for aphids?",
                "How much crop insurance costs for rice?",
                "Where can I buy fertilizers?"
            ]
        }
    
    async def test_api_endpoint(self, message: str, session_id: str) -> Dict:
        """Test a single message against the API endpoint"""
        
        url = f"{self.api_base_url}/sasya-chikitsa/chat"
        payload = {
            "message": message,
            "session_id": session_id
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    "success": True,
                    "response": response_data.get("response", ""),
                    "session_id": response_data.get("session_id", ""),
                    "current_node": response_data.get("current_node", ""),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
        
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "status_code": None
            }
    
    def check_prometheus_metrics(self) -> Dict:
        """Check if out-of-scope metrics are being recorded in Prometheus"""
        
        metrics_to_check = [
            "out_of_scope_requests_total",
            "unhandled_intents_total", 
            "intent_confidence_score",
            "response_type_usage_total"
        ]
        
        metrics_data = {}
        
        for metric in metrics_to_check:
            try:
                url = f"{self.prometheus_url}/api/v1/query?query={metric}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        results = data["data"]["result"]
                        metrics_data[metric] = {
                            "available": True,
                            "series_count": len(results),
                            "sample_data": results[:3] if results else []
                        }
                    else:
                        metrics_data[metric] = {
                            "available": False,
                            "error": "Query failed"
                        }
                else:
                    metrics_data[metric] = {
                        "available": False,
                        "error": f"HTTP {response.status_code}"
                    }
                    
            except requests.exceptions.RequestException as e:
                metrics_data[metric] = {
                    "available": False,
                    "error": f"Connection failed: {str(e)}"
                }
        
        return metrics_data
    
    def analyze_response_appropriateness(self, message: str, response: str, category: str) -> Dict:
        """Analyze if the response is appropriate for the given message"""
        
        out_of_scope_indicators = [
            "can only help with crop care",
            "specialized in agricultural assistance", 
            "only able to answer questions on crop care",
            "designed to assist with agricultural questions",
            "can only provide assistance with crop care",
            "agricultural questions only",
            "crop care and agricultural",
            "sorry", "apologize", 
            "agricultural assistance",
            "farming-related topics",
            "plant diseases, crop care"
        ]
        
        is_out_of_scope_response = any(indicator.lower() in response.lower() 
                                     for indicator in out_of_scope_indicators)
        
        is_agricultural_question = category == "agricultural"
        
        # Expected behavior analysis
        if is_agricultural_question:
            # Agricultural questions should NOT get out-of-scope responses
            appropriate = not is_out_of_scope_response
            expected_behavior = "Should handle agricultural question"
        else:
            # Non-agricultural questions SHOULD get out-of-scope responses  
            appropriate = is_out_of_scope_response
            expected_behavior = "Should reject non-agricultural question"
        
        return {
            "appropriate": appropriate,
            "is_out_of_scope_response": is_out_of_scope_response,
            "expected_behavior": expected_behavior,
            "response_length": len(response),
            "category": category
        }
    
    async def run_comprehensive_test(self) -> Dict:
        """Run comprehensive test suite"""
        
        logger.info("🧪 Starting comprehensive out-of-scope test suite...")
        
        # Test API connectivity first
        logger.info("🔗 Testing API connectivity...")
        connectivity_test = await self.test_api_endpoint("Hello", "connectivity_test")
        
        if not connectivity_test["success"]:
            logger.error(f"❌ API connectivity failed: {connectivity_test['error']}")
            return {"success": False, "error": "API not available"}
        
        logger.info("✅ API connectivity confirmed")
        
        # Run tests for each category
        all_results = {}
        total_tests = 0
        successful_tests = 0
        appropriate_responses = 0
        
        for category, test_messages in self.test_cases.items():
            logger.info(f"📝 Testing {category} questions ({len(test_messages)} tests)...")
            
            category_results = []
            
            for i, message in enumerate(test_messages):
                session_id = f"test_{category}_{i}_{int(time.time())}"
                
                # Test the message
                api_result = await self.test_api_endpoint(message, session_id)
                total_tests += 1
                
                if api_result["success"]:
                    successful_tests += 1
                    
                    # Analyze response appropriateness
                    response_analysis = self.analyze_response_appropriateness(
                        message, api_result["response"], category
                    )
                    
                    if response_analysis["appropriate"]:
                        appropriate_responses += 1
                    
                    test_result = {
                        "message": message,
                        "session_id": session_id,
                        "api_result": api_result,
                        "analysis": response_analysis
                    }
                    
                    category_results.append(test_result)
                    
                    # Log result
                    status = "✅" if response_analysis["appropriate"] else "❌"
                    logger.info(f"  {status} {message[:50]}... -> {'OUT-OF-SCOPE' if response_analysis['is_out_of_scope_response'] else 'HANDLED'}")
                
                else:
                    logger.error(f"  ❌ API failed for: {message[:50]}... -> {api_result['error']}")
                    category_results.append({
                        "message": message,
                        "session_id": session_id,
                        "api_result": api_result,
                        "analysis": {"appropriate": False, "error": "API call failed"}
                    })
                
                # Small delay between requests
                await asyncio.sleep(0.5)
            
            all_results[category] = category_results
        
        # Check Prometheus metrics
        logger.info("📊 Checking Prometheus metrics...")
        metrics_data = self.check_prometheus_metrics()
        
        # Calculate summary statistics
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        appropriateness_rate = (appropriate_responses / successful_tests * 100) if successful_tests > 0 else 0
        
        summary = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "appropriate_responses": appropriate_responses,
            "success_rate": success_rate,
            "appropriateness_rate": appropriateness_rate,
            "categories_tested": len(self.test_cases),
            "metrics_available": sum(1 for m in metrics_data.values() if m.get("available")),
            "total_metrics": len(metrics_data)
        }
        
        logger.info(f"📈 Test Summary:")
        logger.info(f"  Total Tests: {summary['total_tests']}")
        logger.info(f"  Successful API Calls: {summary['successful_tests']} ({summary['success_rate']:.1f}%)")
        logger.info(f"  Appropriate Responses: {summary['appropriate_responses']} ({summary['appropriateness_rate']:.1f}%)")
        logger.info(f"  Metrics Available: {summary['metrics_available']}/{summary['total_metrics']}")
        
        return {
            "success": True,
            "summary": summary,
            "detailed_results": all_results,
            "metrics_data": metrics_data,
            "timestamp": time.time()
        }
    
    def generate_report(self, test_results: Dict) -> str:
        """Generate a detailed test report"""
        
        if not test_results.get("success"):
            return f"❌ Test suite failed: {test_results.get('error', 'Unknown error')}"
        
        summary = test_results["summary"]
        metrics = test_results["metrics_data"]
        
        report_lines = [
            "🧪 OUT-OF-SCOPE HANDLING TEST REPORT",
            "=" * 50,
            "",
            "📊 SUMMARY STATISTICS:",
            f"  • Total Test Cases: {summary['total_tests']}",
            f"  • Successful API Calls: {summary['successful_tests']} ({summary['success_rate']:.1f}%)",
            f"  • Appropriate Responses: {summary['appropriate_responses']} ({summary['appropriateness_rate']:.1f}%)",
            f"  • Categories Tested: {summary['categories_tested']}",
            "",
            "📈 METRICS AVAILABILITY:",
        ]
        
        for metric_name, metric_data in metrics.items():
            status = "✅" if metric_data.get("available") else "❌"
            series = metric_data.get("series_count", 0)
            report_lines.append(f"  • {metric_name}: {status} ({series} series)")
        
        report_lines.extend([
            "",
            "🎯 CATEGORY BREAKDOWN:",
        ])
        
        for category, results in test_results["detailed_results"].items():
            successful = sum(1 for r in results if r["api_result"]["success"])
            appropriate = sum(1 for r in results if r.get("analysis", {}).get("appropriate", False))
            total = len(results)
            
            report_lines.append(f"  • {category.capitalize()}: {appropriate}/{successful} appropriate responses ({total} total)")
        
        # Recommendations
        report_lines.extend([
            "",
            "💡 RECOMMENDATIONS:",
        ])
        
        if summary["appropriateness_rate"] < 90:
            report_lines.append("  ⚠️  Consider improving intent analysis accuracy")
        
        if summary["success_rate"] < 95:
            report_lines.append("  ⚠️  API reliability issues detected")
        
        available_metrics = summary["metrics_available"]
        total_metrics = summary["total_metrics"]
        if available_metrics < total_metrics:
            report_lines.append("  ⚠️  Some metrics are not being recorded properly")
        
        if summary["appropriateness_rate"] >= 90 and available_metrics == total_metrics:
            report_lines.append("  ✅ Out-of-scope handling is working correctly!")
        
        return "\n".join(report_lines)


async def main():
    """Main function to run the test suite"""
    
    test_suite = OutOfScopeTestSuite()
    
    try:
        results = await test_suite.run_comprehensive_test()
        report = test_suite.generate_report(results)
        
        print("\n" + report + "\n")
        
        # Save detailed results to file
        timestamp = int(time.time())
        results_file = f"out_of_scope_test_results_{timestamp}.json"
        
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📁 Detailed results saved to: {results_file}")
        
        # Exit code based on test success
        if results.get("success") and results["summary"]["appropriateness_rate"] >= 80:
            sys.exit(0)
        else:
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Test suite failed with exception: {str(e)}", exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())

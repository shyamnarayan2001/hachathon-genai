# test_retail_bot.py
import pytest
import aiohttp
import asyncio
from typing import Dict, List
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetailBotTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.chat_endpoint = f"{base_url}/api/chat"
        self.session = None
        self.conversation_history = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_message(self, message: str) -> Dict:
        """Send a message to the bot and return the response"""
        try:
            async with self.session.post(
                self.chat_endpoint,
                json={"content": message},
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                self.conversation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "user_message": message,
                    "bot_response": result.get("response", ""),
                    "status_code": response.status
                })
                return result
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise

    def save_conversation_history(self, filename: str = "conversation_history.json"):
        """Save the conversation history to a file"""
        with open(filename, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)

    @staticmethod
    def analyze_response(response: str) -> Dict:
        """Analyze the bot's response for key information"""
        response_lower = response.lower()
        analysis = {
            "contains_price": "$" in response,
            "contains_size": any(f"size {i}" in response_lower for i in range(1, 15)),
            "contains_stock": "in stock" in response_lower,
            "contains_question": "?" in response,
            "shoe_types_mentioned": [],
            "contains_apology": any(word in response_lower for word in ["apologize", "sorry", "unfortunately"]),
            "contains_alternative": "alternative" in response_lower,
            "contains_shoe_name": any(name.lower() in response_lower for name in [
                "Speed Runner Pro", "Marathon Elite", "Comfort Walker", 
                "Trail Blazer X", "Hiking Master"
            ]),
            "is_helpful": False  # Will be set based on content
        }
        
        # Check for shoe types
        shoe_types = ["running", "hiking", "walking"]
        for shoe_type in shoe_types:
            if shoe_type.lower() in response_lower:
                analysis["shoe_types_mentioned"].append(shoe_type)
        
        # Check if response is helpful (has any meaningful content)
        analysis["is_helpful"] = any([
            analysis["contains_price"],
            analysis["contains_size"],
            analysis["contains_stock"],
            analysis["shoe_types_mentioned"],
            analysis["contains_alternative"],
            analysis["contains_shoe_name"],
            len(response_lower) > 50  # Response has substantial content
        ])
        
        return analysis

class TestCases:
    @pytest.mark.asyncio
    async def test_basic_queries(self):
        """Test basic inventory queries"""
        async with RetailBotTester() as tester:
            # Test general inventory query
            response = await tester.send_message("What shoes do you have?")
            assert response["response"] != ""
            analysis = RetailBotTester.analyze_response(response["response"])
            assert analysis["is_helpful"]
            
            # Test specific activity query
            response = await tester.send_message("Show me running shoes")
            analysis = RetailBotTester.analyze_response(response["response"])
            assert analysis["is_helpful"]
            assert "running" in analysis["shoe_types_mentioned"]
            
            # Test size query
            response = await tester.send_message("Do you have any shoes in size 10?")
            analysis = RetailBotTester.analyze_response(response["response"])
            assert analysis["contains_size"]

    @pytest.mark.asyncio
    async def test_complex_queries(self):
        """Test complex, multi-part queries"""
        async with RetailBotTester() as tester:
            # Test combined activity and size query
            response = await tester.send_message("I need running shoes in size 10")
            analysis = RetailBotTester.analyze_response(response["response"])
            assert analysis["is_helpful"]
            assert analysis["contains_size"]
            assert analysis["contains_stock"]
            
            # Test recommendation query
            response = await tester.send_message("What would you recommend for trail hiking?")
            analysis = RetailBotTester.analyze_response(response["response"])
            assert analysis["is_helpful"]
            assert analysis["contains_shoe_name"]

    @pytest.mark.asyncio
    async def test_edge_cases(self):
        """Test edge cases and error handling"""
        async with RetailBotTester() as tester:
            # Test invalid size
            response = await tester.send_message("Do you have shoes in size 99?")
            analysis = RetailBotTester.analyze_response(response["response"])
            assert analysis["contains_apology"] or analysis["contains_alternative"]
            
            # Test unknown activity
            response = await tester.send_message("I need shoes for swimming")
            analysis = RetailBotTester.analyze_response(response["response"])
            assert analysis["is_helpful"]
            assert analysis["contains_shoe_name"] or analysis["contains_alternative"]

    @pytest.mark.asyncio
    async def test_conversation_flow(self):
        """Test a complete conversation flow"""
        async with RetailBotTester() as tester:
            conversation_checks = [
                {
                    "message": "What running shoes do you have?",
                    "checks": ["contains_price", "contains_shoe_name"]
                },
                {
                    "message": "Tell me more about the Speed Runner Pro",
                    "checks": ["contains_shoe_name"]
                },
                {
                    "message": "Do you have it in size 10?",
                    "checks": ["contains_size", "contains_stock"]
                },
                {
                    "message": "How does it compare to the Marathon Elite?",
                    "checks": ["contains_shoe_name", "contains_price"]
                },
                {
                    "message": "Which one would you recommend for marathon training?",
                    "checks": ["contains_shoe_name"]
                },
                {
                    "message": "I'll take the Speed Runner Pro",
                    "checks": ["contains_shoe_name"]
                }
            ]
            
            previous_response = None
            for conv in conversation_checks:
                response = await tester.send_message(conv["message"])
                analysis = RetailBotTester.analyze_response(response["response"])
                
                # Print detailed info for debugging
                logger.info(f"\nMessage: {conv['message']}")
                logger.info(f"Response: {response['response']}")
                logger.info(f"Analysis: {json.dumps(analysis, indent=2)}")
                
                # Check that at least one of the expected elements is present
                assert any(analysis[check] for check in conv["checks"]), \
                    f"Response to '{conv['message']}' missing expected elements. Response: {response['response']}"
                
                # Check that response is different from previous
                if previous_response:
                    assert response["response"] != previous_response, \
                        "Got identical response for different questions"
                
                previous_response = response["response"]
                await asyncio.sleep(0.5)
            
            # Save conversation history
            tester.save_conversation_history("conversation_history.json")

async def run_manual_tests_async():
    """Run manual tests with specific scenarios"""
    async with RetailBotTester() as tester:
        test_cases = [
            {
                "name": "Price Comparison",
                "message": "What's the price difference between Speed Runner Pro and Marathon Elite?",
                "expected_checks": ["contains_price", "contains_shoe_name"]
            },
            {
                "name": "Stock Availability",
                "message": "Which running shoes are currently in stock?",
                "expected_checks": ["contains_stock", "contains_shoe_name"]
            },
            {
                "name": "Recommendation",
                "message": "I'm a beginner looking for comfortable walking shoes",
                "expected_checks": ["contains_shoe_name", "shoe_types_mentioned"]
            }
        ]
        
        for test_case in test_cases:
            response = await tester.send_message(test_case["message"])
            analysis = RetailBotTester.analyze_response(response["response"])
            
            print(f"\n{test_case['name']} Test:")
            print(f"Message: {test_case['message']}")
            print(f"Response: {response['response']}")
            print("Analysis:")
            for check in test_case["expected_checks"]:
                print(f"- {check}: {analysis[check]}")
        
        # Save test results
        tester.save_conversation_history("manual_test_results.json")

def run_manual_tests():
    """Wrapper for running manual tests"""
    asyncio.run(run_manual_tests_async())

if __name__ == "__main__":
    print("Running automated tests...")
    pytest.main([__file__, "-v", "--disable-warnings"])
    
    print("\nRunning manual tests...")
    run_manual_tests()
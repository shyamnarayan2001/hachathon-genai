# load_test_retail_bot.py
import asyncio
import aiohttp
import time
from typing import List, Dict
import statistics
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.chat_endpoint = f"{base_url}/api/chat"
        self.results: List[Dict] = []

    async def send_message(self, message: str, session: aiohttp.ClientSession) -> Dict:
        """Send a single message and measure response time"""
        start_time = time.time()
        try:
            async with session.post(
                self.chat_endpoint,
                json={"content": message},
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                end_time = time.time()
                return {
                    "message": message,
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            end_time = time.time()
            logger.error(f"Error in request: {str(e)}")
            return {
                "message": message,
                "error": str(e),
                "response_time": end_time - start_time,
                "success": False,
                "timestamp": datetime.now().isoformat()
            }

    async def run_load_test(
        self,
        num_requests: int = 100,
        concurrent_requests: int = 10,
        delay_between_batches: float = 0.1
    ):
        """Run load test with specified parameters"""
        test_messages = [
            "What shoes do you have?",
            "Show me running shoes",
            "Do you have any shoes in size 10?",
            "Tell me about the Speed Runner Pro",
            "What hiking shoes are available?",
        ]

        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(num_requests):
                message = test_messages[i % len(test_messages)]
                tasks.append(self.send_message(message, session))
                
                if len(tasks) >= concurrent_requests:
                    batch_results = await asyncio.gather(*tasks)
                    self.results.extend(batch_results)
                    tasks = []
                    await asyncio.sleep(delay_between_batches)
            
            if tasks:
                batch_results = await asyncio.gather(*tasks)
                self.results.extend(batch_results)

    def analyze_results(self) -> Dict:
        """Analyze load test results"""
        response_times = [r["response_time"] for r in self.results]
        successful_requests = sum(1 for r in self.results if r["success"])
        
        analysis = {
            "total_requests": len(self.results),
            "successful_requests": successful_requests,
            "success_rate": (successful_requests / len(self.results)) * 100,
            "response_times": {
                "min": min(response_times),
                "max": max(response_times),
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": sorted(response_times)[int(len(response_times) * 0.95)]
            },
            "errors": [r for r in self.results if not r["success"]]
        }
        
        return analysis

async def main():
    """Run load tests with different configurations"""
    tester = LoadTester()
    
    # Light load test
    logger.info("Running light load test (100 requests, 10 concurrent)...")
    await tester.run_load_test(num_requests=100, concurrent_requests=10)
    light_results = tester.analyze_results()
    
    # Medium load test
    logger.info("Running medium load test (500 requests, 50 concurrent)...")
    await tester.run_load_test(num_requests=500, concurrent_requests=50)
    medium_results = tester.analyze_results()
    
    # Heavy load test
    logger.info("Running heavy load test (1000 requests, 100 concurrent)...")
    await tester.run_load_test(num_requests=1000, concurrent_requests=100)
    heavy_results = tester.analyze_results()
    
    # Print results
    print("\nLoad Test Results:")
    print("\nLight Load Test:")
    print(json.dumps(light_results, indent=2))
    print("\nMedium Load Test:")
    print(json.dumps(medium_results, indent=2))
    print("\nHeavy Load Test:")
    print(json.dumps(heavy_results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
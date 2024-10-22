cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload


Run Tests:
1. Install required packages:

pip install pytest pytest-asyncio aiohttp

2. Run the test suite:

python test_retail_bot.py

3. Run load tests:

python load_test_retail_bot.py
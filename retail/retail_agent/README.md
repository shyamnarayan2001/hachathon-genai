# Retail Bot: AI-Powered Shoe Store Assistant

A modern, AI-powered retail chatbot that helps customers find and purchase shoes. Built with FastAPI, LangChain, and React, utilizing Groq and OpenAI's language models.

## Features

### Functional Features
- 🤖 Natural language interaction with customers
- 👟 Comprehensive shoe inventory management
- 🔍 Smart product recommendations
- 📊 Real-time stock availability
- 💰 Price comparisons and information
- 🛒 Order processing capability

### Technical Features
- ⚡ Async API with FastAPI
- 🔄 WebSocket support for real-time chat
- 🧠 LangChain for LLM orchestration
- 🔄 Fallback mechanisms between Groq and OpenAI
- 🗄️ SQLite database for data persistence
- 🧪 Comprehensive test suite

## Architecture

```
retail_bot/
├── backend/            # FastAPI backend
│   ├── app/
│   │   ├── main.py    # Main application
│   │   ├── agents.py  # LangChain agents
│   │   ├── db.py      # Database operations
│   │   ├── models.py  # Pydantic models
│   │   └── config.py  # Configuration
│   ├── tests/         # Test suite
│   └── requirements.txt
└── database/          # SQLite database
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- pip
- Virtual environment tool

### Environment Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd retail-agent
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Unix/MacOS
python -m venv venv
source venv/bin/activate
```

3. Create .env file:
```bash
cp .env.example .env
```

4. Update .env with your API keys:
```env
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
```

### Installation

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Initialize the database:
```bash
# The database will be automatically initialized on first run
```

### Running the Application

1. Start the backend server:
```bash
uvicorn app.main:app --reload
```

2. Test the API:
```bash
curl http://localhost:8000/health
```

## Testing

### Running Tests

1. Install test dependencies:
```bash
pip install pytest pytest-asyncio aiohttp
```

2. Run the test suite:
```bash
python test_retail_bot.py
```

3. Run load tests:
```bash
python load_test_retail_bot.py
```

## API Documentation

### Chat Endpoints

1. WebSocket Chat:
```bash
ws://localhost:8000/ws/chat
```

2. REST Chat:
```bash
POST /api/chat
Content-Type: application/json

{
    "content": "What running shoes do you have?"
}
```

### Inventory Endpoints

1. Get All Inventory:
```bash
GET /api/inventory
```

2. Get Filtered Inventory:
```bash
GET /api/inventory?activity=running&size=10
```

## Example Usage

1. Basic Query:
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "What shoes do you have?"}'
```

2. Specific Query:
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "I need running shoes in size 10"}'
```

## Troubleshooting

Common issues and solutions:

1. Database Issues:
   - Delete the existing database file and restart the application
   - Check database permissions

2. API Key Issues:
   - Verify API keys in .env file
   - Check API key permissions

3. Test Failures:
   - Ensure all dependencies are installed
   - Check test database connectivity
   - Verify API is running for integration tests

## Contributing

1. Fork the repository
2. Create your feature branch
3. Add tests for any new functionality
4. Ensure tests pass
5. Create a pull request

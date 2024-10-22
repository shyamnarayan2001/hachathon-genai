#!/bin/bash

BASE_URL="http://localhost:8000"

# 1. Basic Inventory Queries
echo "1. Get all shoes"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "What shoes do you have available?"}'

echo -e "\n\n2. Show specific activity"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "Show me running shoes"}'

echo -e "\n\n3. Size specific query"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "Do you have any shoes in size 10?"}'

# 2. Combined Queries
echo -e "\n\n4. Activity and size combined"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "I need running shoes in size 10"}'

echo -e "\n\n5. Price range query"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "What running shoes do you have under $130?"}'

# 3. Specific Product Queries
echo -e "\n\n6. Ask about specific shoe"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "Tell me more about the Speed Runner Pro"}'

echo -e "\n\n7. Compare products"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "What is the difference between Speed Runner Pro and Marathon Elite?"}'

# 4. Use Case Specific Queries
echo -e "\n\n8. Activity recommendation"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "I need shoes for long-distance running"}'

echo -e "\n\n9. Availability check"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "Which hiking shoes are in stock?"}'

# 5. Conversational Flow
echo -e "\n\n10. Follow-up question"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "Do you have these in different colors?"}'

# 6. Edge Cases
echo -e "\n\n11. Out of range size"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "Do you have any shoes in size 15?"}'

echo -e "\n\n12. Unknown activity"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "I need shoes for basketball"}'

# 7. Complex Queries
echo -e "\n\n13. Multiple requirements"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "I need comfortable shoes for both walking and light hiking in size 10"}'

echo -e "\n\n14. Preference-based query"
curl -X POST "${BASE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "What would you recommend for someone who walks a lot on hard surfaces?"}'
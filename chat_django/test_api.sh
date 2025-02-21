#!/bin/bash

# Base URL
BASE_URL="http://127.0.0.1:8000/"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Testing Chat API${NC}"
echo "------------------------"

# 1. Get Google OAuth URL
echo -e "\n${GREEN}1. Getting Google OAuth URL:${NC}"
curl -X GET "${BASE_URL}/auth/google/login/"

# For testing, we'll create a mock token (this simulates the OAuth flow)
echo -e "\n\n${GREEN}2. Simulating OAuth callback with mock token:${NC}"
MOCK_TOKEN=$(echo -n '{"sub":"123","email":"test@example.com","given_name":"Test","family_name":"User"}' | base64)
RESPONSE=$(curl -X GET "${BASE_URL}/auth/google/callback/?mock_token=${MOCK_TOKEN}")
TOKEN=$(echo $RESPONSE | grep -o '"token":"[^"]*' | grep -o '[^"]*$')

echo -e "\nToken: $TOKEN"

# 3. Create a new chat
echo -e "\n${GREEN}3. Creating new chat:${NC}"
CHAT_RESPONSE=$(curl -X POST "${BASE_URL}/api/chat/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Chat"}')

CHAT_ID=$(echo $CHAT_RESPONSE | grep -o '"chat_id":"[^"]*' | grep -o '[^"]*$')
echo -e "\nChat ID: $CHAT_ID"

# 4. Send a message and get streaming response
echo -e "\n${GREEN}4. Sending message and receiving stream:${NC}"
curl -N -X POST "${BASE_URL}/api/chat/${CHAT_ID}/messages/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"content":"Tell me about Django"}'

echo -e "\n\n${GREEN}Tests completed${NC}"
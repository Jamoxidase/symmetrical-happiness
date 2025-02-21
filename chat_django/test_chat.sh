#!/bin/bash

# Base URL
BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing Chat Flow${NC}"

# 1. Login with existing user
echo -e "\n${GREEN}1. Logging in...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "t444est@example.com",
    "password": "testpass123"
  }')

# Extract token from registration response
TOKEN=$(echo $REGISTER_RESPONSE | jq -r '.access_token')

if [ -z "$TOKEN" ]; then
    echo "Failed to get token. Response was:"
    echo $REGISTER_RESPONSE
    exit 1
fi

echo "Got token: ${TOKEN:0:20}..."

# 2. Create chat and process SSE stream
echo -e "\n${GREEN}2. Creating chat and processing stream...${NC}"
echo "Events:"

# Use curl directly for streaming
curl -N -s -X POST "$BASE_URL/api/chat/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Test Chat",
    "content": "Show me some selenocysteine tRNAs"
  }' | while IFS= read -r line; do
    # Skip empty lines
    [ -z "$line" ] && continue
    
    # Remove "data: " prefix and parse JSON
    if [[ $line == data:* ]]; then
        EVENT_DATA=${line#data: }
        # Pretty print the JSON
        echo $EVENT_DATA | jq '.' || echo "Failed to parse JSON: $EVENT_DATA"
        echo "---"
    fi
done

echo -e "\n${GREEN}Done!${NC}"
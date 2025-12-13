#!/bin/bash

echo "======================================"
echo "Checking Railway Deployment Status"
echo "======================================"
echo ""

read -p "Enter your Railway URL: " RAILWAY_URL

echo ""
echo "Testing root endpoint..."
echo "--------------------------------------"

RESPONSE=$(curl -s "$RAILWAY_URL/")

echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

# Check version
if echo "$RESPONSE" | grep -q "3.1.0"; then
    echo ""
    echo "✅ SUCCESS: New version deployed (3.1.0)"
    echo ""
    echo "Available endpoints:"
    echo "$RESPONSE" | grep -o '"endpoints":\[[^]]*\]' || echo "Couldn't parse endpoints"
elif echo "$RESPONSE" | grep -q "version"; then
    echo ""
    echo "⚠️  WARNING: Old version still deployed"
    CURRENT_VERSION=$(echo "$RESPONSE" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    echo "Current version: $CURRENT_VERSION"
    echo "Expected version: 3.1.0"
    echo ""
    echo "Railway is probably still deploying. Wait 1-2 minutes and try again."
else
    echo ""
    echo "❌ ERROR: Can't connect to Railway or API not responding"
    echo ""
    echo "Possible issues:"
    echo "1. Railway URL is incorrect"
    echo "2. Railway is still deploying"
    echo "3. API crashed during deployment"
    echo ""
    echo "Check Railway logs at: https://railway.app"
fi

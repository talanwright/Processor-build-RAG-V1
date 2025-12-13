#!/bin/bash

# Test Secure Email Feature
# This script tests if your secure email implementation is working

echo "======================================"
echo "Testing Secure Email Implementation"
echo "======================================"
echo ""

# You need to set these variables
read -p "Enter your Railway URL (e.g., https://web-production-abc123.up.railway.app): " RAILWAY_URL
read -p "Enter your API Key: " API_KEY

echo ""
echo "Step 1: Testing /generate-email endpoint..."
echo "--------------------------------------"

RESPONSE=$(curl -s -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_id": "TEST123",
    "borrower_name": "John Smith",
    "template_type": "ready_for_review",
    "monthly_income": 8500,
    "completeness_score": 100
  }' \
  "$RAILWAY_URL/generate-email")

echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

# Extract the secure link
SECURE_LINK=$(echo "$RESPONSE" | grep -o '"secure_link":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SECURE_LINK" ]; then
    echo ""
    echo "❌ ERROR: No secure_link found in response!"
    echo "Check if BASE_URL is set in Railway environment variables"
    exit 1
fi

echo ""
echo "✅ SUCCESS: Email generated with secure link"
echo "Secure Link: $SECURE_LINK"

echo ""
echo "Step 2: Testing secure link access..."
echo "--------------------------------------"

LOAN_RESPONSE=$(curl -s "$SECURE_LINK")

echo "$LOAN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOAN_RESPONSE"

# Check if the response contains loan data
if echo "$LOAN_RESPONSE" | grep -q "loan_id"; then
    echo ""
    echo "✅ SUCCESS: Secure link works!"
    echo ""
    echo "======================================"
    echo "All Tests Passed! ✅"
    echo "======================================"
    echo ""
    echo "Next Steps:"
    echo "1. Set BASE_URL in Railway to: $RAILWAY_URL"
    echo "2. Update your Make.com scenario (see TESTING_SECURE_EMAIL.md)"
    echo "3. Send a test email"
    echo ""
else
    echo ""
    echo "❌ ERROR: Secure link didn't return loan data"
    echo "Check Railway logs for errors"
fi

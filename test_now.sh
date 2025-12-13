#!/bin/bash

# Quick test for secure email
API_KEY="sk-ant-api03-f7DWNLWX-A03nVamVZdBgHZCokUHsZT1HdEXkHiVyL4GjBAP5oR5u8LH5-gNYx5LJCZ4wEUYh-_Ui9y6UBl6lQ-wNLlNAAA"
RAILWAY_URL="https://web-production-0a9f4.up.railway.app"

echo "Testing secure email generation..."
echo ""

curl -X POST "${RAILWAY_URL}/generate-email?loan_id=TEST123&borrower_name=John%20Smith&template_type=ready_for_review&monthly_income=8500&completeness_score=100" \
  -H "X-API-Key: ${API_KEY}" \
  -s | python3 -m json.tool

echo ""
echo "If you see a 'secure_link' above, it worked! Copy that link and paste it in your browser."

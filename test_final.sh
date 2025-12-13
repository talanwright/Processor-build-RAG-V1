#!/bin/bash

API_KEY='ox93A93QBT9ybJLJdo3tkpA5Zdwugr563u2q6dBqwkkPWNuh9ABwafm4oenGVhBC'
RAILWAY_URL='https://web-production-0a9f4.up.railway.app'

echo "Testing secure email generation..."
echo ""

curl -X POST "${RAILWAY_URL}/generate-email?loan_id=TEST123&borrower_name=John%20Smith&template_type=ready_for_review&monthly_income=8500&completeness_score=100" \
  -H "X-API-Key: ${API_KEY}" | python3 -m json.tool

echo ""
echo "========================================"
echo "Look for 'secure_link' in the output above"
echo "========================================"

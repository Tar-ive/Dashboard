#!/bin/bash

# Test script for containerized NSF Solicitation Deconstruction API
# This simulates the Postman collection workflow

set -e

echo "🧪 Testing Containerized NSF Solicitation Deconstruction API"
echo "============================================================"

BASE_URL="http://localhost:8000/api"
PDF_FILE="data/uploads/NSF 24-569_ Mathematical Foundations of Artificial Intelligence (MFAI) _ NSF - National Science Foundation.pdf"

# Check if PDF file exists
if [ ! -f "$PDF_FILE" ]; then
    echo "❌ PDF file not found: $PDF_FILE"
    exit 1
fi

echo "📡 Testing API health..."
HEALTH=$(curl -s "$BASE_URL/../health" | jq -r '.api_status')
if [ "$HEALTH" != "ready" ]; then
    echo "❌ API is not ready. Status: $HEALTH"
    exit 1
fi
echo "✅ API is healthy"

echo ""
echo "📄 Step 1: Upload PDF solicitation..."
RESPONSE=$(curl -s -X POST "$BASE_URL/deconstruct" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@$PDF_FILE")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
STATUS=$(echo "$RESPONSE" | jq -r '.status')

if [ "$JOB_ID" == "null" ] || [ -z "$JOB_ID" ]; then
    echo "❌ Failed to upload PDF. Response: $RESPONSE"
    exit 1
fi

echo "✅ PDF uploaded successfully"
echo "   Job ID: $JOB_ID"
echo "   Initial Status: $STATUS"

echo ""
echo "⏳ Step 2: Polling job status..."
MAX_ATTEMPTS=20
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "   Attempt $ATTEMPT/$MAX_ATTEMPTS..."
    
    STATUS_RESPONSE=$(curl -s "$BASE_URL/jobs/$JOB_ID")
    CURRENT_STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
    PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.progress // 0')
    
    echo "   Status: $CURRENT_STATUS, Progress: $PROGRESS%"
    
    if [ "$CURRENT_STATUS" == "completed" ]; then
        echo "✅ Job completed successfully!"
        break
    elif [ "$CURRENT_STATUS" == "failed" ]; then
        ERROR_MSG=$(echo "$STATUS_RESPONSE" | jq -r '.error_message')
        echo "❌ Job failed: $ERROR_MSG"
        exit 1
    fi
    
    sleep 3
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo "❌ Job did not complete within expected time"
    exit 1
fi

echo ""
echo "🔍 Step 3: Validating structured result..."
FINAL_RESPONSE=$(curl -s "$BASE_URL/jobs/$JOB_ID")
RESULT=$(echo "$FINAL_RESPONSE" | jq '.result')

# Validate key fields
AWARD_TITLE=$(echo "$RESULT" | jq -r '.award_title // "null"')
FUNDING=$(echo "$RESULT" | jq -r '.funding_ceiling // "null"')
DURATION=$(echo "$RESULT" | jq -r '.project_duration_months // "null"')
PI_RULES_COUNT=$(echo "$RESULT" | jq '.pi_eligibility_rules | length // 0')
SKILLS_COUNT=$(echo "$RESULT" | jq '.required_scientific_skills | length // 0')

echo "📊 Extracted Data:"
echo "   Award Title: $AWARD_TITLE"
echo "   Funding Ceiling: \$$FUNDING"
echo "   Duration: $DURATION months"
echo "   PI Eligibility Rules: $PI_RULES_COUNT rules"
echo "   Required Skills: $SKILLS_COUNT skills"

# Validation checks
VALIDATION_PASSED=true

if [ "$AWARD_TITLE" == "null" ] || [ -z "$AWARD_TITLE" ]; then
    echo "❌ Award title not extracted"
    VALIDATION_PASSED=false
fi

if [ "$FUNDING" == "null" ] || [ "$FUNDING" == "0" ]; then
    echo "❌ Funding ceiling not extracted"
    VALIDATION_PASSED=false
fi

if [ "$DURATION" == "null" ] || [ "$DURATION" == "0" ]; then
    echo "❌ Project duration not extracted"
    VALIDATION_PASSED=false
fi

if [ "$PI_RULES_COUNT" == "0" ]; then
    echo "❌ PI eligibility rules not extracted"
    VALIDATION_PASSED=false
fi

if [ "$VALIDATION_PASSED" == "true" ]; then
    echo ""
    echo "🎉 All validations passed! Containerized API is working perfectly."
    echo ""
    echo "📋 Summary:"
    echo "   ✅ PDF Upload: Working"
    echo "   ✅ Background Processing: Working"
    echo "   ✅ Status Polling: Working"
    echo "   ✅ Data Extraction: Working"
    echo "   ✅ LLM Integration: Working"
    echo "   ✅ Redis Storage: Working"
    echo ""
    echo "🔧 Ready for Postman testing!"
else
    echo ""
    echo "❌ Some validations failed. Check the API implementation."
    exit 1
fi
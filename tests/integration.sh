#!/usr/bin/env bash
set -euo pipefail

TIMEOUT=${INTEGRATION_TIMEOUT:-120}
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

echo "=== Integration Test ==="
echo "Frontend URL: $FRONTEND_URL"
echo "Timeout: ${TIMEOUT}s"

echo "Submitting job..."
response=$(curl -s -X POST "$FRONTEND_URL/submit")
echo "Response: $response"

job_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Job ID: $job_id"

echo "Polling for job completion (timeout: ${TIMEOUT}s)..."
start_time=$(date +%s)
while true; do
    elapsed=$(( $(date +%s) - start_time ))
    if [ "$elapsed" -ge "$TIMEOUT" ]; then
        echo "TIMEOUT: Job did not complete within ${TIMEOUT}s"
        exit 1
    fi

    status_response=$(curl -s "$FRONTEND_URL/status/$job_id")
    echo "Status response: $status_response"
    status=$(echo "$status_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
    echo "Status: $status"

    if [ "$status" = "completed" ]; then
        echo "PASS: Job completed successfully!"
        exit 0
    fi

    sleep 2
done

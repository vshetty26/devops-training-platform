#!/bin/bash
# validate.sh - Checks if Nginx is returning successful HTTP responses

set -e

# Check if Nginx is running and responding with 200 OK
# We'll test on port 8080 where our broken config was listening

response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 2>/dev/null || echo "000")

if [ "$response_code" = "200" ]; then
    echo "✓ Success! Nginx is returning HTTP 200 OK"
    exit 0
else
    echo "✗ Validation failed: Nginx returned HTTP $response_code"
    echo ""
    echo "Hint: Check the Nginx configuration files and error logs"
    echo "      - Look at /tmp/broken_backend.conf for the misconfiguration"
    echo "      - Check if the upstream backend at 127.0.0.1:9999 is reachable"
    echo "      - Consider either fixing the upstream or serving content directly"
    echo "      - Use 'curl -v http://localhost:8080' to see detailed response"
    exit 1
fi

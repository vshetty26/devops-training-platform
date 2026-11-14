#!/bin/bash
# validate.sh - Checks if the application runs stably without exiting

set -e

echo "Validating container stability..."

# Check if the startup script exists and is executable
if [ ! -x /app/start.sh ]; then
    echo "✗ Validation failed: /app/start.sh not found or not executable"
    exit 1
fi

# Try to start the application in the background and monitor it
/app/start.sh &
APP_PID=$!

echo "Started application with PID $APP_PID"
echo "Monitoring stability for 5 seconds..."

# Wait a few seconds to see if the process stays alive
sleep 5

# Check if the process is still running
if ! kill -0 $APP_PID 2>/dev/null; then
    echo "✗ Validation failed: Application exited within 5 seconds"
    echo ""
    echo "Hint: The startup script checks for /app/config.json"
    echo "      - Create the missing configuration file, OR"
    echo "      - Remove/fix the check that causes the script to exit"
    echo "      - Make sure the script can start python3 /app/app.py successfully"
    exit 1
fi

# Check if the application is serving HTTP on port 8080
sleep 2
response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 2>/dev/null || echo "000")

# Kill the background process
kill $APP_PID 2>/dev/null || true

if [ "$response_code" = "200" ]; then
    echo "✓ Success! Application is running stably and serving HTTP on port 8080"
    exit 0
else
    echo "✗ Validation failed: Application is running but not responding on port 8080"
    echo ""
    echo "Hint: Make sure the application starts correctly with: python3 /app/app.py"
    echo "      Test manually with: curl http://localhost:8080"
    exit 1
fi

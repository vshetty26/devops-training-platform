#!/bin/bash
# setup.sh - Injects a container restart loop by creating a broken service script

set -e

# Create a simple Python web application
cat > /app/app.py << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver

PORT = 8080

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server running on port {PORT}")
    httpd.serve_forever()
EOF

chmod +x /app/app.py

# Create a BROKEN startup script that causes immediate exit
# This simulates a common Docker restart loop scenario
cat > /app/start.sh << 'EOF'
#!/bin/bash
# Broken startup script - has a fatal error that causes immediate exit

# This line references a non-existent configuration file and exits if not found
# This is a common pattern in init scripts
if [ ! -f /app/config.json ]; then
    echo "ERROR: Configuration file /app/config.json not found!"
    exit 1
fi

# This would start the application (but never reached due to above exit)
python3 /app/app.py
EOF

chmod +x /app/start.sh

# Create a systemd-style service file that would use this broken script
cat > /tmp/app.service << 'EOF'
[Unit]
Description=Simple Web Application
After=network.target

[Service]
Type=simple
User=challenger
WorkingDirectory=/app
ExecStart=/app/start.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "===== CONTAINER RESTART LOOP CHALLENGE ====="
echo ""
echo "A broken startup script has been created at /app/start.sh"
echo "The script checks for /app/config.json and exits if it doesn't exist"
echo ""
echo "If this were a Docker container with CMD ['/app/start.sh'], it would:"
echo "1. Start"
echo "2. Check for /app/config.json"
echo "3. Exit with error code 1 (file not found)"
echo "4. Docker restarts it (because of restart policy)"
echo "5. Repeat endlessly (restart loop)"
echo ""
echo "Your task: Fix the startup script so the application runs continuously"
echo "The app should serve HTTP on port 8080"
echo ""


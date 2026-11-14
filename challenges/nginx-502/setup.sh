#!/bin/bash
# setup.sh - Injects broken Nginx upstream configuration to cause 502 errors

set -e

# Create a broken Nginx configuration with unreachable upstream
cat > /tmp/broken_backend.conf << 'EOF'
upstream backend {
    # This upstream points to a non-existent backend server
    server 127.0.0.1:9999;
}

server {
    listen 8080;
    server_name localhost;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Note: In a real scenario with proper permissions, this would copy to /etc/nginx/sites-available/
# and create a symlink in sites-enabled. For this challenge, the configuration will need
# to be fixed by the user who will need to either:
# 1. Fix the upstream to point to a valid backend, OR
# 2. Change the configuration to serve static content directly

echo "Broken Nginx configuration created at /tmp/broken_backend.conf"
echo "The configuration sets up an unreachable upstream backend at 127.0.0.1:9999"
echo "This will cause Nginx to return 502 Bad Gateway errors when proxying requests"

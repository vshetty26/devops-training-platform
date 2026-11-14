#!/bin/bash
# setup.sh - Creates a broken Kubernetes pod manifest with CrashLoopBackOff issues

set -e

# Create a broken pod manifest with multiple common crash loop causes
cat > /tmp/broken-pod.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: webapp
  labels:
    app: webapp
spec:
  containers:
  - name: webapp
    image: nginx:latest
    # ISSUE 1: Wrong command that doesn't exist in the container
    command: ["/usr/bin/nonexistent-command"]
    args: ["--start"]
    ports:
    - containerPort: 80
    env:
    # ISSUE 2: Missing required environment variable value
    - name: DATABASE_URL
      # valueFrom should have a valid source, or use value directly
      valueFrom:
        secretKeyRef:
          name: db-secret-that-does-not-exist
          key: url
    - name: APP_MODE
      value: "production"
    livenessProbe:
      httpGet:
        path: /healthz
        # ISSUE 3: Wrong port - container runs on 80, but probe checks 8080
        port: 8080
      initialDelaySeconds: 3
      periodSeconds: 3
      failureThreshold: 1
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
EOF

echo "Broken Kubernetes pod manifest created at /tmp/broken-pod.yaml"
echo ""
echo "This pod has multiple issues that will cause CrashLoopBackOff:"
echo "1. Command references a non-existent binary"
echo "2. Environment variable references a non-existent secret"
echo "3. Liveness probe checks the wrong port"
echo ""
echo "Your task: Fix the manifest so the pod can run successfully"

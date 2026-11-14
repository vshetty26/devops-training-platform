#!/bin/bash
# validate.sh - Validates that the pod manifest is fixed and can run successfully

set -e

MANIFEST="/tmp/broken-pod.yaml"

# Check if the manifest file exists
if [ ! -f "$MANIFEST" ]; then
    echo "✗ Validation failed: Pod manifest not found at $MANIFEST"
    exit 1
fi

# Basic YAML validation - check if it has required Kubernetes fields
if ! grep -q "apiVersion:" "$MANIFEST" || ! grep -q "kind: Pod" "$MANIFEST"; then
    echo "✗ Validation failed: Invalid Kubernetes pod manifest structure"
    echo ""
    echo "The manifest must have 'apiVersion' and 'kind: Pod' fields"
    exit 1
fi

# Check that problematic command has been removed or fixed
if grep -q "/usr/bin/nonexistent-command" "$MANIFEST"; then
    echo "✗ Validation failed: Pod still references non-existent command"
    echo ""
    echo "Hint: Remove the invalid 'command' field or use a valid command"
    echo "      For nginx, you can remove the command/args and use the default"
    exit 1
fi

# Check that secret reference has been removed or fixed
if grep -q "db-secret-that-does-not-exist" "$MANIFEST"; then
    echo "✗ Validation failed: Pod still references non-existent secret"
    echo ""
    echo "Hint: Either remove the DATABASE_URL env var if not needed,"
    echo "      or use 'value' instead of 'valueFrom' for a direct value"
    exit 1
fi

# Check that liveness probe port has been fixed or removed
if grep -A5 "livenessProbe:" "$MANIFEST" | grep -q "port: 8080"; then
    echo "✗ Validation failed: Liveness probe still checks wrong port (8080)"
    echo ""
    echo "Hint: The nginx container runs on port 80, not 8080"
    echo "      Either change the probe port to 80 or remove the liveness probe"
    exit 1
fi

# All checks passed
echo "✓ Success! Pod manifest is fixed and valid"
echo ""
echo "The pod configuration no longer has CrashLoopBackOff issues:"
echo "  • Command/args are valid or removed"
echo "  • Environment variables are properly configured"
echo "  • Liveness probe targets the correct port"
echo ""
echo "In a real cluster, this pod would now start successfully!"
exit 0

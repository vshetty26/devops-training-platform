#!/bin/bash
# validate.sh - Validates GitHub Actions workflow YAML syntax and structure

set -e

WORKFLOW_FILE="/home/challenger/.github/workflows/ci.yml"

# Check if workflow file exists
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "✗ Validation failed: Workflow file not found at $WORKFLOW_FILE"
    echo ""
    echo "Hint: The workflow file should be located at .github/workflows/ci.yml"
    exit 1
fi

# Check YAML syntax with yamllint
echo "Checking YAML syntax..."
if ! yamllint -d "{extends: default, rules: {line-length: {max: 120}, indentation: {spaces: 2}}}" "$WORKFLOW_FILE" 2>/dev/null; then
    echo ""
    echo "✗ Validation failed: YAML syntax errors detected"
    echo ""
    echo "Hint: Run 'yamllint ~/.github/workflows/ci.yml' to see detailed syntax errors"
    echo "      Common issues include:"
    echo "      - Incorrect indentation (GitHub Actions uses 2 spaces)"
    echo "      - Missing colons after keys"
    echo "      - Inconsistent spacing"
    exit 1
fi

# Basic validation for GitHub Actions specific structure
echo "Checking GitHub Actions structure..."

# Check for required top-level keys
if ! grep -q "^name:" "$WORKFLOW_FILE"; then
    echo "✗ Validation failed: Missing 'name' key"
    echo ""
    echo "Hint: GitHub Actions workflows must have a 'name' field at the top level"
    exit 1
fi

if ! grep -q "^on:" "$WORKFLOW_FILE"; then
    echo "✗ Validation failed: Missing 'on' key"
    echo ""
    echo "Hint: GitHub Actions workflows must have an 'on' field defining triggers"
    exit 1
fi

if ! grep -q "^jobs:" "$WORKFLOW_FILE"; then
    echo "✗ Validation failed: Missing 'jobs' key"
    echo ""
    echo "Hint: GitHub Actions workflows must have a 'jobs' field defining job configurations"
    exit 1
fi

# Check for invalid keys like 'runs' instead of 'run'
if grep -q "runs:" "$WORKFLOW_FILE"; then
    echo "✗ Validation failed: Invalid key 'runs' found in workflow"
    echo ""
    echo "Hint: The correct key for executing commands is 'run', not 'runs'"
    echo "      Check your step definitions for this typo"
    exit 1
fi

# Check that all steps have proper structure (name + either uses/run)
# This is a simple heuristic check
step_count=$(grep -c "- name:" "$WORKFLOW_FILE" || echo "0")
if [ "$step_count" -eq 0 ]; then
    echo "✗ Validation failed: No properly formatted steps found"
    echo ""
    echo "Hint: Each step should start with '- name:' followed by 'uses:' or 'run:'"
    exit 1
fi

# Verify indentation is consistent (2 spaces per level for GitHub Actions)
if grep -E "^   [^ ]" "$WORKFLOW_FILE" | grep -q "- name:"; then
    echo "✗ Validation failed: Inconsistent indentation detected"
    echo ""
    echo "Hint: GitHub Actions YAML should use 2 spaces per indentation level"
    echo "      Check for lines with 3 or odd numbers of leading spaces"
    exit 1
fi

# All checks passed
echo ""
echo "✓ Success! GitHub Actions workflow YAML is valid"
echo ""
echo "  ✓ YAML syntax is correct"
echo "  ✓ Required top-level keys are present (name, on, jobs)"
echo "  ✓ No invalid keys detected"
echo "  ✓ Indentation is consistent"
echo ""
echo "The workflow is ready to be committed to your repository!"

exit 0

#!/bin/bash
# setup.sh - Injects broken GitHub Actions workflow YAML with multiple issues

set -e

# Create .github/workflows directory if it doesn't exist
mkdir -p /home/challenger/.github/workflows

# Create a broken GitHub Actions workflow with common YAML and configuration errors
cat > /home/challenger/.github/workflows/ci.yml << 'EOF'
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    # Broken indentation - this line is not properly aligned
   - name: Install dependencies
      run: npm install
    
    - name: Run linter
      run: npm run lint
    
    # Invalid key name - 'runs' should be 'run'
    - name: Run tests
      runs: npm test
    
    - name: Build project
      run: npm run build

  deploy:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      # Missing 'run' key - command is dangling
      echo "Deploying to production..."
    
    # Incorrect indentation for this entire step block
  - name: Notify team
    run: |
      echo "Deployment complete"
      echo "Build number: ${{ github.run_number }}"
EOF

echo "Broken GitHub Actions workflow created at /home/challenger/.github/workflows/ci.yml"
echo ""
echo "The workflow contains multiple issues:"
echo "  1. Indentation error in the 'Install dependencies' step"
echo "  2. Invalid key 'runs' instead of 'run' in the test step"
echo "  3. Missing 'run' key in the deployment step"
echo "  4. Incorrect indentation in the 'Notify team' step"
echo ""
echo "Fix all YAML syntax and structure issues to pass validation!"

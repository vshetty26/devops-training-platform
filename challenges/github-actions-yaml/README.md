# GitHub Actions YAML Challenge

## Challenge Overview

This challenge presents users with a broken GitHub Actions CI/CD workflow file that contains multiple YAML syntax errors and configuration issues. Users must identify and fix all errors to pass validation.

## Challenge Files

- **Dockerfile**: Ubuntu 22.04 image with yamllint, vim, nano, and git installed
- **setup.sh**: Creates broken workflow file at `~/.github/workflows/ci.yml`
- **validate.sh**: Validates YAML syntax and GitHub Actions structure
- **metadata.json**: Challenge metadata with hints

## Injected Errors

The setup script creates a workflow with the following issues:

### 1. Indentation Error (Line 20)
```yaml
# BROKEN - 3 spaces instead of 4
   - name: Install dependencies
      run: npm install
```

**Fix**: Use proper 4-space indentation
```yaml
    - name: Install dependencies
      run: npm install
```

### 2. Invalid Key Name (Line 27)
```yaml
# BROKEN - 'runs' is not a valid key
    - name: Run tests
      runs: npm test
```

**Fix**: Use 'run' instead of 'runs'
```yaml
    - name: Run tests
      run: npm test
```

### 3. Missing Action Key (Line 39)
```yaml
# BROKEN - command without 'run:' key
    - name: Deploy to production
      echo "Deploying to production..."
```

**Fix**: Add 'run:' key
```yaml
    - name: Deploy to production
      run: echo "Deploying to production..."
```

### 4. Incorrect Step Indentation (Line 42-43)
```yaml
# BROKEN - step is indented at job level instead of under steps
  - name: Notify team
    run: |
      echo "Deployment complete"
```

**Fix**: Proper indentation under steps array
```yaml
    - name: Notify team
      run: |
        echo "Deployment complete"
```

## Validation Criteria

The validate.sh script checks:

1. ✓ YAML syntax correctness (using yamllint)
2. ✓ Required top-level keys present (`name`, `on`, `jobs`)
3. ✓ No invalid keys (e.g., 'runs' instead of 'run')
4. ✓ Proper step structure (each step has name + action)
5. ✓ Consistent indentation (2 spaces per level)

## Learning Objectives

- Understanding GitHub Actions workflow YAML structure
- Identifying and fixing YAML indentation issues
- Recognizing valid vs invalid GitHub Actions keys
- Using yamllint for YAML validation
- Understanding proper GitHub Actions job and step structure

## Difficulty

**Easy** - Suitable for users learning YAML syntax and GitHub Actions basics

## Tools Available

- `yamllint` - YAML syntax validator
- `vim` / `nano` - Text editors
- `cat` / `less` - File viewers

## Expected Completion Time

5-10 minutes for users familiar with YAML, 15-20 minutes for beginners

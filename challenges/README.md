# Challenge Definitions

This directory contains challenge definitions for DevOps Arena.

## Challenge Structure

Each challenge is a subdirectory containing:

```
challenge-name/
├── Dockerfile         # Base container image
├── setup.sh          # Script to inject the fault
├── validate.sh       # Script to check if issue is resolved
└── metadata.json     # Challenge metadata
```

### metadata.json Format

```json
{
  "id": "challenge-id",
  "title": "Challenge Title",
  "difficulty": "easy|medium|hard",
  "brief": "Problem description presented to users",
  "hints": [
    "Hint 1",
    "Hint 2"
  ]
}
```

### setup.sh

- Executed after container creation
- Injects the specific fault
- Must be executable (`chmod +x`)

### validate.sh

- Checks if the issue is resolved
- Exit 0 for success
- Exit non-zero for failure
- Print hints to stdout on failure

## Example Challenge

See the starter challenges that will be implemented:
- `docker-restart-loop` - Debug a container restart loop
- `disk-full` - Resolve server disk full issues
- `nginx-502` - Fix Nginx 502 errors
- `github-actions-yaml` - Correct broken workflow YAML
- `k8s-crashloop` - Debug Kubernetes CrashLoopBackOff

Requirements: 7.1-7.6, 8.1-8.5

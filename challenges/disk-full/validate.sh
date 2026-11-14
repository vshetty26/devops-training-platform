#!/bin/bash
# validate.sh - Checks if sufficient disk space has been freed

set -e

echo "Validating disk space cleanup..."

# Calculate total size of dummy files that should be removed
# We check if at least 200MB has been freed (out of the ~255MB created)

total_remaining=0

# Check /var/log/oldlogs/
if [ -d /var/log/oldlogs ]; then
    oldlogs_size=$(du -sb /var/log/oldlogs 2>/dev/null | awk '{print $1}')
    total_remaining=$((total_remaining + oldlogs_size))
fi

# Check /tmp/cache/
if [ -d /tmp/cache ]; then
    cache_size=$(du -sb /tmp/cache 2>/dev/null | awk '{print $1}')
    total_remaining=$((total_remaining + cache_size))
fi

# Check /home/challenger/.backup/
if [ -d /home/challenger/.backup ]; then
    backup_size=$(du -sb /home/challenger/.backup 2>/dev/null | awk '{print $1}')
    total_remaining=$((total_remaining + backup_size))
fi

# Convert to MB for easier reading
total_remaining_mb=$((total_remaining / 1048576))

# Success if less than 50MB remains in these directories (meaning 200+ MB was freed)
if [ $total_remaining_mb -lt 50 ]; then
    echo "✓ Success! Sufficient disk space has been freed"
    echo "  Remaining space in monitored directories: ${total_remaining_mb}MB"
    echo "  You successfully identified and removed the large unnecessary files!"
    exit 0
else
    echo "✗ Validation failed: Still too much disk usage"
    echo "  Current usage in monitored directories: ${total_remaining_mb}MB"
    echo "  You need to free up more space (target: < 50MB remaining)"
    echo ""
    echo "Hints for finding and removing large files:"
    echo "  1. Use 'du -sh /*' to see disk usage by top-level directories"
    echo "  2. Use 'du -sh /var/log/oldlogs /tmp/cache ~/.backup' to check specific locations"
    echo "  3. Use 'du -ah <directory> | sort -rh | head -20' to find the largest files"
    echo "  4. Use 'find <directory> -type f -size +10M' to find files larger than 10MB"
    echo "  5. Remove files with 'rm <filename>' after identifying unnecessary ones"
    echo "  6. Look for old log files, cache files, and backup files"
    exit 1
fi

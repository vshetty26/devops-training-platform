#!/bin/bash
# setup.sh - Fills the disk with dummy data to simulate a disk full scenario

set -e

echo "Setting up disk-full challenge..."

# Create large dummy files in various locations to simulate a full disk
# Using dd to create files filled with zeros

# Simulate old log files that have grown too large
echo "Creating old log files in /var/log/oldlogs..."
dd if=/dev/zero of=/var/log/oldlogs/application.log.old bs=1M count=50 2>/dev/null
dd if=/dev/zero of=/var/log/oldlogs/system.log.1 bs=1M count=40 2>/dev/null
dd if=/dev/zero of=/var/log/oldlogs/debug.log.old bs=1M count=30 2>/dev/null

# Simulate cache files that weren't cleaned up
echo "Creating cache files in /tmp/cache..."
dd if=/dev/zero of=/tmp/cache/package_cache.tar bs=1M count=35 2>/dev/null
dd if=/dev/zero of=/tmp/cache/build_artifacts.tmp bs=1M count=25 2>/dev/null

# Simulate backup files in home directory
echo "Creating old backup files in home directory..."
dd if=/dev/zero of=/home/challenger/.backup/database_backup_old.sql bs=1M count=45 2>/dev/null
dd if=/dev/zero of=/home/challenger/.backup/files_backup.tar.gz bs=1M count=30 2>/dev/null

echo ""
echo "Disk full scenario created successfully!"
echo "Total dummy data created: ~255MB across multiple directories"
echo ""
echo "Locations of large files:"
echo "  - /var/log/oldlogs/ (old log files)"
echo "  - /tmp/cache/ (temporary cache files)"
echo "  - /home/challenger/.backup/ (old backup files)"
echo ""
echo "Your task: Free up disk space by identifying and removing unnecessary large files"
echo "Hint: Use commands like 'du', 'df', 'find', and 'ls' to locate large files"

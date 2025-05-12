#!/bin/bash
# Script to configure current repository for WSL compatibility

# Apply settings only to this repository
git config core.autocrlf input
git config core.eol lf
git config core.fileMode false

# Ask for confirmation before running git reset --hard
echo "WARNING: This will discard all uncommitted changes!"
read -p "Are you sure you want to continue? (y/n): " confirm

if [[ "$confirm" == [yY] || "$confirm" == [yY][eE][sS] ]]; then
    git reset --hard
    echo "Repository reset completed."
else
    echo "Reset operation cancelled."
fi

echo "Repository configured for WSL compatibility"

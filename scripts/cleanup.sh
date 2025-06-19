#!/bin/bash

# Quick cleanup script

echo "🧹 Running project cleanup..."

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="\${PYTHONPATH}:\$(pwd)/src"

# Ask for confirmation
read -p "Are you sure you want to clean up all resources? (yes/no): " confirm

if [ "\$confirm" = "yes" ]; then
    python scripts/cleanup.py --confirm
else
    echo "Cleanup cancelled"
fi
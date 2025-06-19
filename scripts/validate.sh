#!/bin/bash

# Quick validation script

echo "🔍 Running project validation..."

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="\${PYTHONPATH}:\$(pwd)/src"

# Run validation
python src/utils/validation.py

if [ \$? -eq 0 ]; then
    echo "✅ Validation passed!"
else
    echo "❌ Validation failed!"
    exit 1
fi
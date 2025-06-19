#!/bin/bash
cd /workspaces
# Base project directory
PROJECT_DIR="mlops-ecommerce-recommendation-system-aws"

# Create directories
mkdir -p $PROJECT_DIR/src/data_preparation
mkdir -p $PROJECT_DIR/src/config
mkdir -p $PROJECT_DIR/src/utils
mkdir -p $PROJECT_DIR/data/raw
mkdir -p $PROJECT_DIR/data/processed
mkdir -p $PROJECT_DIR/data/sample
mkdir -p $PROJECT_DIR/notebooks

# Create Python module files
touch $PROJECT_DIR/src/data_preparation/__init__.py
touch $PROJECT_DIR/src/data_preparation/data_ingestion.py
touch $PROJECT_DIR/src/data_preparation/data_transformation.py
touch $PROJECT_DIR/src/data_preparation/feature_engineering.py
touch $PROJECT_DIR/src/data_preparation/data_validation.py

touch $PROJECT_DIR/src/config/__init__.py
touch $PROJECT_DIR/src/config/aws_config.py

touch $PROJECT_DIR/src/utils/__init__.py
touch $PROJECT_DIR/src/utils/helpers.py

# Create notebook and config files
touch $PROJECT_DIR/notebooks/data_exploration.ipynb
touch $PROJECT_DIR/requirements.txt
touch $PROJECT_DIR/setup.py

echo "✅ Project structure for Domain 1: Data Preparation created successfully in '$PROJECT_DIR'"



@btholath ➜ /workspaces $ cd mlops-ecommerce-recommendation-system-aws/
@btholath ➜ /workspaces/mlops-ecommerce-recommendation-system-aws (main) $ python -m venv .venv
@btholath ➜ /workspaces/mlops-ecommerce-recommendation-system-aws (main) $ source .venv/bin/activate
(.venv) @btholath ➜ /workspaces/mlops-ecommerce-recommendation-system-aws (main) $ pip install -r requirements.txt 


Usage Examples:
Run validation:

# Full validation
python src/utils/validation.py

# Or use the script
chmod +x scripts/validate.sh
./scripts/validate.sh
Run cleanup:

# Dry run first (recommended)
python scripts/cleanup.py --dry-run

# Full cleanup
python scripts/cleanup.py

# Cleanup specific resources
python scripts/cleanup.py --s3-only
python scripts/cleanup.py --glue-only --dry-run

# Use the script
chmod +x scripts/cleanup.sh
./scripts/cleanup.sh
These scripts provide comprehensive validation and cleanup capabilities, ensuring you can:

Validate all project components and AWS resources
Monitor costs and performance
Clean up resources safely to avoid charges
Generate reports for audit and troubleshooting

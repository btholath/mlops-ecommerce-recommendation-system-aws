#!/bin/bash

# AWS ML Project Setup Script

echo "🚀 Setting up AWS ML Project..."

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p src/{data_preparation,config,utils}
mkdir -p data/{raw,processed,sample}
mkdir -p notebooks
mkdir -p scripts

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set up AWS credentials check
echo "🔑 Checking AWS credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    echo "✅ AWS credentials configured"
else
    echo "❌ AWS credentials not configured"
    echo "Please run: aws configure"
    exit 1
fi

# Create environment file template
echo "📄 Creating environment template..."
cat > .env.example << EOF
# AWS Configuration
AWS_REGION=us-east-1
ML_DATA_BUCKET=your-ml-data-bucket-name
GLUE_DATABASE=ecommerce_ml_db
SAGEMAKER_ROLE=arn:aws:iam::ACCOUNT:role/SageMakerExecutionRole

# Project Configuration
PROJECT_NAME=ecommerce-ml-project
ENVIRONMENT=development
EOF

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and update with your AWS settings"
echo "2. Run: python src/data_preparation/data_ingestion.py"
echo "3. Run: python src/utils/validation.py"
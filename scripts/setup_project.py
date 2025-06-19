#!/usr/bin/env python3
"""
Project Setup Helper
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"📋 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    print("🔧 Setting up AWS ML Project...")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not in a virtual environment")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled")
            return False
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        return False
    
    # Check AWS CLI
    if not run_command("aws --version", "Checking AWS CLI"):
        print("Please install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        return False
    
    # Check AWS credentials
    if not run_command("aws sts get-caller-identity", "Checking AWS credentials"):
        print("Please configure AWS credentials: aws configure")
        return False
    
    # Create .env file if it doesn't exist
    env_file = Path('.env')
    if not env_file.exists():
        print("📄 Creating .env file template...")
        with open(env_file, 'w') as f:
            f.write("""# AWS Configuration
AWS_REGION=us-east-1
ML_DATA_BUCKET=your-unique-ml-data-bucket-name
GLUE_DATABASE=ecommerce_ml_db

# Replace YOUR_ACCOUNT_ID with your actual AWS account ID
SAGEMAKER_ROLE=arn:aws:iam::YOUR_ACCOUNT_ID:role/SageMakerExecutionRole

# Project Configuration
PROJECT_NAME=ecommerce-ml-project
ENVIRONMENT=development
""")
        print("✅ Created .env file template")
        print("⚠️  Please update .env file with your actual AWS configuration")
        return False
    
    print("✅ Project setup completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
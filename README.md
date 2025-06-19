# mlops-ecommerce-recommendation-system-aws
End-to-end MLOps project on AWS to build a real-world e-commerce recommendation system. Covers all four domains of the AWS Certified Machine Learning Engineer – Associate exam: data preparation, model development, deployment &amp; orchestration, and ML solution monitoring.


This project implements a scalable, production-grade **e-commerce product recommendation system** using AWS Machine Learning services. It is designed to align with the four competency domains of the **AWS Certified Machine Learning Engineer – Associate (MLA-C01)** exam:

- 🧼 **Domain 1: Data Preparation for ML (28%)**  
  Ingest and preprocess purchase, clickstream, and product metadata using SageMaker Processing and AWS Glue.

- 🧠 **Domain 2: ML Model Development (26%)**  
  Train collaborative filtering and deep learning models using SageMaker built-in algorithms and custom XGBoost/PyTorch scripts.

- 🚀 **Domain 3: Deployment and Orchestration (22%)**  
  Deploy models with SageMaker endpoints, orchestrate workflows using SageMaker Pipelines and Step Functions.

- 🔍 **Domain 4: Monitoring, Maintenance, and Security (24%)**  
  Monitor model drift and bias with SageMaker Model Monitor, secure infrastructure with IAM and encryption, and automate retraining.

This project runs from **VS Code** using the **AWS SDK (Boto3)**, and is deployable in the AWS cloud using real-world MLOps best practices.

---
How to Run the Data Preparation Scripts
Here's a step-by-step guide to set up and run the data preparation scripts for the AWS ML project.

1. Initial Setup
Step 1: Clone/Create Project Structure
# Create project directory
mkdir ecommerce-ml-project
cd ecommerce-ml-project

# Create the directory structure
mkdir -p src/{data_preparation,config,utils}
mkdir -p data/{raw,processed,sample}
mkdir -p notebooks
mkdir -p scripts
Step 2: Create Requirements File
Create requirements.txt:

boto3==1.28.36
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
sagemaker==2.175.0
awswrangler==3.4.0
pyarrow==12.0.1
matplotlib==3.7.2
seaborn==0.12.2
jupyter==1.0.0
python-dotenv==1.0.0
Step 3: Set up Python Environment
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
2. AWS Configuration
Step 1: Configure AWS Credentials
# Option 1: Using AWS CLI
aws configure

# Option 2: Set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
Step 2: Create S3 Bucket
# Create S3 bucket (replace with unique name)
aws s3 mb s3://your-unique-ml-data-bucket-name

# Verify bucket creation
aws s3 ls | grep your-unique-ml-data-bucket-name
Step 3: Create Environment Configuration
Create .env file in project root:

# AWS Configuration
AWS_REGION=us-east-1
ML_DATA_BUCKET=your-unique-ml-data-bucket-name
GLUE_DATABASE=ecommerce_ml_db
SAGEMAKER_ROLE=arn:aws:iam::YOUR_ACCOUNT_ID:role/SageMakerExecutionRole

# Project Configuration
PROJECT_NAME=ecommerce-ml-project
ENVIRONMENT=development
3. Update AWS Config to Use Environment Variables
Update src/config/aws_config.py to load from environment:

import boto3
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AWSConfig:
    """AWS Configuration and service clients"""
    
    def __init__(self, region_name: str = None):
        self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-1')
        self.session = boto3.Session(region_name=self.region_name)
        
        # Initialize AWS service clients
        self.s3_client = self.session.client('s3')
        self.glue_client = self.session.client('glue')
        self.sagemaker_client = self.session.client('sagemaker')
        self.athena_client = self.session.client('athena')
        
        # Configuration from environment
        self.s3_bucket = os.getenv('ML_DATA_BUCKET')
        self.glue_database = os.getenv('GLUE_DATABASE', 'ecommerce_ml_db')
        self.sagemaker_role = os.getenv('SAGEMAKER_ROLE')
        
        if not self.s3_bucket:
            raise ValueError("ML_DATA_BUCKET environment variable is required")
        
    def get_s3_path(self, key: str) -> str:
        return f's3://{self.s3_bucket}/{key}'
    
    def validate_setup(self) -> Dict[str, bool]:
        """Validate AWS resources are accessible"""
        validation = {}
        
        try:
            # Check S3 bucket access
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            validation['s3_access'] = True
            print(f"✅ S3 bucket {self.s3_bucket} is accessible")
        except Exception as e:
            print(f"❌ S3 bucket access failed: {e}")
            validation['s3_access'] = False
            
        try:
            # Check if we can list Glue databases
            self.glue_client.get_databases()
            validation['glue_access'] = True
            print("✅ AWS Glue is accessible")
        except Exception as e:
            print(f"❌ Glue access failed: {e}")
            validation['glue_access'] = False
            
        return validation
4. Create a Simple Runner Script
Create run_data_preparation.py in the project root:

#!/usr/bin/env python3
"""
Data Preparation Runner Script
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def main():
    print("🚀 Starting AWS ML Data Preparation...")
    
    try:
        # Import after adding to path
        from config.aws_config import AWSConfig
        from data_preparation.data_ingestion import DataIngestion
        
        # Initialize AWS configuration
        print("🔧 Initializing AWS configuration...")
        aws_config = AWSConfig()
        
        # Validate setup
        print("🔍 Validating AWS setup...")
        validation_results = aws_config.validate_setup()
        
        if not validation_results.get('s3_access', False):
            print("❌ S3 access validation failed. Please check your configuration.")
            return False
        
        # Initialize data ingestion
        print("📊 Initializing data ingestion...")
        ingestion = DataIngestion(aws_config)
        
        # Run data ingestion
        print("⬆️  Starting data ingestion process...")
        success = ingestion.ingest_all_sample_data()
        
        if success:
            print("✅ Data preparation completed successfully!")
            print(f"📍 Data stored in S3 bucket: {aws_config.s3_bucket}")
            print(f"📍 Glue database: {aws_config.glue_database}")
            
            # Show some metrics
            metrics = ingestion.monitor_ingestion_performance('raw/transactions/year=2023/month=1/transactions.parquet')
            if metrics:
                print(f"📊 Sample metrics: {metrics}")
            
            return True
        else:
            print("❌ Data preparation failed!")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed:")
        print("pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error during data preparation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
5. Create Helper Scripts
Create scripts/setup_project.py:

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
6. Step-by-Step Execution Guide
Step 1: Complete Initial Setup
# 1. Make sure you're in the project directory
cd ecommerce-ml-project

# 2. Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# 3. Run setup helper
python scripts/setup_project.py
Step 2: Configure Environment
# 1. Update .env file with your actual values
nano .env  # or use your preferred editor

# Example .env content:
# AWS_REGION=us-east-1
# ML_DATA_BUCKET=my-unique-ml-bucket-12345
# GLUE_DATABASE=ecommerce_ml_db
# SAGEMAKER_ROLE=arn:aws:iam::123456789012:role/SageMakerExecutionRole
Step 3: Create S3 Bucket (if not exists)
# Replace with your bucket name from .env
aws s3 mb s3://my-unique-ml-bucket-12345

# Verify
aws s3 ls | grep my-unique-ml-bucket-12345
Step 4: Run Data Preparation
# Option 1: Run the complete data preparation
python run_data_preparation.py

# Option 2: Run step by step in Python
python -c "
import sys
sys.path.append('src')
from config.aws_config import AWSConfig
from data_preparation.data_ingestion import DataIngestion

aws_config = AWSConfig()
print('Config loaded:', aws_config.s3_bucket)

ingestion = DataIngestion(aws_config)
success = ingestion.ingest_all_sample_data()
print('Success:', success)
"
Step 5: Verify Data Ingestion
# Check S3 bucket contents
aws s3 ls s3://my-unique-ml-bucket-12345/raw/ --recursive

# Run validation
python src/utils/validation.py
7. Troubleshooting Common Issues
Issue 1: AWS Credentials Not Found
# Check current credentials
aws sts get-caller-identity

# If not configured, run:
aws configure
Issue 2: S3 Bucket Access Denied
# Check bucket exists and you have access
aws s3 ls s3://your-bucket-name

# Check your IAM permissions - you need:
# - s3:GetObject
# - s3:PutObject  
# - s3:ListBucket
Issue 3: Import Errors
# Make sure you're in the virtual environment
which python
# Should show path to .venv/bin/python

# Reinstall packages if needed
pip install -r requirements.txt --force-reinstall
Issue 4: Module Not Found
# Set PYTHONPATH
export PYTHONPATH="\${PYTHONPATH}:\$(pwd)/src"

# Or use the runner script which handles this
python run_data_preparation.py
8. Quick Test Run
Here's a minimal test to verify everything works:

# test_setup.py
import sys
sys.path.append('src')

try:
    from config.aws_config import AWSConfig
    
    print("Testing AWS configuration...")
    config = AWSConfig()
    print(f"✅ S3 Bucket: {config.s3_bucket}")
    print(f"✅ Region: {config.region_name}")
    
    # Test AWS connectivity
    validation = config.validate_setup()
    if validation.get('s3_access'):
        print("✅ AWS connection successful!")
    else:
        print("❌ AWS connection failed!")
        
except Exception as e:
    print(f"❌ Setup test failed: {e}")
Run with: python test_setup.py

9. Expected Output
When successful, you should see:

🚀 Starting AWS ML Data Preparation...
🔧 Initializing AWS configuration...
✅ S3 bucket my-unique-ml-bucket-12345 is accessible
✅ AWS Glue is accessible
🔍 Validating AWS setup...
📊 Initializing data ingestion...
⬆️  Starting data ingestion process...
INFO:__main__:Generating sample e-commerce data...
INFO:__main__:Saved customers.csv
INFO:__main__:Saved products.json
INFO:__main__:Saved transactions.parquet
INFO:__main__:Saved clickstream.jsonl
INFO:__main__:Successfully uploaded data/sample/customers.csv to s3://my-unique-ml-bucket-12345/raw/customers/customers.csv
INFO:__main__:Converted JSON to Parquet and uploaded to S3
INFO:__main__:Uploaded partitioned Parquet to s3://my-unique-ml-bucket-12345/raw/transactions/transactions.parquet
INFO:__main__:Converted JSON Lines to Parquet and uploaded to S3
INFO:__main__:Created Glue database: ecommerce_ml_db
INFO:__main__:Created Glue table: customers
INFO:__main__:Created Glue table: transactions
✅ Data preparation completed successfully!
📍 Data stored in S3 bucket: my-unique-ml-bucket-12345
📍 Glue database: ecommerce_ml_db
This completes the data preparation setup and execution! The scripts will generate sample e-commerce data and upload it to your S3 bucket in the proper format for ML processing.
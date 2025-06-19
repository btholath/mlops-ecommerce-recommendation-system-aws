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
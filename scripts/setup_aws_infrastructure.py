# scripts/setup_aws_infrastructure.py
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def setup_s3_bucket():
    """Create S3 bucket for ML data"""
    s3_client = boto3.client('s3')
    bucket_name = os.getenv('ML_BUCKET')
    
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"S3 bucket {bucket_name} created successfully")
        
        # Create folder structure
        folders = [
            'raw-data/customers/',
            'raw-data/products/',
            'raw-data/transactions/',
            'processed-data/',
            'models/',
            'feature-store/'
        ]
        
        for folder in folders:
            s3_client.put_object(Bucket=bucket_name, Key=folder)
        
        print("S3 folder structure created")
        
    except Exception as e:
        print(f"Error creating S3 bucket: {e}")

def create_iam_roles():
    """Create necessary IAM roles"""
    iam_client = boto3.client('iam')
    
    # SageMaker execution role
    sagemaker_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "sagemaker.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        iam_client.create_role(
            RoleName='SageMakerExecutionRole',
            AssumeRolePolicyDocument=json.dumps(sagemaker_policy),
            Description='SageMaker execution role for ML pipeline'
        )
        
        # Attach policies
        iam_client.attach_role_policy(
            RoleName='SageMakerExecutionRole',
            PolicyArn='arn:aws:iam::aws:policy/AmazonSageMakerFullAccess'
        )
        
        print("SageMaker execution role created")
        
    except Exception as e:
        print(f"Error creating IAM roles: {e}")

def main():
    """Setup AWS infrastructure"""
    print("Setting up AWS infrastructure...")
    
    setup_s3_bucket()
    create_iam_roles()
    
    print("AWS infrastructure setup completed!")

if __name__ == "__main__":
    main()
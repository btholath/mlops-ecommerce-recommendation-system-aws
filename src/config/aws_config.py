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
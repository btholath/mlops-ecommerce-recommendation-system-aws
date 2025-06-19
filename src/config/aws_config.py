import boto3
import os
from typing import Dict, Any

class AWSConfig:
    """AWS Configuration and service clients"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.region_name = region_name
        self.session = boto3.Session(region_name=region_name)
        
        # Initialize AWS service clients
        self.s3_client = self.session.client('s3')
        self.glue_client = self.session.client('glue')
        self.sagemaker_client = self.session.client('sagemaker')
        self.athena_client = self.session.client('athena')
        
        # Configuration
        self.s3_bucket = os.getenv('ML_DATA_BUCKET', 'my-ml-data-bucket')
        self.glue_database = os.getenv('GLUE_DATABASE', 'ecommerce_ml_db')
        self.sagemaker_role = os.getenv('SAGEMAKER_ROLE')
        
    def get_s3_path(self, key: str) -> str:
        return f's3://{self.s3_bucket}/{key}'
    
    def validate_setup(self) -> Dict[str, bool]:
        """Validate AWS resources are accessible"""
        validation = {}
        
        try:
            # Check S3 bucket access
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            validation['s3_access'] = True
        except Exception as e:
            print(f"S3 bucket access failed: {e}")
            validation['s3_access'] = False
            
        try:
            # Check Glue database
            self.glue_client.get_database(Name=self.glue_database)
            validation['glue_database'] = True
        except Exception as e:
            print(f"Glue database access failed: {e}")
            validation['glue_database'] = False
            
        return validation
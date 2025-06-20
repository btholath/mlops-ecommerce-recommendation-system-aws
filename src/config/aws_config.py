# src/config/aws_config.py
import boto3
import os
from typing import Dict, Any

class AWSConfig:
    """AWS Configuration and client management"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.region_name = region_name
        self.clients = {}
        
    def get_client(self, service_name: str):
        """Get AWS service client with lazy loading"""
        if service_name not in self.clients:
            self.clients[service_name] = boto3.client(
                service_name, 
                region_name=self.region_name
            )
        return self.clients[service_name]
    
    def get_session(self):
        """Get boto3 session"""
        return boto3.Session(region_name=self.region_name)

# Environment configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('ML_BUCKET', 'mlops-ecommerce-data-prod-btholath')
SAGEMAKER_ROLE = os.getenv('SAGEMAKER_ROLE')

# Data paths
RAW_DATA_PREFIX = 'raw-data'
PROCESSED_DATA_PREFIX = 'processed-data'
FEATURE_STORE_PREFIX = 'feature-store'
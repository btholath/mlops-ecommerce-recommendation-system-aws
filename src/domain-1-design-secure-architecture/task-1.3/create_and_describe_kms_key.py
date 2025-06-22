
"""
create_and_describe_kms_key.py

This script:
1. Creates a KMS key
2. Retrieves and prints all metadata about the created key
"""

import boto3
import logging
from dotenv import load_dotenv
import os
import json

# Load environment and configure logging
load_dotenv()
REGION = os.getenv("AWS_REGION", "us-east-1")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def create_kms_key():
    kms_client = boto3.client('kms', region_name=REGION)
    response = kms_client.create_key(
        Description='ML Secure Architecture KMS Key',
        KeyUsage='ENCRYPT_DECRYPT',
        CustomerMasterKeySpec='SYMMETRIC_DEFAULT',
        Origin='AWS_KMS',
        Tags=[
            {'TagKey': 'Project', 'TagValue': 'SecureArchitecture'},
            {'TagKey': 'Environment', 'TagValue': 'Dev'}
        ]
    )
    key_id = response['KeyMetadata']['KeyId']
    logging.info(f"KMS Key Created: {key_id}")
    return key_id

def describe_kms_key(key_id):
    kms_client = boto3.client('kms', region_name=REGION)
    response = kms_client.describe_key(KeyId=key_id)
    metadata = response['KeyMetadata']
    logging.info("Full Key Metadata:")
    print(json.dumps(metadata, indent=2, default=str))


if __name__ == "__main__":
    key_id = create_kms_key()
    describe_kms_key(key_id)

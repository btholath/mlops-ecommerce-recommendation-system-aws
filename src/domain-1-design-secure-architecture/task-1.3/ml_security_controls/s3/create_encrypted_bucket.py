
import boto3
import logging

logging.basicConfig(level=logging.INFO)
s3 = boto3.client('s3')
bucket_name = 'ml-secure-bucket-2025'

s3.create_bucket(Bucket=bucket_name)
s3.put_bucket_encryption(
    Bucket=bucket_name,
    ServerSideEncryptionConfiguration={
        'Rules': [{
            'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'aws:kms'}
        }]
    }
)
logging.info(f"Bucket {bucket_name} encrypted with SSE-KMS")

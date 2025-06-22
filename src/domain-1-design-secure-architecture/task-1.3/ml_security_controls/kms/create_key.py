
import boto3
import logging

logging.basicConfig(level=logging.INFO)
client = boto3.client('kms')

response = client.create_key(
    Description='Key for ML data encryption',
    KeyUsage='ENCRYPT_DECRYPT',
    Origin='AWS_KMS'
)
logging.info(f"Key Created: {response['KeyMetadata']['KeyId']}")

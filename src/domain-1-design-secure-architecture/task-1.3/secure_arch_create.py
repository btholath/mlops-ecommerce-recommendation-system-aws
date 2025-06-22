
"""
secure_arch_sample.py

Demonstrates secure architecture practices using AWS SDK.
"""


import os
from dotenv import load_dotenv
import boto3
import logging

load_dotenv()
REGION = os.getenv("AWS_REGION")
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def create_kms_key():
    client = boto3.client('kms', region_name=REGION)
    response = client.create_key(
        Description='Key for ML data encryption',
        KeyUsage='ENCRYPT_DECRYPT',
        Origin='AWS_KMS'
    )
    key_id = response['KeyMetadata']['KeyId']
    logging.info(f"KMS Key Created: {key_id}")
    return key_id

def create_encrypted_bucket(bucket_name, kms_key_id):
    s3 = boto3.client('s3', region_name=REGION)
    s3.create_bucket(Bucket=bucket_name)
    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            'Rules': [{
                'ApplyServerSideEncryptionByDefault': {
                    'SSEAlgorithm': 'aws:kms',
                    'KMSMasterKeyID': kms_key_id
                }
            }]
        }
    )
    logging.info(f"Encrypted S3 Bucket created: {bucket_name}")

def request_tls_certificate(domain_name):
    acm = boto3.client('acm', region_name=REGION)
    response = acm.request_certificate(
        DomainName=domain_name,
        ValidationMethod='DNS'
    )
    logging.info(f"Requested ACM Certificate: {response['CertificateArn']}")

def create_rds_snapshot(instance_id, snapshot_id):
    rds = boto3.client('rds', region_name=REGION)
    response = rds.create_db_snapshot(
        DBInstanceIdentifier=instance_id,
        DBSnapshotIdentifier=snapshot_id
    )
    logging.info(f"RDS Snapshot Created: {response['DBSnapshot']['DBSnapshotIdentifier']}")

def classify_glue_resource(resource_arn):
    glue = boto3.client('glue', region_name=REGION)
    glue.tag_resource(
        ResourceArn=resource_arn,
        TagsToAdd={'Classification': 'Confidential', 'Retention': '1-year'}
    )
    logging.info("Tagged Glue resource for classification.")

def create_log_group(log_group_name):
    logs = boto3.client('logs', region_name=REGION)
    logs.create_log_group(logGroupName=log_group_name)
    logs.put_retention_policy(logGroupName=log_group_name, retentionInDays=90)
    logging.info(f"CloudWatch Log Group Created: {log_group_name}")

if __name__ == "__main__":
    key_id = create_kms_key()
    create_encrypted_bucket("ml-secure-bucket-sample", key_id)
    request_tls_certificate("example.com")
    create_rds_snapshot("ml-database-instance", "ml-database-snapshot")
    classify_glue_resource("arn:aws:glue:region:account-id:database/my-db")
    create_log_group("/ml/data/access")

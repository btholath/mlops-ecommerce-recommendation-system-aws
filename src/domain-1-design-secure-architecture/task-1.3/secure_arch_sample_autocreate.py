
"""
secure_arch_sample_autocreate.py

This script:
- Creates a KMS key
- Creates an S3 bucket with encryption
- Requests an ACM certificate
- Creates an RDS instance (if not exists) and snapshot
- Tags a Glue database
- Sets up a CloudWatch log group

Requires: boto3, python-dotenv
"""

import boto3
import os
import logging
from dotenv import load_dotenv
import json
from botocore.exceptions import ClientError

# Load environment variables and configure logging
load_dotenv()
REGION = os.getenv("AWS_REGION", "us-east-1")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Initialize clients
kms = boto3.client('kms', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
rds = boto3.client('rds', region_name=REGION)
acm = boto3.client('acm', region_name=REGION)
glue = boto3.client('glue', region_name=REGION)
logs = boto3.client('logs', region_name=REGION)

def create_kms_key():
    response = kms.create_key(
        Description='Key for ML data encryption',
        KeyUsage='ENCRYPT_DECRYPT',
        Origin='AWS_KMS'
    )
    key_id = response['KeyMetadata']['KeyId']
    logging.info(f"KMS Key Created: {key_id}")
    return key_id

def create_s3_bucket(bucket_name, kms_key_id):
    try:
        s3.head_bucket(Bucket=bucket_name)
        logging.info(f"Bucket already exists: {bucket_name}")
    except ClientError:
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

def request_acm_certificate(domain_name):
    response = acm.request_certificate(
        DomainName=domain_name,
        ValidationMethod='DNS'
    )
    logging.info(f"Requested ACM Certificate: {response['CertificateArn']}")

def create_rds_instance(instance_id):
    try:
        rds.describe_db_instances(DBInstanceIdentifier=instance_id)
        logging.info(f"RDS instance already exists: {instance_id}")
    except rds.exceptions.DBInstanceNotFoundFault:
        rds.create_db_instance(
            DBInstanceIdentifier=instance_id,
            AllocatedStorage=20,
            DBInstanceClass='db.t3.micro',
            Engine='mysql',
            MasterUsername='admin',
            MasterUserPassword='Password123!',
            PubliclyAccessible=True
        )
        logging.info(f"Creating RDS instance: {instance_id}")

def create_rds_snapshot(instance_id, snapshot_id):
    try:
        rds.describe_db_snapshots(DBSnapshotIdentifier=snapshot_id)
        logging.info(f"Snapshot already exists: {snapshot_id}")
    except rds.exceptions.DBSnapshotNotFoundFault:
        response = rds.create_db_snapshot(
            DBInstanceIdentifier=instance_id,
            DBSnapshotIdentifier=snapshot_id
        )
        logging.info(f"RDS Snapshot Created: {response['DBSnapshot']['DBSnapshotIdentifier']}")

def tag_glue_database(resource_arn):
    glue.tag_resource(
        ResourceArn=resource_arn,
        TagsToAdd={'Classification': 'Confidential', 'Retention': '1-year'}
    )
    logging.info("Tagged Glue resource for classification.")

def create_log_group(log_group_name):
    try:
        logs.create_log_group(logGroupName=log_group_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
            logging.info(f"Log group already exists: {log_group_name}")
            return
        else:
            raise
    logs.put_retention_policy(logGroupName=log_group_name, retentionInDays=90)
    logging.info(f"CloudWatch Log Group Created: {log_group_name}")

if __name__ == "__main__":
    key_id = create_kms_key()
    create_s3_bucket("ml-secure-bucket-sample", key_id)
    request_acm_certificate("example.com")
    create_rds_instance("ml-database-instance")
    create_rds_snapshot("ml-database-instance", "ml-database-snapshot")
    tag_glue_database("arn:aws:glue:region:account-id:database/my-db")
    create_log_group("/ml/data/access")

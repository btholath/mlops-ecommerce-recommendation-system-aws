
"""
secure_arch_cleanup_env_v2.py

Cleans up resources created by secure_arch_sample_autocreate_v2.py
- Includes error handling
- Checks resource state before deletion
- Uses environment and STS for dynamic config
"""

import boto3
import os
import logging
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()
REGION = os.getenv("AWS_REGION", "us-east-1")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# AWS clients
sts = boto3.client('sts', region_name=REGION)
ACCOUNT_ID = sts.get_caller_identity()['Account']

kms = boto3.client('kms', region_name=REGION)
s3 = boto3.resource('s3', region_name=REGION)
acm = boto3.client('acm', region_name=REGION)
rds = boto3.client('rds', region_name=REGION)
glue = boto3.client('glue', region_name=REGION)
logs = boto3.client('logs', region_name=REGION)

def schedule_kms_key_deletion(key_id):
    try:
        response = kms.describe_key(KeyId=key_id)
        key_state = response['KeyMetadata']['KeyState']
        if key_state == 'PendingDeletion':
            logging.info(f"KMS Key {key_id} is already pending deletion.")
        else:
            kms.schedule_key_deletion(KeyId=key_id, PendingWindowInDays=7)
            logging.info(f"KMS Key scheduled for deletion: {key_id}")
    except ClientError as e:
        logging.error(f"Failed to schedule KMS key deletion: {e}")

def delete_s3_bucket(bucket_name):
    try:
        bucket = s3.Bucket(bucket_name)
        bucket.objects.all().delete()
        bucket.delete()
        logging.info(f"S3 Bucket deleted: {bucket_name}")
    except ClientError as e:
        logging.error(f"Failed to delete S3 bucket: {e}")

def delete_acm_certificate(domain_name):
    try:
        certs = acm.list_certificates()['CertificateSummaryList']
        for cert in certs:
            if cert['DomainName'] == domain_name:
                acm.delete_certificate(CertificateArn=cert['CertificateArn'])
                logging.info(f"ACM Certificate deleted: {cert['CertificateArn']}")
                return
        logging.info("No ACM certificate found for deletion.")
    except ClientError as e:
        logging.error(f"Failed to delete ACM certificate: {e}")

def delete_rds_snapshot(snapshot_id):
    try:
        rds.delete_db_snapshot(DBSnapshotIdentifier=snapshot_id)
        logging.info(f"RDS Snapshot deleted: {snapshot_id}")
    except ClientError as e:
        logging.error(f"Failed to delete RDS snapshot: {e}")

def untag_glue_resource(resource_arn):
    try:
        glue.untag_resource(
            ResourceArn=resource_arn,
            TagsToRemove=['Classification', 'Retention']
        )
        logging.info("Removed tags from Glue resource.")
    except ClientError as e:
        logging.error(f"Failed to untag Glue resource: {e}")

def delete_log_group(log_group_name):
    try:
        logs.delete_log_group(logGroupName=log_group_name)
        logging.info(f"CloudWatch Log Group deleted: {log_group_name}")
    except ClientError as e:
        logging.error(f"Failed to delete CloudWatch Log Group: {e}")

if __name__ == "__main__":
    kms_key_id = os.getenv("KMS_KEY_ID")
    s3_bucket_name = os.getenv("S3_BUCKET_NAME", "ml-secure-bucket-sample")
    domain_name = os.getenv("ACM_DOMAIN_NAME", "example.com")
    rds_snapshot_id = os.getenv("RDS_SNAPSHOT_ID", "ml-database-snapshot")
    glue_db_name = os.getenv("GLUE_DB_NAME", "my-db")
    log_group_name = os.getenv("LOG_GROUP_NAME", "/ml/data/access")

    glue_resource_arn = f"arn:aws:glue:{REGION}:{ACCOUNT_ID}:database/{glue_db_name}"

    schedule_kms_key_deletion(kms_key_id)
    delete_s3_bucket(s3_bucket_name)
    delete_acm_certificate(domain_name)
    delete_rds_snapshot(rds_snapshot_id)
    untag_glue_resource(glue_resource_arn)
    delete_log_group(log_group_name)

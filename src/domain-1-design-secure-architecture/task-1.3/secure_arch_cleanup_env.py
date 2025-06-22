
"""
secure_arch_cleanup.py

Cleans up AWS resources created by secure_arch_sample.py
"""


import os
from dotenv import load_dotenv
import boto3
import logging

load_dotenv()
REGION = os.getenv("AWS_REGION")
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def schedule_kms_key_deletion(key_id):
    kms = boto3.client('kms', region_name=REGION)
    response = kms.schedule_key_deletion(KeyId=key_id, PendingWindowInDays=7)
    logging.info(f"KMS Key scheduled for deletion: {key_id}")

def delete_s3_bucket(bucket_name):
    s3 = boto3.resource('s3', region_name=REGION)
    bucket = s3.Bucket(bucket_name)
    bucket.objects.all().delete()
    bucket.delete()
    logging.info(f"S3 Bucket deleted: {bucket_name}")

def delete_acm_certificate(domain_name):
    acm = boto3.client('acm', region_name=REGION)
    certs = acm.list_certificates()['CertificateSummaryList']
    for cert in certs:
        if cert['DomainName'] == domain_name:
            acm.delete_certificate(CertificateArn=cert['CertificateArn'])
            logging.info(f"ACM Certificate deleted: {cert['CertificateArn']}")

def delete_rds_snapshot(snapshot_id):
    rds = boto3.client('rds', region_name=REGION)
    rds.delete_db_snapshot(DBSnapshotIdentifier=snapshot_id)
    logging.info(f"RDS Snapshot deleted: {snapshot_id}")

def untag_glue_resource(resource_arn):
    glue = boto3.client('glue', region_name=REGION)
    glue.untag_resource(
        ResourceArn=resource_arn,
        TagsToRemove=['Classification', 'Retention']
    )
    logging.info("Removed tags from Glue resource.")

def delete_log_group(log_group_name):
    logs = boto3.client('logs', region_name=REGION)
    logs.delete_log_group(logGroupName=log_group_name)
    logging.info(f"CloudWatch Log Group deleted: {log_group_name}")

if __name__ == "__main__":
    kms_key_id = os.getenv("KMS_KEY_ID")
    s3_bucket_name = os.getenv("S3_BUCKET_NAME", "ml-secure-bucket-sample")
    domain_name = os.getenv("ACM_DOMAIN_NAME", "example.com")
    rds_snapshot_id = os.getenv("RDS_SNAPSHOT_ID", "ml-database-snapshot")
    glue_resource_arn = os.getenv("GLUE_RESOURCE_ARN", "arn:aws:glue:region:account-id:database/my-db")
    log_group_name = os.getenv("LOG_GROUP_NAME", "/ml/data/access")

    schedule_kms_key_deletion(kms_key_id)
    delete_s3_bucket(s3_bucket_name)
    delete_acm_certificate(domain_name)
    delete_rds_snapshot(rds_snapshot_id)
    untag_glue_resource(glue_resource_arn)
    delete_log_group(log_group_name)

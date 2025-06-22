
import boto3
import logging

logging.basicConfig(level=logging.INFO)
client = boto3.client('logs')
log_group = '/ml/data/access'

client.create_log_group(logGroupName=log_group)
client.put_retention_policy(logGroupName=log_group, retentionInDays=90)
logging.info(f"Created log group and set retention: {log_group}")

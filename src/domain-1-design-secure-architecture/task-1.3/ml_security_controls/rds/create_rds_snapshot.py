
import boto3
import logging

logging.basicConfig(level=logging.INFO)
rds = boto3.client('rds')

response = rds.create_db_snapshot(
    DBSnapshotIdentifier='ml-database-snapshot',
    DBInstanceIdentifier='ml-database-instance'
)
logging.info("Snapshot created: " + response['DBSnapshot']['DBSnapshotIdentifier'])

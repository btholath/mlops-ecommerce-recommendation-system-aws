
import boto3
import logging

logging.basicConfig(level=logging.INFO)
client = boto3.client('glue')

client.tag_resource(
    ResourceArn='arn:aws:glue:region:account-id:database/my-db',
    TagsToAdd={'Classification': 'Confidential', 'Retention': '1-year'}
)
logging.info("Tags applied to Glue database.")

# src/data_preparation/data_ingestion.py
import boto3
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from src.config.aws_config import AWSConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestionPipeline:
    """
    Handles data ingestion from multiple sources:
    - S3 (batch files)
    - Kinesis (streaming data)
    - RDS (transactional data)
    """
    
    def __init__(self, aws_config: AWSConfig):
        self.aws_config = aws_config
        self.s3_client = aws_config.get_client('s3')
        self.kinesis_client = aws_config.get_client('kinesis')
        self.glue_client = aws_config.get_client('glue')
        
    def ingest_from_s3(self, bucket: str, prefix: str, 
                       file_format: str = 'parquet') -> pd.DataFrame:
        """
        Ingest batch data from S3
        Supports multiple file formats as per exam requirements
        """
        try:
            # List objects in S3 prefix
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                logger.warning(f"No files found in s3://{bucket}/{prefix}")
                return pd.DataFrame()
            
            dataframes = []
            for obj in response['Contents']:
                key = obj['Key']
                if not key.endswith(f'.{file_format}'):
                    continue
                    
                # Read based on format
                if file_format == 'parquet':
                    df = pd.read_parquet(f's3://{bucket}/{key}')
                elif file_format == 'csv':
                    df = pd.read_csv(f's3://{bucket}/{key}')
                elif file_format == 'json':
                    df = pd.read_json(f's3://{bucket}/{key}', lines=True)
                else:
                    raise ValueError(f"Unsupported format: {file_format}")
                
                dataframes.append(df)
            
            # Combine all dataframes
            combined_df = pd.concat(dataframes, ignore_index=True)
            logger.info(f"Ingested {len(combined_df)} records from S3")
            
            return combined_df
            
        except Exception as e:
            logger.error(f"Error ingesting from S3: {str(e)}")
            raise
    
    def setup_kinesis_consumer(self, stream_name: str, 
                              consumer_name: str) -> Dict:
        """
        Set up Kinesis consumer for real-time data ingestion
        """
        try:
            # Register stream consumer
            response = self.kinesis_client.register_stream_consumer(
                StreamARN=f"arn:aws:kinesis:{self.aws_config.region_name}:"
                         f"{boto3.client('sts').get_caller_identity()['Account']}:"
                         f"stream/{stream_name}",
                ConsumerName=consumer_name
            )
            
            logger.info(f"Kinesis consumer {consumer_name} registered")
            return response
            
        except Exception as e:
            logger.error(f"Error setting up Kinesis consumer: {str(e)}")
            raise
    
    def ingest_streaming_data(self, stream_name: str, 
                             shard_iterator_type: str = 'LATEST') -> List[Dict]:
        """
        Ingest real-time streaming data from Kinesis
        """
        try:
            # Get shard information
            stream_description = self.kinesis_client.describe_stream(
                StreamName=stream_name
            )
            
            records = []
            for shard in stream_description['StreamDescription']['Shards']:
                shard_id = shard['ShardId']
                
                # Get shard iterator
                shard_iterator_response = self.kinesis_client.get_shard_iterator(
                    StreamName=stream_name,
                    ShardId=shard_id,
                    ShardIteratorType=shard_iterator_type
                )
                
                shard_iterator = shard_iterator_response['ShardIterator']
                
                # Get records
                records_response = self.kinesis_client.get_records(
                    ShardIterator=shard_iterator,
                    Limit=1000
                )
                
                for record in records_response['Records']:
                    data = json.loads(record['Data'])
                    records.append(data)
            
            logger.info(f"Ingested {len(records)} streaming records")
            return records
            
        except Exception as e:
            logger.error(f"Error ingesting streaming data: {str(e)}")
            raise
    
    def create_glue_crawler(self, crawler_name: str, s3_path: str, 
                           database_name: str) -> Dict:
        """
        Create AWS Glue crawler for data cataloging
        """
        try:
            response = self.glue_client.create_crawler(
                Name=crawler_name,
                Role=os.getenv('GLUE_ROLE'),
                DatabaseName=database_name,
                Targets={
                    'S3Targets': [
                        {
                            'Path': s3_path,
                            'Exclusions': ['*.tmp', '*.log']
                        }
                    ]
                },
                Schedule='cron(0 2 * * ? *)',  # Daily at 2 AM
                Configuration=json.dumps({
                    "Version": 1.0,
                    "Grouping": {
                        "TableGroupingPolicy": "CombineCompatibleSchemas"
                    }
                })
            )
            
            logger.info(f"Glue crawler {crawler_name} created successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error creating Glue crawler: {str(e)}")
            raise
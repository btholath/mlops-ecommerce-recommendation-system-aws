import boto3
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from src.config.aws_config import AWSConfig
import io

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
                       file_format: str = 'csv') -> pd.DataFrame:
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
                
                # Skip directories (keys ending with /)
                if key.endswith('/'):
                    continue
                    
                if not key.endswith(f'.{file_format}'):
                    continue
                
                logger.info(f"Reading file: s3://{bucket}/{key}")
                
                # Get object from S3
                s3_object = self.s3_client.get_object(Bucket=bucket, Key=key)
                
                # Read based on format
                if file_format == 'csv':
                    # Read CSV directly from S3 object
                    df = pd.read_csv(io.BytesIO(s3_object['Body'].read()))
                elif file_format == 'parquet':
                    # For parquet, we need to use s3fs or download first
                    df = self._read_parquet_from_s3(bucket, key)
                elif file_format == 'json':
                    # Read JSON lines format
                    content = s3_object['Body'].read().decode('utf-8')
                    df = pd.read_json(io.StringIO(content), lines=True)
                else:
                    raise ValueError(f"Unsupported format: {file_format}")
                
                logger.info(f"Read {len(df)} records from {key}")
                dataframes.append(df)
            
            if not dataframes:
                logger.warning(f"No {file_format} files found in s3://{bucket}/{prefix}")
                return pd.DataFrame()
            
            # Combine all dataframes
            combined_df = pd.concat(dataframes, ignore_index=True)
            logger.info(f"Ingested {len(combined_df)} total records from S3")
            
            return combined_df
            
        except Exception as e:
            logger.error(f"Error ingesting from S3: {str(e)}")
            raise
    
    def _read_parquet_from_s3(self, bucket: str, key: str) -> pd.DataFrame:
        """Read parquet file from S3 using boto3"""
        try:
            # Download to temporary location and read
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as tmp_file:
                self.s3_client.download_fileobj(bucket, key, tmp_file)
                tmp_file.flush()
                
                # Read parquet file
                df = pd.read_parquet(tmp_file.name)
                
                # Clean up
                os.unlink(tmp_file.name)
                
                return df
                
        except Exception as e:
            logger.error(f"Error reading parquet from S3: {str(e)}")
            raise
    
    def ingest_from_s3_with_s3fs(self, bucket: str, prefix: str, 
                                 file_format: str = 'csv') -> pd.DataFrame:
        """
        Alternative method using s3fs (requires s3fs package)
        """
        try:
            import s3fs
            
            # Create s3fs filesystem
            fs = s3fs.S3FileSystem()
            
            # List files
            files = fs.glob(f's3://{bucket}/{prefix}/*.{file_format}')
            
            if not files:
                logger.warning(f"No {file_format} files found in s3://{bucket}/{prefix}")
                return pd.DataFrame()
            
            dataframes = []
            for file_path in files:
                logger.info(f"Reading file: s3://{file_path}")
                
                if file_format == 'csv':
                    with fs.open(f's3://{file_path}', 'r') as f:
                        df = pd.read_csv(f)
                elif file_format == 'parquet':
                    df = pd.read_parquet(f's3://{file_path}', filesystem=fs)
                elif file_format == 'json':
                    with fs.open(f's3://{file_path}', 'r') as f:
                        df = pd.read_json(f, lines=True)
                else:
                    raise ValueError(f"Unsupported format: {file_format}")
                
                dataframes.append(df)
            
            # Combine all dataframes
            combined_df = pd.concat(dataframes, ignore_index=True)
            logger.info(f"Ingested {len(combined_df)} total records from S3")
            
            return combined_df
            
        except ImportError:
            logger.warning("s3fs not available, falling back to boto3 method")
            return self.ingest_from_s3(bucket, prefix, file_format)
        except Exception as e:
            logger.error(f"Error ingesting from S3 with s3fs: {str(e)}")
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
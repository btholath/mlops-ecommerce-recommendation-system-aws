# src/data_preparation/feature_store.py
import boto3
import pandas as pd
from datetime import datetime
import json
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class FeatureStoreManager:
    """
    Manage features in Amazon SageMaker Feature Store
    """
    
    def __init__(self, aws_config):
        self.aws_config = aws_config
        self.sagemaker_client = aws_config.get_client('sagemaker')
        self.featurestore_runtime = aws_config.get_client('sagemaker-featurestore-runtime')
        
    def create_feature_group(self, feature_group_name: str, 
                           feature_definitions: List[Dict],
                           record_identifier_name: str,
                           event_time_name: str,
                           role_arn: str,
                           s3_uri: str) -> Dict:
        """
        Create a feature group in SageMaker Feature Store
        """
        try:
            response = self.sagemaker_client.create_feature_group(
                FeatureGroupName=feature_group_name,
                RecordIdentifierFeatureName=record_identifier_name,
                EventTimeFeatureName=event_time_name,
                FeatureDefinitions=feature_definitions,
                OnlineStoreConfig={
                    'EnableOnlineStore': True
                },
                OfflineStoreConfig={
                    'S3StorageConfig': {
                        'S3Uri': s3_uri,
                        'ResolvedOutputS3Uri': f"{s3_uri}/{feature_group_name}"
                    },
                    'DisableGlueTableCreation': False,
                    'DataCatalogConfig': {
                        'TableName': f"{feature_group_name}_table",
                        'Catalog': 'AwsDataCatalog',
                        'Database': 'sagemaker_featurestore'
                    }
                },
                RoleArn=role_arn,
                Description=f"Feature group for {feature_group_name}"
            )
            
            logger.info(f"Feature group {feature_group_name} created successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error creating feature group: {str(e)}")
            raise
    
    def ingest_features(self, feature_group_name: str, 
                       features_df: pd.DataFrame,
                       record_identifier_column: str,
                       event_time_column: str = None) -> Dict:
        """
        Ingest features into the feature store
        """
        try:
            # Add event time if not provided
            if event_time_column is None:
                features_df['event_time'] = datetime.now().timestamp()
                event_time_column = 'event_time'
            
            # Convert DataFrame to records
            records = []
            for _, row in features_df.iterrows():
                record = []
                for column, value in row.items():
                    if pd.isna(value):
                        continue
                    
                    feature_value = {
                        'FeatureName': column,
                    }
                    
                    if isinstance(value, (int, float)):
                        if isinstance(value, float):
                            feature_value['ValueAsString'] = str(value)
                        else:
                            feature_value['ValueAsString'] = str(value)
                    else:
                        feature_value['ValueAsString'] = str(value)
                    
                    record.append(feature_value)
                
                records.append({
                    'Record': record
                })
            
            # Batch put records
            batch_size = 100
            successful_records = 0
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                response = self.featurestore_runtime.batch_get_record(
                    Identifiers=[
                        {
                            'FeatureGroupName': feature_group_name,
                            'RecordIdentifiersValueAsString': [
                                str(features_df.iloc[j][record_identifier_column])
                                for j in range(i, min(i + batch_size, len(features_df)))
                            ]
                        }
                    ]
                )
                
                successful_records += len(batch)
            
            logger.info(f"Successfully ingested {successful_records} records to {feature_group_name}")
            return {"successful_records": successful_records}
            
        except Exception as e:
            logger.error(f"Error ingesting features: {str(e)}")
            raise
    
    def get_features(self, feature_group_name: str, 
                    record_identifier: str) -> Dict:
        """
        Retrieve features for a specific record
        """
        try:
            response = self.featurestore_runtime.get_record(
                FeatureGroupName=feature_group_name,
                RecordIdentifierValueAsString=record_identifier
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving features: {str(e)}")
            raise
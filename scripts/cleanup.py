#!/usr/bin/env python3
"""
AWS ML Project Cleanup Script
Removes all AWS resources created by the project
"""

import boto3
import json
import time
import argparse
from typing import List, Dict, Any
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.append('src')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectCleanup:
    """
    Comprehensive cleanup for AWS ML project resources
    """
    
    def __init__(self, aws_config, dry_run: bool = False):
        self.aws_config = aws_config
        self.dry_run = dry_run
        self.s3_client = aws_config.s3_client
        self.glue_client = aws_config.glue_client
        self.sagemaker_client = aws_config.sagemaker_client
        self.cleanup_log = []
        
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No resources will be deleted")
        else:
            logger.warning("⚠️  LIVE MODE - Resources will be permanently deleted!")
    
    def cleanup_all(self, confirm: bool = False) -> Dict[str, Any]:
        """Run complete cleanup"""
        if not confirm and not self.dry_run:
            response = input("Are you sure you want to delete ALL project resources? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Cleanup cancelled by user")
                return {'status': 'cancelled'}
        
        logger.info("🧹 Starting comprehensive project cleanup...")
        
        cleanup_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'dry_run': self.dry_run,
            'results': {}
        }
        
        # Cleanup in reverse dependency order
        cleanup_results['results']['sagemaker'] = self._cleanup_sagemaker_resources()
        cleanup_results['results']['glue'] = self._cleanup_glue_resources()
        cleanup_results['results']['s3'] = self._cleanup_s3_resources()
        cleanup_results['results']['local'] = self._cleanup_local_resources()
        
        # Generate cleanup report
        self._generate_cleanup_report(cleanup_results)
        
        return cleanup_results
    
    def _cleanup_s3_resources(self) -> Dict[str, Any]:
        """Clean up S3 bucket contents"""
        logger.info("Cleaning up S3 resources...")
        
        s3_results = {
            'bucket': self.aws_config.s3_bucket,
            'deleted_objects': [],
            'errors': [],
            'total_deleted': 0,
            'total_size_deleted_mb': 0
        }
        
        try:
            # List all objects in the bucket with our project prefix
            project_prefixes = ['raw/', 'processed/', 'models/', 'artifacts/']
            
            for prefix in project_prefixes:
                logger.info(f"Cleaning up S3 prefix: {prefix}")
                
                # List objects with pagination
                paginator = self.s3_client.get_paginator('list_objects_v2')
                pages = paginator.paginate(
                    Bucket=self.aws_config.s3_bucket,
                    Prefix=prefix
                )
                
                objects_to_delete = []
                
                for page in pages:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            objects_to_delete.append({
                                'Key': obj['Key'],
                                'Size': obj['Size']
                            })
                            s3_results['total_size_deleted_mb'] += obj['Size'] / (1024 * 1024)
                
                # Delete objects in batches of 1000 (S3 limit)
                batch_size = 1000
                for i in range(0, len(objects_to_delete), batch_size):
                    batch = objects_to_delete[i:i + batch_size]
                    
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would delete {len(batch)} objects from S3")
                        s3_results['deleted_objects'].extend([obj['Key'] for obj in batch])
                        s3_results['total_deleted'] += len(batch)
                    else:
                        try:
                            delete_objects = [{'Key': obj['Key']} for obj in batch]
                            
                            response = self.s3_client.delete_objects(
                                Bucket=self.aws_config.s3_bucket,
                                Delete={'Objects': delete_objects}
                            )
                            
                            if 'Deleted' in response:
                                deleted_keys = [obj['Key'] for obj in response['Deleted']]
                                s3_results['deleted_objects'].extend(deleted_keys)
                                s3_results['total_deleted'] += len(deleted_keys)
                                logger.info(f"Deleted {len(deleted_keys)} objects from S3")
                            
                            if 'Errors' in response:
                                s3_results['errors'].extend(response['Errors'])
                                logger.error(f"Errors deleting objects: {response['Errors']}")
                        
                        except Exception as e:
                            error_msg = f"Failed to delete batch: {str(e)}"
                            s3_results['errors'].append(error_msg)
                            logger.error(error_msg)
        
        except Exception as e:
            error_msg = f"Failed to cleanup S3 resources: {str(e)}"
            s3_results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return s3_results
    
    def _cleanup_glue_resources(self) -> Dict[str, Any]:
        """Clean up AWS Glue resources"""
        logger.info("Cleaning up Glue resources...")
        
        glue_results = {
            'database': {},
            'tables_deleted': [],
            'partitions_deleted': 0,
            'errors': []
        }
        
        try:
            database_name = self.aws_config.glue_database
            
            # Get all tables in the database
            try:
                tables_response = self.glue_client.get_tables(DatabaseName=database_name)
                tables = tables_response['TableList']
                
                # Delete tables
                for table in tables:
                    table_name = table['Name']
                    
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would delete Glue table: {table_name}")
                        glue_results['tables_deleted'].append(table_name)
                    else:
                        try:
                            # Delete partitions first if table is partitioned
                            if table.get('PartitionKeys'):
                                partitions_response = self.glue_client.get_partitions(
                                    DatabaseName=database_name,
                                    TableName=table_name
                                )
                                
                                for partition in partitions_response['Partitions']:
                                    self.glue_client.delete_partition(
                                        DatabaseName=database_name,
                                        TableName=table_name,
                                        PartitionValues=partition['Values']
                                    )
                                    glue_results['partitions_deleted'] += 1
                            
                            # Delete table
                            self.glue_client.delete_table(
                                DatabaseName=database_name,
                                Name=table_name
                            )
                            glue_results['tables_deleted'].append(table_name)
                            logger.info(f"Deleted Glue table: {table_name}")
                        
                        except Exception as e:
                            error_msg = f"Failed to delete table {table_name}: {str(e)}"
                            glue_results['errors'].append(error_msg)
                            logger.error(error_msg)
            
            except self.glue_client.exceptions.EntityNotFoundException:
                logger.info(f"Glue database {database_name} not found")
            
            # Delete database
            if self.dry_run:
                logger.info(f"[DRY RUN] Would delete Glue database: {database_name}")
                glue_results['database'] = {'status': 'would_delete'}
            else:
                try:
                    self.glue_client.delete_database(Name=database_name)
                    glue_results['database'] = {'status': 'deleted'}
                    logger.info(f"Deleted Glue database: {database_name}")
                
                except self.glue_client.exceptions.EntityNotFoundException:
                    glue_results['database'] = {'status': 'not_found'}
                    logger.info(f"Glue database {database_name} not found")
                
                except Exception as e:
                    error_msg = f"Failed to delete database {database_name}: {str(e)}"
                    glue_results['database'] = {'status': 'error', 'error': error_msg}
                    glue_results['errors'].append(error_msg)
                    logger.error(error_msg)
        
        except Exception as e:
            error_msg = f"Failed to cleanup Glue resources: {str(e)}"
            glue_results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return glue_results
    
    def _cleanup_sagemaker_resources(self) -> Dict[str, Any]:
        """Clean up SageMaker resources"""
        logger.info("Cleaning up SageMaker resources...")
        
        sagemaker_results = {
            'endpoints_deleted': [],
            'models_deleted': [],
            'training_jobs': [],
            'processing_jobs': [],
            'errors': []
        }
        
        try:
            # List and delete endpoints
            endpoints_response = self.sagemaker_client.list_endpoints()
            
            for endpoint in endpoints_response['Endpoints']:
                endpoint_name = endpoint['EndpointName']
                
                # Check if endpoint belongs to our project (by naming convention)
                if 'ecommerce-ml' in endpoint_name.lower() or 'recommendation' in endpoint_name.lower():
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would delete SageMaker endpoint: {endpoint_name}")
                        sagemaker_results['endpoints_deleted'].append(endpoint_name)
                    else:
                        try:
                            self.sagemaker_client.delete_endpoint(EndpointName=endpoint_name)
                            sagemaker_results['endpoints_deleted'].append(endpoint_name)
                            logger.info(f"Deleted SageMaker endpoint: {endpoint_name}")
                        except Exception as e:
                            error_msg = f"Failed to delete endpoint {endpoint_name}: {str(e)}"
                            sagemaker_results['errors'].append(error_msg)
                            logger.error(error_msg)
            
            # List and delete models
            models_response = self.sagemaker_client.list_models()
            
            for model in models_response['Models']:
                model_name = model['ModelName']
                
                # Check if model belongs to our project
                if 'ecommerce-ml' in model_name.lower() or 'recommendation' in model_name.lower():
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would delete SageMaker model: {model_name}")
                        sagemaker_results['models_deleted'].append(model_name)
                    else:
                        try:
                            self.sagemaker_client.delete_model(ModelName=model_name)
                            sagemaker_results['models_deleted'].append(model_name)
                            logger.info(f"Deleted SageMaker model: {model_name}")
                        except Exception as e:
                            error_msg = f"Failed to delete model {model_name}: {str(e)}"
                            sagemaker_results['errors'].append(error_msg)
                            logger.error(error_msg)
            
            # List training jobs (cannot delete, but list for reference)
            training_jobs_response = self.sagemaker_client.list_training_jobs(
                StatusEquals='Completed',
                MaxResults=100
            )
            
            project_training_jobs = [
                job['TrainingJobName'] for job in training_jobs_response['TrainingJobSummaries']
                if 'ecommerce-ml' in job['TrainingJobName'].lower() or 'recommendation' in job['TrainingJobName'].lower()
            ]
            
            sagemaker_results['training_jobs'] = project_training_jobs
            if project_training_jobs:
                logger.info(f"Found {len(project_training_jobs)} training jobs (cannot be deleted)")
        
        except Exception as e:
            error_msg = f"Failed to cleanup SageMaker resources: {str(e)}"
            sagemaker_results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return sagemaker_results
    
    def _cleanup_local_resources(self) -> Dict[str, Any]:
        """Clean up local project files"""
        logger.info("Cleaning up local resources...")
        
        local_results = {
            'directories_removed': [],
            'files_removed': [],
            'errors': []
        }
        
        try:
            import shutil
            
            # Directories to clean
            directories_to_clean = [
                'data/raw',
                'data/processed', 
                'data/sample',
                '__pycache__',
                'src/__pycache__',
                'src/data_preparation/__pycache__',
                'src/config/__pycache__',
                'src/utils/__pycache__'
            ]
            
            # Files to clean
            files_to_clean = [
                'validation_report.json',
                'cleanup_report.json',
                '.DS_Store'
            ]
            
            # Remove directories
            for dir_path in directories_to_clean:
                path = Path(dir_path)
                if path.exists():
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would remove directory: {dir_path}")
                        local_results['directories_removed'].append(str(path))
                    else:
                        try:
                            shutil.rmtree(path)
                            local_results['directories_removed'].append(str(path))
                            logger.info(f"Removed directory: {dir_path}")
                        except Exception as e:
                            error_msg = f"Failed to remove directory {dir_path}: {str(e)}"
                            local_results['errors'].append(error_msg)
                            logger.error(error_msg)
            
            # Remove files
            for file_path in files_to_clean:
                path = Path(file_path)
                if path.exists():
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would remove file: {file_path}")
                        local_results['files_removed'].append(str(path))
                    else:
                        try:
                            path.unlink()
                            local_results['files_removed'].append(str(path))
                            logger.info(f"Removed file: {file_path}")
                        except Exception as e:
                            error_msg = f"Failed to remove file {file_path}: {str(e)}"
                            local_results['errors'].append(error_msg)
                            logger.error(error_msg)
        
        except Exception as e:
            error_msg = f"Failed to cleanup local resources: {str(e)}"
            local_results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return local_results
    
    def _generate_cleanup_report(self, cleanup_results: Dict[str, Any]) -> None:
        """Generate cleanup report"""
        report_path = Path('cleanup_report.json')
        
        # Add summary
        cleanup_results['summary'] = {
            'total_s3_objects_deleted': cleanup_results['results']['s3']['total_deleted'],
            'total_size_deleted_mb': cleanup_results['results']['s3']['total_size_deleted_mb'],
            'glue_tables_deleted': len(cleanup_results['results']['glue']['tables_deleted']),
            'sagemaker_endpoints_deleted': len(cleanup_results['results']['sagemaker']['endpoints_deleted']),
            'sagemaker_models_deleted': len(cleanup_results['results']['sagemaker']['models_deleted']),
            'local_directories_removed': len(cleanup_results['results']['local']['directories_removed']),
            'total_errors': sum([
                len(cleanup_results['results'][service].get('errors', []))
                for service in cleanup_results['results']
            ])
        }
        
        if not self.dry_run:
            with open(report_path, 'w') as f:
                json.dump(cleanup_results, f, indent=2, default=str)
            logger.info(f"📋 Cleanup report saved to {report_path}")
        
        # Print summary
        self._print_cleanup_summary(cleanup_results)
    
    def _print_cleanup_summary(self, cleanup_results: Dict[str, Any]) -> None:
        """Print cleanup summary"""
        print("\n" + "="*60)
        print("🧹 PROJECT CLEANUP SUMMARY")
        print("="*60)
        
        mode = "DRY RUN" if self.dry_run else "LIVE RUN"
        print(f"Mode: {mode}")
        print(f"Timestamp: {cleanup_results['timestamp']}")
        
        summary = cleanup_results['summary']
        print(f"\n📊 CLEANUP STATISTICS:")
        print(f"  S3 Objects: {summary['total_s3_objects_deleted']}")
        print(f"  Data Size: {summary['total_size_deleted_mb']:.2f} MB")
        print(f"  Glue Tables: {summary['glue_tables_deleted']}")
        print(f"  SageMaker Endpoints: {summary['sagemaker_endpoints_deleted']}")
        print(f"  SageMaker Models: {summary['sagemaker_models_deleted']}")
        print(f"  Local Directories: {summary['local_directories_removed']}")
        print(f"  Total Errors: {summary['total_errors']}")
        
        if summary['total_errors'] > 0:
            print(f"\n⚠️  {summary['total_errors']} errors occurred during cleanup")
            print("Check the cleanup report for details")
        else:
            success_msg = "✅ Cleanup completed successfully" if not self.dry_run else "✅ Dry run completed successfully"
            print(f"\n{success_msg}")

def main():
    parser = argparse.ArgumentParser(description='AWS ML Project Cleanup Script')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without deleting resources')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--s3-only', action='store_true', help='Clean up S3 resources only')
    parser.add_argument('--glue-only', action='store_true', help='Clean up Glue resources only')
    parser.add_argument('--local-only', action='store_true', help='Clean up local resources only')
    
    args = parser.parse_args()
    
    try:
        from config.aws_config import AWSConfig
        
        # Initialize
        aws_config = AWSConfig()
        cleanup = ProjectCleanup(aws_config, dry_run=args.dry_run)
        
        # Selective cleanup
        if args.s3_only:
            result = cleanup._cleanup_s3_resources()
            print(f"S3 cleanup result: {json.dumps(result, indent=2, default=str)}")
        elif args.glue_only:
            result = cleanup._cleanup_glue_resources()
            print(f"Glue cleanup result: {json.dumps(result, indent=2, default=str)}")
        elif args.local_only:
            result = cleanup._cleanup_local_resources()
            print(f"Local cleanup result: {json.dumps(result, indent=2, default=str)}")
        else:
            # Full cleanup
            results = cleanup.cleanup_all(confirm=args.confirm)
            
            # Exit with error code if cleanup failed
            if results.get('summary', {}).get('total_errors', 0) > 0:
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n❌ Cleanup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
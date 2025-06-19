import boto3
import pandas as pd
import json
import awswrangler as wr
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectValidator:
    """
    Comprehensive validation for the ML project resources
    Validates AWS resources, data integrity, and project setup
    """
    
    def __init__(self, aws_config):
        self.aws_config = aws_config
        self.s3_client = aws_config.s3_client
        self.glue_client = aws_config.glue_client
        self.sagemaker_client = aws_config.sagemaker_client
        self.validation_results = {}
        
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        logger.info("🔍 Starting comprehensive project validation...")
        
        # AWS Resource Validation
        self.validation_results['aws_access'] = self._validate_aws_access()
        self.validation_results['s3_resources'] = self._validate_s3_resources()
        self.validation_results['glue_resources'] = self._validate_glue_resources()
        self.validation_results['iam_permissions'] = self._validate_iam_permissions()
        
        # Data Validation
        self.validation_results['data_integrity'] = self._validate_data_integrity()
        self.validation_results['data_schemas'] = self._validate_data_schemas()
        self.validation_results['data_quality'] = self._validate_data_quality()
        
        # Project Structure Validation
        self.validation_results['project_structure'] = self._validate_project_structure()
        self.validation_results['dependencies'] = self._validate_dependencies()
        
        # Performance and Cost Validation
        self.validation_results['storage_costs'] = self._validate_storage_costs()
        self.validation_results['performance_metrics'] = self._validate_performance_metrics()
        
        # Generate validation report
        self._generate_validation_report()
        
        return self.validation_results
    
    def _validate_aws_access(self) -> Dict[str, Any]:
        """Validate AWS service access and permissions"""
        logger.info("Validating AWS access...")
        
        access_results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'overall_status': True
        }
        
        # Test S3 access
        try:
            self.s3_client.list_buckets()
            self.s3_client.head_bucket(Bucket=self.aws_config.s3_bucket)
            access_results['services']['s3'] = {
                'status': 'success',
                'bucket_exists': True,
                'permissions': ['read', 'write']
            }
        except Exception as e:
            access_results['services']['s3'] = {
                'status': 'failed',
                'error': str(e),
                'bucket_exists': False
            }
            access_results['overall_status'] = False
        
        # Test Glue access
        try:
            self.glue_client.get_databases()
            try:
                self.glue_client.get_database(Name=self.aws_config.glue_database)
                database_exists = True
            except self.glue_client.exceptions.EntityNotFoundException:
                database_exists = False
            
            access_results['services']['glue'] = {
                'status': 'success',
                'database_exists': database_exists,
                'permissions': ['read', 'write']
            }
        except Exception as e:
            access_results['services']['glue'] = {
                'status': 'failed',
                'error': str(e)
            }
            access_results['overall_status'] = False
        
        # Test SageMaker access
        try:
            self.sagemaker_client.list_domains()
            access_results['services']['sagemaker'] = {
                'status': 'success',
                'permissions': ['read']
            }
        except Exception as e:
            access_results['services']['sagemaker'] = {
                'status': 'failed',
                'error': str(e)
            }
            access_results['overall_status'] = False
        
        return access_results
    
    def _validate_s3_resources(self) -> Dict[str, Any]:
        """Validate S3 bucket structure and data"""
        logger.info("Validating S3 resources...")
        
        s3_results = {
            'bucket_name': self.aws_config.s3_bucket,
            'structure': {},
            'data_files': {},
            'total_size_mb': 0,
            'file_count': 0
        }
        
        try:
            # Check expected folder structure
            expected_prefixes = ['raw/customers/', 'raw/products/', 'raw/transactions/', 'raw/clickstream/']
            
            for prefix in expected_prefixes:
                try:
                    response = self.s3_client.list_objects_v2(
                        Bucket=self.aws_config.s3_bucket,
                        Prefix=prefix,
                        MaxKeys=100
                    )
                    
                    if 'Contents' in response:
                        files = response['Contents']
                        total_size = sum([obj['Size'] for obj in files])
                        
                        s3_results['structure'][prefix] = {
                            'exists': True,
                            'file_count': len(files),
                            'total_size_mb': total_size / (1024 * 1024),
                            'files': [obj['Key'] for obj in files]
                        }
                        
                        s3_results['total_size_mb'] += total_size / (1024 * 1024)
                        s3_results['file_count'] += len(files)
                    else:
                        s3_results['structure'][prefix] = {
                            'exists': False,
                            'file_count': 0,
                            'total_size_mb': 0
                        }
                
                except Exception as e:
                    s3_results['structure'][prefix] = {
                        'exists': False,
                        'error': str(e)
                    }
            
            # Validate specific data files
            data_files = [
                'raw/customers/customers.csv',
                'raw/products/products.parquet',
                'raw/transactions/transactions.parquet',
                'raw/clickstream/clickstream.parquet'
            ]
            
            for file_key in data_files:
                try:
                    response = self.s3_client.head_object(
                        Bucket=self.aws_config.s3_bucket,
                        Key=file_key
                    )
                    
                    s3_results['data_files'][file_key] = {
                        'exists': True,
                        'size_mb': response['ContentLength'] / (1024 * 1024),
                        'last_modified': response['LastModified'].isoformat(),
                        'storage_class': response.get('StorageClass', 'STANDARD')
                    }
                
                except self.s3_client.exceptions.NoSuchKey:
                    s3_results['data_files'][file_key] = {
                        'exists': False,
                        'error': 'File not found'
                    }
                except Exception as e:
                    s3_results['data_files'][file_key] = {
                        'exists': False,
                        'error': str(e)
                    }
        
        except Exception as e:
            s3_results['error'] = str(e)
        
        return s3_results
    
    def _validate_glue_resources(self) -> Dict[str, Any]:
        """Validate AWS Glue catalog resources"""
        logger.info("Validating Glue resources...")
        
        glue_results = {
            'database': {},
            'tables': {},
            'partitions': {}
        }
        
        try:
            # Check database
            try:
                db_response = self.glue_client.get_database(Name=self.aws_config.glue_database)
                glue_results['database'] = {
                    'exists': True,
                    'name': db_response['Database']['Name'],
                    'creation_time': db_response['Database'].get('CreateTime', '').isoformat() if db_response['Database'].get('CreateTime') else None
                }
            except self.glue_client.exceptions.EntityNotFoundException:
                glue_results['database'] = {
                    'exists': False,
                    'error': 'Database not found'
                }
            
            # Check tables
            expected_tables = ['customers', 'transactions']
            
            for table_name in expected_tables:
                try:
                    table_response = self.glue_client.get_table(
                        DatabaseName=self.aws_config.glue_database,
                        Name=table_name
                    )
                    
                    table_info = table_response['Table']
                    glue_results['tables'][table_name] = {
                        'exists': True,
                        'columns': len(table_info['StorageDescriptor']['Columns']),
                        'location': table_info['StorageDescriptor']['Location'],
                        'input_format': table_info['StorageDescriptor']['InputFormat'],
                        'partition_keys': len(table_info.get('PartitionKeys', []))
                    }
                    
                    # Check partitions for partitioned tables
                    if table_info.get('PartitionKeys'):
                        try:
                            partition_response = self.glue_client.get_partitions(
                                DatabaseName=self.aws_config.glue_database,
                                TableName=table_name,
                                MaxResults=100
                            )
                            
                            glue_results['partitions'][table_name] = {
                                'count': len(partition_response['Partitions']),
                                'partitions': [p['Values'] for p in partition_response['Partitions'][:5]]  # First 5
                            }
                        except Exception as e:
                            glue_results['partitions'][table_name] = {
                                'error': str(e)
                            }
                
                except self.glue_client.exceptions.EntityNotFoundException:
                    glue_results['tables'][table_name] = {
                        'exists': False,
                        'error': 'Table not found'
                    }
                except Exception as e:
                    glue_results['tables'][table_name] = {
                        'exists': False,
                        'error': str(e)
                    }
        
        except Exception as e:
            glue_results['error'] = str(e)
        
        return glue_results
    
    def _validate_iam_permissions(self) -> Dict[str, Any]:
        """Validate IAM permissions for the project"""
        logger.info("Validating IAM permissions...")
        
        iam_results = {
            'sagemaker_role': {},
            'current_user_permissions': {}
        }
        
        try:
            iam_client = boto3.client('iam')
            
            # Check SageMaker execution role if specified
            if self.aws_config.sagemaker_role:
                try:
                    role_arn = self.aws_config.sagemaker_role
                    role_name = role_arn.split('/')[-1]
                    
                    role_response = iam_client.get_role(RoleName=role_name)
                    
                    iam_results['sagemaker_role'] = {
                        'exists': True,
                        'role_name': role_name,
                        'role_arn': role_arn,
                        'creation_date': role_response['Role']['CreateDate'].isoformat()
                    }
                    
                    # Get attached policies
                    policies_response = iam_client.list_attached_role_policies(RoleName=role_name)
                    iam_results['sagemaker_role']['attached_policies'] = [
                        p['PolicyName'] for p in policies_response['AttachedPolicies']
                    ]
                
                except Exception as e:
                    iam_results['sagemaker_role'] = {
                        'exists': False,
                        'error': str(e)
                    }
            
            # Test current user permissions
            sts_client = boto3.client('sts')
            identity = sts_client.get_caller_identity()
            
            iam_results['current_user_permissions'] = {
                'user_arn': identity['Arn'],
                'account_id': identity['Account'],
                'user_id': identity['UserId']
            }
        
        except Exception as e:
            iam_results['error'] = str(e)
        
        return iam_results
    
    def _validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data integrity across datasets"""
        logger.info("Validating data integrity...")
        
        integrity_results = {
            'referential_integrity': {},
            'data_consistency': {},
            'completeness': {}
        }
        
        try:
            # Load data from S3 for validation
            customers_path = self.aws_config.get_s3_path('raw/customers/')
            transactions_path = self.aws_config.get_s3_path('raw/transactions/')
            
            try:
                customers_df = wr.s3.read_csv(customers_path, boto3_session=self.aws_config.session)
                transactions_df = wr.s3.read_parquet(transactions_path, boto3_session=self.aws_config.session)
                
                # Check referential integrity
                customer_ids_in_customers = set(customers_df['customer_id'].unique())
                customer_ids_in_transactions = set(transactions_df['customer_id'].unique())
                
                orphaned_transactions = customer_ids_in_transactions - customer_ids_in_customers
                
                integrity_results['referential_integrity'] = {
                    'customers_count': len(customer_ids_in_customers),
                    'unique_customers_in_transactions': len(customer_ids_in_transactions),
                    'orphaned_transaction_customers': len(orphaned_transactions),
                    'integrity_score': 1 - (len(orphaned_transactions) / len(customer_ids_in_transactions)) if customer_ids_in_transactions else 1
                }
                
                # Check data consistency
                integrity_results['data_consistency'] = {
                    'customers_duplicates': customers_df['customer_id'].duplicated().sum(),
                    'transactions_nulls': transactions_df.isnull().sum().to_dict(),
                    'negative_amounts': (transactions_df['total_amount'] < 0).sum()
                }
                
                # Check completeness
                integrity_results['completeness'] = {
                    'customers_completeness': (1 - customers_df.isnull().sum() / len(customers_df)).to_dict(),
                    'transactions_completeness': (1 - transactions_df.isnull().sum() / len(transactions_df)).to_dict()
                }
            
            except Exception as e:
                integrity_results['error'] = f"Could not load data for validation: {str(e)}"
        
        except Exception as e:
            integrity_results['error'] = str(e)
        
        return integrity_results
    
    def _validate_data_schemas(self) -> Dict[str, Any]:
        """Validate data schemas match expected structure"""
        logger.info("Validating data schemas...")
        
        schema_results = {}
        
        expected_schemas = {
            'customers': {
                'customer_id': 'string',
                'age': 'int64',
                'gender': 'string',
                'location_city': 'string',
                'location_state': 'string',
                'customer_segment': 'string'
            },
            'transactions': {
                'transaction_id': 'string',
                'customer_id': 'string',
                'product_id': 'string',
                'quantity': 'int64',
                'unit_price': 'float64',
                'total_amount': 'float64'
            }
        }
        
        try:
            for dataset_name, expected_schema in expected_schemas.items():
                if dataset_name == 'customers':
                    path = self.aws_config.get_s3_path('raw/customers/')
                    df = wr.s3.read_csv(path, boto3_session=self.aws_config.session)
                elif dataset_name == 'transactions':
                    path = self.aws_config.get_s3_path('raw/transactions/')
                    df = wr.s3.read_parquet(path, boto3_session=self.aws_config.session)
                
                actual_schema = df.dtypes.to_dict()
                actual_schema = {k: str(v) for k, v in actual_schema.items()}
                
                schema_validation = {
                    'expected_columns': list(expected_schema.keys()),
                    'actual_columns': list(actual_schema.keys()),
                    'missing_columns': [col for col in expected_schema.keys() if col not in actual_schema.keys()],
                    'extra_columns': [col for col in actual_schema.keys() if col not in expected_schema.keys()],
                    'type_mismatches': []
                }
                
                for col in expected_schema.keys():
                    if col in actual_schema:
                        if expected_schema[col] not in actual_schema[col]:
                            schema_validation['type_mismatches'].append({
                                'column': col,
                                'expected': expected_schema[col],
                                'actual': actual_schema[col]
                            })
                
                schema_validation['schema_valid'] = (
                    len(schema_validation['missing_columns']) == 0 and
                    len(schema_validation['type_mismatches']) == 0
                )
                
                schema_results[dataset_name] = schema_validation
        
        except Exception as e:
            schema_results['error'] = str(e)
        
        return schema_results
    
    def _validate_data_quality(self) -> Dict[str, Any]:
        """Validate data quality metrics"""
        logger.info("Validating data quality...")
        
        quality_results = {}
        
        try:
            # Customers data quality
            customers_path = self.aws_config.get_s3_path('raw/customers/')
            customers_df = wr.s3.read_csv(customers_path, boto3_session=self.aws_config.session)
            
            quality_results['customers'] = {
                'total_records': len(customers_df),
                'duplicate_rate': customers_df['customer_id'].duplicated().sum() / len(customers_df),
                'null_rate': customers_df.isnull().sum().sum() / (len(customers_df) * len(customers_df.columns)),
                'age_outliers': ((customers_df['age'] < 18) | (customers_df['age'] > 100)).sum(),
                'data_quality_score': 0  # Will calculate below
            }
            
            # Calculate overall quality score for customers (0-1)
            quality_score = 1.0
            quality_score -= min(quality_results['customers']['duplicate_rate'], 0.1) * 5  # Penalize duplicates
            quality_score -= min(quality_results['customers']['null_rate'], 0.1) * 3      # Penalize nulls
            quality_score -= min(quality_results['customers']['age_outliers'] / len(customers_df), 0.05) * 10  # Penalize outliers
            quality_results['customers']['data_quality_score'] = max(quality_score, 0)
            
            # Transactions data quality
            transactions_path = self.aws_config.get_s3_path('raw/transactions/')
            transactions_df = wr.s3.read_parquet(transactions_path, boto3_session=self.aws_config.session)
            
            quality_results['transactions'] = {
                'total_records': len(transactions_df),
                'negative_amounts': (transactions_df['total_amount'] < 0).sum(),
                'zero_quantities': (transactions_df['quantity'] <= 0).sum(),
                'future_dates': (pd.to_datetime(transactions_df['transaction_date']) > datetime.now()).sum(),
                'null_rate': transactions_df.isnull().sum().sum() / (len(transactions_df) * len(transactions_df.columns)),
                'data_quality_score': 0
            }
            
            # Calculate quality score for transactions
            quality_score = 1.0
            quality_score -= min(quality_results['transactions']['negative_amounts'] / len(transactions_df), 0.05) * 10
            quality_score -= min(quality_results['transactions']['zero_quantities'] / len(transactions_df), 0.05) * 10
            quality_score -= min(quality_results['transactions']['null_rate'], 0.1) * 3
            quality_results['transactions']['data_quality_score'] = max(quality_score, 0)
        
        except Exception as e:
            quality_results['error'] = str(e)
        
        return quality_results
    
    def _validate_project_structure(self) -> Dict[str, Any]:
        """Validate local project structure"""
        logger.info("Validating project structure...")
        
        structure_results = {
            'directories': {},
            'files': {},
            'structure_valid': True
        }
        
        expected_structure = {
            'directories': [
                'src/data_preparation',
                'src/config',
                'src/utils',
                'data/raw',
                'data/processed',
                'data/sample',
                'notebooks'
            ],
            'files': [
                'requirements.txt',
                'src/config/aws_config.py',
                'src/data_preparation/data_ingestion.py',
                'src/utils/validation.py'
            ]
        }
        
        # Check directories
        for directory in expected_structure['directories']:
            path = Path(directory)
            structure_results['directories'][directory] = {
                'exists': path.exists() and path.is_dir(),
                'path': str(path.absolute())
            }
            if not structure_results['directories'][directory]['exists']:
                structure_results['structure_valid'] = False
        
        # Check files
        for file_path in expected_structure['files']:
            path = Path(file_path)
            structure_results['files'][file_path] = {
                'exists': path.exists() and path.is_file(),
                'size_kb': path.stat().st_size / 1024 if path.exists() else 0,
                'path': str(path.absolute())
            }
            if not structure_results['files'][file_path]['exists']:
                structure_results['structure_valid'] = False
        
        return structure_results
    
    def _validate_dependencies(self) -> Dict[str, Any]:
        """Validate Python dependencies"""
        logger.info("Validating dependencies...")
        
        deps_results = {
            'requirements_file': {},
            'installed_packages': {},
            'missing_packages': []
        }
        
        try:
            # Check requirements.txt
            req_path = Path('requirements.txt')
            if req_path.exists():
                with open(req_path, 'r') as f:
                    requirements = f.read().splitlines()
                
                deps_results['requirements_file'] = {
                    'exists': True,
                    'packages_count': len([r for r in requirements if r.strip() and not r.startswith('#')]),
                    'requirements': requirements
                }
                
                # Check if packages are installed
                import pkg_resources
                installed_packages = {pkg.project_name: pkg.version for pkg in pkg_resources.working_set}
                
                for req in requirements:
                    if req.strip() and not req.startswith('#'):
                        pkg_name = req.split('==')[0].strip()
                        if pkg_name.lower() in [p.lower() for p in installed_packages.keys()]:
                            deps_results['installed_packages'][pkg_name] = 'installed'
                        else:
                            deps_results['missing_packages'].append(pkg_name)
            else:
                deps_results['requirements_file'] = {
                    'exists': False,
                    'error': 'requirements.txt not found'
                }
        
        except Exception as e:
            deps_results['error'] = str(e)
        
        return deps_results
    
    def _validate_storage_costs(self) -> Dict[str, Any]:
        """Validate and estimate storage costs"""
        logger.info("Validating storage costs...")
        
        cost_results = {
            'storage_breakdown': {},
            'estimated_monthly_cost': 0,
            'cost_optimization_suggestions': []
        }
        
        try:
            # S3 pricing (approximate, us-east-1)
            s3_standard_price_per_gb = 0.023  # \$0.023 per GB/month
            s3_ia_price_per_gb = 0.0125       # \$0.0125 per GB/month
            
            # Get S3 usage from validation results
            if 'total_size_mb' in self.validation_results.get('s3_resources', {}):
                total_size_gb = self.validation_results['s3_resources']['total_size_mb'] / 1024
                
                cost_results['storage_breakdown'] = {
                    'total_size_gb': total_size_gb,
                    's3_standard_monthly_cost': total_size_gb * s3_standard_price_per_gb,
                    's3_ia_monthly_cost': total_size_gb * s3_ia_price_per_gb
                }
                
                cost_results['estimated_monthly_cost'] = total_size_gb * s3_standard_price_per_gb
                
                # Cost optimization suggestions
                if total_size_gb > 1:  # If more than 1GB
                    cost_results['cost_optimization_suggestions'].extend([
                        'Consider using S3 Intelligent-Tiering for automatic cost optimization',
                        'Use S3 Lifecycle policies to transition old data to cheaper storage classes'
                    ])
                
                if total_size_gb > 10:  # If more than 10GB
                    cost_results['cost_optimization_suggestions'].append(
                        'Consider data compression to reduce storage costs'
                    )
        
        except Exception as e:
            cost_results['error'] = str(e)
        
        return cost_results
    
    def _validate_performance_metrics(self) -> Dict[str, Any]:
        """Validate performance metrics"""
        logger.info("Validating performance metrics...")
        
        perf_results = {
            'ingestion_performance': {},
            'query_performance': {},
            'recommendations': []
        }
        
        try:
            # Test S3 read performance
            start_time = time.time()
            customers_path = self.aws_config.get_s3_path('raw/customers/')
            customers_df = wr.s3.read_csv(customers_path, boto3_session=self.aws_config.session)
            csv_read_time = time.time() - start_time
            
            start_time = time.time()
            transactions_path = self.aws_config.get_s3_path('raw/transactions/')
            transactions_df = wr.s3.read_parquet(transactions_path, boto3_session=self.aws_config.session)
            parquet_read_time = time.time() - start_time
            
            perf_results['ingestion_performance'] = {
                'csv_read_time_seconds': csv_read_time,
                'csv_records_per_second': len(customers_df) / csv_read_time if csv_read_time > 0 else 0,
                'parquet_read_time_seconds': parquet_read_time,
                'parquet_records_per_second': len(transactions_df) / parquet_read_time if parquet_read_time > 0 else 0
            }
            
            # Performance recommendations
            if csv_read_time > parquet_read_time * 2:
                perf_results['recommendations'].append(
                    'Consider converting CSV files to Parquet for better read performance'
                )
            
            if len(transactions_df) > 100000:
                perf_results['recommendations'].append(
                    'Consider partitioning large datasets for better query performance'
                )
        
        except Exception as e:
            perf_results['error'] = str(e)
        
        return perf_results
    
    def _generate_validation_report(self) -> None:
        """Generate comprehensive validation report"""
        logger.info("Generating validation report...")
        
        report_path = Path('validation_report.json')
        
        # Add summary
        self.validation_results['summary'] = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': self._calculate_overall_status(),
            'total_checks': self._count_total_checks(),
            'passed_checks': self._count_passed_checks(),
            'failed_checks': self._count_failed_checks()
        }
        
        # Save detailed report
        with open(report_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        logger.info(f"✅ Validation report saved to {report_path}")
        
        # Print summary
        self._print_validation_summary()
    
    def _calculate_overall_status(self) -> str:
        """Calculate overall validation status"""
        critical_checks = [
            self.validation_results['aws_access']['overall_status'],
            self.validation_results['project_structure']['structure_valid']
        ]
        
        if all(critical_checks):
            return 'PASSED'
        else:
            return 'FAILED'
    
    def _count_total_checks(self) -> int:
        """Count total validation checks"""
        return len(self.validation_results) - 1  # Exclude summary
    
    def _count_passed_checks(self) -> int:
        """Count passed validation checks"""
        passed = 0
        for key, result in self.validation_results.items():
            if key == 'summary':
                continue
            if isinstance(result, dict) and not result.get('error'):
                passed += 1
        return passed
    
    def _count_failed_checks(self) -> int:
        """Count failed validation checks"""
        return self._count_total_checks() - self._count_passed_checks()
    
    def _print_validation_summary(self) -> None:
        """Print validation summary to console"""
        print("\n" + "="*60)
        print("📋 PROJECT VALIDATION SUMMARY")
        print("="*60)
        
        summary = self.validation_results['summary']
        print(f"Overall Status: {'✅ PASSED' if summary['overall_status'] == 'PASSED' else '❌ FAILED'}")
        print(f"Total Checks: {summary['total_checks']}")
        print(f"Passed: {summary['passed_checks']}")
        print(f"Failed: {summary['failed_checks']}")
        print(f"Timestamp: {summary['timestamp']}")
        
        print("\n📊 DETAILED RESULTS:")
        for check_name, result in self.validation_results.items():
            if check_name == 'summary':
                continue
            
            status = "✅" if not result.get('error') else "❌"
            print(f"  {status} {check_name.replace('_', ' ').title()}")
            
            if result.get('error'):
                print(f"    Error: {result['error']}")

# Usage in validation script
if __name__ == "__main__":
    import sys
    sys.path.append('src')
    
    from config.aws_config import AWSConfig
    
    # Initialize
    aws_config = AWSConfig()
    validator = ProjectValidator(aws_config)
    
    # Run validation
    results = validator.validate_all()
    
    # Exit with appropriate code
    sys.exit(0 if results['summary']['overall_status'] == 'PASSED' else 1)
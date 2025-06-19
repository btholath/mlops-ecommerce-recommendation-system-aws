"""
This data ingestion module covers all the key aspects of Task Statement 1.1:

Key Features Covered:
Data Formats & Ingestion Mechanisms:
✅ CSV (customers data)
✅ JSON (products data)
✅ Parquet (transactions data)
✅ JSON Lines (clickstream data)

AWS Data Sources:
✅ Amazon S3 (primary storage)
✅ AWS Glue (data cataloging)
✅ Partitioning strategies for performance

Skills Demonstrated:
✅ Extracting data from multiple sources
✅ Choosing appropriate formats based on access patterns
✅ Merging data from multiple sources
✅ Troubleshooting capacity/scalability issues
✅ Cost/performance trade-offs in storage decisions

Real-world Exam Scenarios:
 Multiple format handling (CSV, JSON, Parquet, JSON Lines)
 Schema validation and data quality checks
 Partitioning strategies for large datasets
 Performance monitoring and optimization
 AWS Glue integration for data discovery
"""
import boto3
import pandas as pd
import json
import awswrangler as wr
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from pathlib import Path
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestion:
    """
    Handles data ingestion from multiple sources with various formats
    Covers Task Statement 1.1: Ingest and store data
    """
    
    def __init__(self, aws_config):
        self.aws_config = aws_config
        self.s3_client = aws_config.s3_client
        self.glue_client = aws_config.glue_client
        
    def generate_sample_data(self) -> None:
        """Generate sample e-commerce data for the project"""
        logger.info("Generating sample e-commerce data...")
        
        # Generate customer data (CSV format)
        customers = self._generate_customer_data()
        
        # Generate product data (JSON format) 
        products = self._generate_product_data()
        
        # Generate transaction data (Parquet format)
        transactions = self._generate_transaction_data()
        
        # Generate clickstream data (JSON Lines format)
        clickstream = self._generate_clickstream_data()
        
        # Save locally first
        self._save_sample_data_locally(customers, products, transactions, clickstream)
        
        logger.info("Sample data generated successfully")
    
    def _generate_customer_data(self) -> pd.DataFrame:
        """Generate customer data - CSV format"""
        np.random.seed(42)
        
        n_customers = 10000
        
        customers = pd.DataFrame({
            'customer_id': [f'CUST_{i:06d}' for i in range(1, n_customers + 1)],
            'age': np.random.randint(18, 80, n_customers),
            'gender': np.random.choice(['M', 'F', 'Other'], n_customers, p=[0.45, 0.45, 0.1]),
            'location_city': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'], n_customers),
            'location_state': np.random.choice(['NY', 'CA', 'IL', 'TX', 'AZ'], n_customers),
            'registration_date': pd.date_range('2020-01-01', '2023-12-31', periods=n_customers),
            'customer_segment': np.random.choice(['Premium', 'Standard', 'Basic'], n_customers, p=[0.2, 0.5, 0.3]),
            'email_domain': np.random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'company.com'], n_customers)
        })
        
        return customers
    
    def _generate_product_data(self) -> List[Dict]:
        """Generate product data - JSON format"""
        np.random.seed(42)
        
        categories = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports', 'Beauty']
        brands = ['BrandA', 'BrandB', 'BrandC', 'BrandD', 'BrandE']
        
        products = []
        for i in range(1, 5001):  # 5000 products
            product = {
                'product_id': f'PROD_{i:06d}',
                'product_name': f'Product {i}',
                'category': np.random.choice(categories),
                'subcategory': f'Sub_{np.random.randint(1, 21)}',
                'brand': np.random.choice(brands),
                'price': round(np.random.uniform(10, 500), 2),
                'rating': round(np.random.uniform(1, 5), 1),
                'num_reviews': np.random.randint(0, 1000),
                'in_stock': np.random.choice([True, False], p=[0.85, 0.15]),
                'created_date': (datetime.now() - timedelta(days=np.random.randint(1, 1095))).isoformat(),
                'attributes': {
                    'color': np.random.choice(['Red', 'Blue', 'Green', 'Black', 'White']),
                    'size': np.random.choice(['S', 'M', 'L', 'XL', 'XXL']) if np.random.random() > 0.5 else None,
                    'weight': round(np.random.uniform(0.1, 10), 2) if np.random.random() > 0.3 else None
                }
            }
            products.append(product)
        
        return products
    
    def _generate_transaction_data(self) -> pd.DataFrame:
        """Generate transaction data - Parquet format"""
        np.random.seed(42)
        
        n_transactions = 50000
        
        # Generate transaction dates with seasonal patterns
        base_date = datetime(2023, 1, 1)
        transaction_dates = []
        for _ in range(n_transactions):
            # Add some seasonality (more sales in Nov-Dec)
            month_weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2.5]
            month = np.random.choice(range(1, 13), p=np.array(month_weights)/sum(month_weights))
            day = np.random.randint(1, 29)  # Simplified to avoid month-day complications
            hour = np.random.randint(0, 24)
            transaction_dates.append(datetime(2023, month, day, hour))
        
        transactions = pd.DataFrame({
            'transaction_id': [f'TXN_{i:08d}' for i in range(1, n_transactions + 1)],
            'customer_id': [f'CUST_{np.random.randint(1, 10001):06d}' for _ in range(n_transactions)],
            'product_id': [f'PROD_{np.random.randint(1, 5001):06d}' for _ in range(n_transactions)],
            'quantity': np.random.randint(1, 6, n_transactions),
            'unit_price': np.round(np.random.uniform(10, 500, n_transactions), 2),
            'total_amount': 0,  # Will calculate below
            'discount_amount': np.round(np.random.uniform(0, 50, n_transactions), 2),
            'payment_method': np.random.choice(['Credit Card', 'Debit Card', 'PayPal', 'Bank Transfer'], n_transactions),
            'transaction_date': transaction_dates,
            'shipping_cost': np.round(np.random.uniform(0, 25, n_transactions), 2),
            'order_status': np.random.choice(['Completed', 'Pending', 'Cancelled', 'Returned'], 
                                           n_transactions, p=[0.8, 0.1, 0.05, 0.05])
        })
        
        # Calculate total amount
        transactions['total_amount'] = (transactions['quantity'] * transactions['unit_price'] 
                                      - transactions['discount_amount'] 
                                      + transactions['shipping_cost'])
        
        return transactions
    
    def _generate_clickstream_data(self) -> List[Dict]:
        """Generate clickstream data - JSON Lines format"""
        np.random.seed(42)
        
        events = ['page_view', 'product_view', 'add_to_cart', 'remove_from_cart', 'purchase']
        devices = ['desktop', 'mobile', 'tablet']
        browsers = ['Chrome', 'Firefox', 'Safari', 'Edge']
        
        clickstream = []
        for i in range(100000):  # 100k events
            event = {
                'event_id': f'EVT_{i:08d}',
                'customer_id': f'CUST_{np.random.randint(1, 10001):06d}',
                'product_id': f'PROD_{np.random.randint(1, 5001):06d}' if np.random.random() > 0.3 else None,
                'event_type': np.random.choice(events, p=[0.4, 0.3, 0.15, 0.1, 0.05]),
                'timestamp': (datetime.now() - timedelta(seconds=np.random.randint(1, 86400*30))).isoformat(),
                'session_id': f'SESS_{np.random.randint(1, 20001):06d}',
                'device_type': np.random.choice(devices),
                'browser': np.random.choice(browsers),
                'ip_address': f'{np.random.randint(1, 256)}.{np.random.randint(1, 256)}.{np.random.randint(1, 256)}.{np.random.randint(1, 256)}',
                'page_url': f'/product/{np.random.randint(1, 5001)}' if np.random.random() > 0.5 else f'/category/{np.random.randint(1, 11)}',
                'referrer': np.random.choice(['google.com', 'facebook.com', 'direct', 'email', 'ad_campaign']) if np.random.random() > 0.2 else None
            }
            clickstream.append(event)
        
        return clickstream
    
    def _save_sample_data_locally(self, customers: pd.DataFrame, products: List[Dict], 
                                 transactions: pd.DataFrame, clickstream: List[Dict]) -> None:
        """Save sample data to local directories"""
        
        # Create directories
        Path('data/raw').mkdir(parents=True, exist_ok=True)
        Path('data/sample').mkdir(parents=True, exist_ok=True)
        
        # Save customers as CSV
        customers.to_csv('data/sample/customers.csv', index=False)
        logger.info("Saved customers.csv")
        
        # Save products as JSON
        with open('data/sample/products.json', 'w') as f:
            json.dump(products, f, indent=2)
        logger.info("Saved products.json")
        
        # Save transactions as Parquet
        transactions.to_parquet('data/sample/transactions.parquet', index=False)
        logger.info("Saved transactions.parquet")
        
        # Save clickstream as JSON Lines
        with open('data/sample/clickstream.jsonl', 'w') as f:
            for event in clickstream:
                f.write(json.dumps(event) + '\n')
        logger.info("Saved clickstream.jsonl")
    
    def ingest_csv_to_s3(self, local_path: str, s3_key: str, 
                        validate_schema: bool = True) -> bool:
        """
        Ingest CSV data to S3 with validation
        Demonstrates CSV format handling and S3 storage
        """
        try:
            # Read and validate CSV
            df = pd.read_csv(local_path)
            logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
            
            if validate_schema:
                self._validate_csv_schema(df, local_path)
            
            # Upload to S3 using awswrangler for better performance
            s3_path = self.aws_config.get_s3_path(s3_key)
            wr.s3.to_csv(
                df=df,
                path=s3_path,
                index=False,
                boto3_session=self.aws_config.session
            )
            
            logger.info(f"Successfully uploaded {local_path} to {s3_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest CSV {local_path}: {str(e)}")
            return False
    
    def ingest_json_to_s3(self, local_path: str, s3_key: str, 
                         format_type: str = 'json') -> bool:
        """
        Ingest JSON data to S3
        Supports both regular JSON and JSON Lines format
        """
        try:
            s3_path = self.aws_config.get_s3_path(s3_key)
            
            if format_type == 'jsonl':
                # Handle JSON Lines format
                data = []
                with open(local_path, 'r') as f:
                    for line in f:
                        data.append(json.loads(line.strip()))
                
                # Convert to DataFrame for better S3 handling
                df = pd.json_normalize(data)
                wr.s3.to_parquet(
                    df=df,
                    path=s3_path.replace('.jsonl', '.parquet'),
                    boto3_session=self.aws_config.session
                )
                logger.info(f"Converted JSON Lines to Parquet and uploaded to S3")
                
            else:
                # Handle regular JSON
                with open(local_path, 'r') as f:
                    data = json.load(f)
                
                df = pd.json_normalize(data)
                wr.s3.to_parquet(
                    df=df,
                    path=s3_path.replace('.json', '.parquet'),
                    boto3_session=self.aws_config.session
                )
                logger.info(f"Converted JSON to Parquet and uploaded to S3")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest JSON {local_path}: {str(e)}")
            return False
    
    def ingest_parquet_to_s3(self, local_path: str, s3_key: str) -> bool:
        """
        Ingest Parquet data to S3
        Demonstrates Parquet format handling with optimizations
        """
        try:
            df = pd.read_parquet(local_path)
            s3_path = self.aws_config.get_s3_path(s3_key)
            
            # Use awswrangler for optimized Parquet upload with partitioning
            if 'transaction_date' in df.columns:
                df['year'] = pd.to_datetime(df['transaction_date']).dt.year
                df['month'] = pd.to_datetime(df['transaction_date']).dt.month
                
                wr.s3.to_parquet(
                    df=df,
                    path=s3_path,
                    partition_cols=['year', 'month'],
                    boto3_session=self.aws_config.session
                )
                logger.info(f"Uploaded partitioned Parquet to {s3_path}")
            else:
                wr.s3.to_parquet(
                    df=df,
                    path=s3_path,
                    boto3_session=self.aws_config.session
                )
                logger.info(f"Uploaded Parquet to {s3_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest Parquet {local_path}: {str(e)}")
            return False
    
    def create_glue_catalog_tables(self) -> bool:
        """
        Create Glue Catalog tables for data discovery
        Demonstrates AWS Glue integration for data cataloging
        """
        try:
            database_name = self.aws_config.glue_database
            
            # Create database if it doesn't exist
            try:
                self.glue_client.create_database(
                    DatabaseInput={'Name': database_name}
                )
                logger.info(f"Created Glue database: {database_name}")
            except self.glue_client.exceptions.AlreadyExistsException:
                logger.info(f"Glue database {database_name} already exists")
            
            # Define table schemas
            tables = [
                {
                    'name': 'customers',
                    'location': self.aws_config.get_s3_path('raw/customers/'),
                    'input_format': 'org.apache.hadoop.mapred.TextInputFormat',
                    'output_format': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
                    'serde': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe',
                    'columns': [
                        {'Name': 'customer_id', 'Type': 'string'},
                        {'Name': 'age', 'Type': 'int'},
                        {'Name': 'gender', 'Type': 'string'},
                        {'Name': 'location_city', 'Type': 'string'},
                        {'Name': 'location_state', 'Type': 'string'},
                        {'Name': 'registration_date', 'Type': 'date'},
                        {'Name': 'customer_segment', 'Type': 'string'},
                        {'Name': 'email_domain', 'Type': 'string'}
                    ]
                },
                {
                    'name': 'transactions',
                    'location': self.aws_config.get_s3_path('raw/transactions/'),
                    'input_format': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
                    'output_format': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
                    'serde': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
                    'columns': [
                        {'Name': 'transaction_id', 'Type': 'string'},
                        {'Name': 'customer_id', 'Type': 'string'},
                        {'Name': 'product_id', 'Type': 'string'},
                        {'Name': 'quantity', 'Type': 'int'},
                        {'Name': 'unit_price', 'Type': 'double'},
                        {'Name': 'total_amount', 'Type': 'double'},
                        {'Name': 'discount_amount', 'Type': 'double'},
                        {'Name': 'payment_method', 'Type': 'string'},
                        {'Name': 'transaction_date', 'Type': 'timestamp'},
                        {'Name': 'shipping_cost', 'Type': 'double'},
                        {'Name': 'order_status', 'Type': 'string'}
                    ],
                    'partition_keys': [
                        {'Name': 'year', 'Type': 'int'},
                        {'Name': 'month', 'Type': 'int'}
                    ]
                }
            ]
            
            # Create tables
            for table_def in tables:
                table_input = {
                    'Name': table_def['name'],
                    'StorageDescriptor': {
                        'Columns': table_def['columns'],
                        'Location': table_def['location'],
                        'InputFormat': table_def['input_format'],
                        'OutputFormat': table_def['output_format'],
                        'SerdeInfo': {
                            'SerializationLibrary': table_def['serde']
                        }
                    }
                }
                
                if 'partition_keys' in table_def:
                    table_input['PartitionKeys'] = table_def['partition_keys']
                
                try:
                    self.glue_client.create_table(
                        DatabaseName=database_name,
                        TableInput=table_input
                    )
                    logger.info(f"Created Glue table: {table_def['name']}")
                except self.glue_client.exceptions.AlreadyExistsException:
                    logger.info(f"Glue table {table_def['name']} already exists")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Glue catalog tables: {str(e)}")
            return False
    
    def _validate_csv_schema(self, df: pd.DataFrame, file_path: str) -> None:
        """Validate CSV schema and data quality"""
        
        if 'customers' in file_path:
            required_columns = ['customer_id', 'age', 'gender', 'location_city']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Check for duplicates
            if df['customer_id'].duplicated().any():
                raise ValueError("Duplicate customer_ids found")
            
            # Validate age range
            if (df['age'] < 0).any() or (df['age'] > 120).any():
                raise ValueError("Invalid age values found")
        
        logger.info(f"Schema validation passed for {file_path}")
    
    def ingest_all_sample_data(self) -> bool:
        """Ingest all sample data to S3"""
        try:
            # Generate sample data first
            self.generate_sample_data()
            
            # Ingest each data type
            success = True
            
            # CSV data
            success &= self.ingest_csv_to_s3('data/sample/customers.csv', 'raw/customers/customers.csv')
            
            # JSON data  
            success &= self.ingest_json_to_s3('data/sample/products.json', 'raw/products/products.json')
            
            # Parquet data
            success &= self.ingest_parquet_to_s3('data/sample/transactions.parquet', 'raw/transactions/transactions.parquet')
            
            # JSON Lines data
            success &= self.ingest_json_to_s3('data/sample/clickstream.jsonl', 'raw/clickstream/clickstream.jsonl', 'jsonl')
            
            # Create Glue catalog
            success &= self.create_glue_catalog_tables()
            
            if success:
                logger.info("All data ingestion completed successfully")
            else:
                logger.warning("Some data ingestion steps failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to ingest sample data: {str(e)}")
            return False

    def monitor_ingestion_performance(self, s3_key: str) -> Dict[str, Any]:
        """
        Monitor data ingestion performance and provide metrics
        Demonstrates troubleshooting capacity and scalability
        """
        try:
            s3_path = self.aws_config.get_s3_path(s3_key)
            
            # Get S3 object metadata
            response = self.s3_client.head_object(
                Bucket=self.aws_config.s3_bucket,
                Key=s3_key
            )
            
            metrics = {
                'file_size_mb': response['ContentLength'] / (1024 * 1024),
                'last_modified': response['LastModified'],
                'storage_class': response.get('StorageClass', 'STANDARD'),
                'server_side_encryption': response.get('ServerSideEncryption'),
                'metadata': response.get('Metadata', {})
            }
            
            logger.info(f"Ingestion metrics for {s3_key}: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get ingestion metrics: {str(e)}")
            return {}

# Usage example
if __name__ == "__main__":
    from config.aws_config import AWSConfig
    
    # Initialize
    aws_config = AWSConfig()
    ingestion = DataIngestion(aws_config)
    
    # Run data ingestion
    success = ingestion.ingest_all_sample_data()
    
    if success:
        print("✅ Data ingestion completed successfully!")
        
        # Monitor performance
        metrics = ingestion.monitor_ingestion_performance('raw/transactions/transactions.parquet')
        print(f"📊 Ingestion metrics: {metrics}")
    else:
        print("❌ Data ingestion failed!")
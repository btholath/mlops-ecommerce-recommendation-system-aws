# main.py (updated with better error handling)
import os
import sys
import yaml
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from config.aws_config import AWSConfig
from data_preparation.data_ingestion import DataIngestionPipeline
from data_preparation.data_transformation import DataTransformer
from data_preparation.data_validation import DataValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ecommerce_ml.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EcommerceMLPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, config_path: str = "config.yaml"):
        # Load environment variables
        load_dotenv()
        
        # Verify required environment variables
        required_vars = ['ML_BUCKET', 'AWS_REGION']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        # Load configuration
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using default configuration")
            self.config = self._get_default_config()
        
        # Update config with environment variables
        self.config['aws']['bucket'] = os.getenv('ML_BUCKET')
        self.config['aws']['region'] = os.getenv('AWS_REGION', 'us-east-1')
        
        # Initialize AWS configuration
        self.aws_config = AWSConfig(
            region_name=self.config['aws']['region']
        )
        
        # Initialize components
        self.data_ingestion = DataIngestionPipeline(self.aws_config)
        self.data_transformer = DataTransformer()
        self.data_validator = DataValidator()
        
        logger.info("EcommerceMLPipeline initialized successfully")
        logger.info(f"Using S3 bucket: {self.config['aws']['bucket']}")
        logger.info(f"Using AWS region: {self.config['aws']['region']}")
    
    def _get_default_config(self):
        """Return default configuration"""
        return {
            'aws': {
                'region': 'us-east-1',
                'bucket': os.getenv('ML_BUCKET', 'default-bucket')
            },
            'data': {
                'raw_data_prefix': 'raw-data',
                'processed_data_prefix': 'processed-data',
                'feature_store_prefix': 'feature-store'
            }
        }
    
    def run_data_preparation(self):
        """Execute complete data preparation pipeline"""
        logger.info("Starting data preparation pipeline...")
        
        try:
            # Step 1: Verify data availability
            logger.info("Step 1: Verifying data availability")
            self._verify_data_availability()
            
            # Step 2: Data Ingestion
            logger.info("Step 2: Data Ingestion")
            self._ingest_data()
            
            # Step 3: Data Validation
            logger.info("Step 3: Data Validation")
            self._validate_data()
            
            # Step 4: Data Transformation
            logger.info("Step 4: Data Transformation")
            self._transform_data()
            
            # Step 5: Save processed data
            logger.info("Step 5: Saving processed data")
            self._save_processed_data()
            
            logger.info("Data preparation pipeline completed successfully!")
            
        except Exception as e:
            logger.error(f"Data preparation pipeline failed: {str(e)}")
            raise
    
    def _verify_data_availability(self):
        """Verify that required data files exist in S3"""
        s3_client = self.aws_config.get_client('s3')
        bucket = self.config['aws']['bucket']
        
        required_files = [
            'raw-data/customers/customers.csv',
            'raw-data/products/products.csv',
            'raw-data/transactions/transactions.csv'
        ]
        
        missing_files = []
        
        for file_key in required_files:
            try:
                s3_client.head_object(Bucket=bucket, Key=file_key)
                logger.info(f"✓ Found: s3://{bucket}/{file_key}")
            except s3_client.exceptions.NoSuchKey:
                missing_files.append(file_key)
                logger.warning(f"✗ Missing: s3://{bucket}/{file_key}")
        
        if missing_files:
            logger.error("Missing required data files. Please run:")
            logger.error("1. python scripts/generate_sample_data.py")
            logger.error("2. python scripts/upload_sample_data.py")
            raise FileNotFoundError(f"Missing files in S3: {missing_files}")
    
    def _ingest_data(self):
        """Data ingestion step"""
        bucket = self.config['aws']['bucket']
        
        # Ingest customer data
        self.customer_data = self.data_ingestion.ingest_from_s3(
            bucket=bucket,
            prefix=f"{self.config['data']['raw_data_prefix']}/customers",
            file_format='csv'
        )
        logger.info(f"Ingested {len(self.customer_data)} customer records")
        
        # Ingest product data
        self.product_data = self.data_ingestion.ingest_from_s3(
            bucket=bucket,
            prefix=f"{self.config['data']['raw_data_prefix']}/products",
            file_format='csv'
        )
        logger.info(f"Ingested {len(self.product_data)} product records")
        
        # Ingest transaction data
        self.transaction_data = self.data_ingestion.ingest_from_s3(
            bucket=bucket,
            prefix=f"{self.config['data']['raw_data_prefix']}/transactions",
            file_format='csv'
        )
        logger.info(f"Ingested {len(self.transaction_data)} transaction records")
    
    def _validate_data(self):
        """Data validation step"""
        # Define expected schemas
        customer_schema = {
            'customer_id': 'string',
            'age': 'int',
            'gender': 'string',
            'income': 'float',
            'location': 'string',
            'registration_date': 'string'  # Will be converted to datetime later
        }
        
        product_schema = {
            'product_id': 'string',
            'category': 'string',
            'price': 'float',
            'product_description': 'string'
        }
        
        transaction_schema = {
            'transaction_id': 'string',
            'customer_id': 'string',
            'product_id': 'string',
            'transaction_amount': 'float',
            'transaction_timestamp': 'string'  # Will be converted to datetime later
        }
        
        # Check data quality
        customer_quality = self.data_validator.check_data_quality(self.customer_data)
        product_quality = self.data_validator.check_data_quality(self.product_data)
        transaction_quality = self.data_validator.check_data_quality(self.transaction_data)
        
        # Log validation results
        logger.info(f"Customer data quality score: {customer_quality['quality_score']:.2f}")
        logger.info(f"Product data quality score: {product_quality['quality_score']:.2f}")
        logger.info(f"Transaction data quality score: {transaction_quality['quality_score']:.2f}")
        
        # Store validation results
        self.validation_results = {
            'customer': customer_quality,
            'product': product_quality,
            'transaction': transaction_quality
        }
    
    def _transform_data(self):
        """Data transformation step"""
        # Clean and transform customer data
        self.customer_data_clean = self.data_transformer.clean_customer_data(
            self.customer_data.copy()
        )
        
        # Transform transaction data
        self.customer_aggregated = self.data_transformer.transform_transaction_data(
            self.transaction_data.copy()
        )
        
        # Create product features
        self.product_features = self.data_transformer.create_product_features(
            self.product_data.copy()
        )
        
        # Create interaction features
        self.interaction_features = self.data_transformer.create_interaction_features(
            self.customer_data_clean,
            self.product_features,
            self.transaction_data
        )
        
        logger.info("Data transformation completed successfully")
    
    def _save_processed_data(self):
        """Save processed data back to S3"""
        bucket = self.config['aws']['bucket']
        prefix = self.config['data']['processed_data_prefix']
        
        # Create processed data directory locally
        os.makedirs('data/processed', exist_ok=True)
        
        # Save processed datasets locally first
        datasets = {
            'customer_features.csv': self.customer_data_clean,
            'product_features.csv': self.product_features,
            'customer_aggregated.csv': self.customer_aggregated,
            'interaction_features.csv': self.interaction_features
        }
        
        s3_client = self.aws_config.get_client('s3')
        
        for filename, dataframe in datasets.items():
            local_path = f'data/processed/{filename}'
            s3_key = f'{prefix}/{filename}'
            
            # Save locally
            dataframe.to_csv(local_path, index=False)
            logger.info(f"Saved {filename} locally with {len(dataframe)} records")
            
            # Upload to S3
            try:
                s3_client.upload_file(local_path, bucket, s3_key)
                logger.info(f"Uploaded to s3://{bucket}/{s3_key}")
            except Exception as e:
                logger.error(f"Failed to upload {filename} to S3: {e}")

def main():
    """Main execution function"""
    try:
        # Initialize pipeline
        pipeline = EcommerceMLPipeline()
        
        # Run data preparation
        pipeline.run_data_preparation()
        
        logger.info("Pipeline execution completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
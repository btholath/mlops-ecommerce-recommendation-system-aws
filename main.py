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
from data_preparation.feature_store import FeatureStoreManager

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
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize AWS configuration
        self.aws_config = AWSConfig(
            region_name=self.config['aws']['region']
        )
        
        # Initialize components
        self.data_ingestion = DataIngestionPipeline(self.aws_config)
        self.data_transformer = DataTransformer()
        self.data_validator = DataValidator()
        self.feature_store_manager = FeatureStoreManager(self.aws_config)
        
        logger.info("EcommerceMLPipeline initialized successfully")
    
    def run_data_preparation(self):
        """Execute complete data preparation pipeline"""
        logger.info("Starting data preparation pipeline...")
        
        try:
            # Step 1: Data Ingestion
            logger.info("Step 1: Data Ingestion")
            self._ingest_data()
            
            # Step 2: Data Validation
            logger.info("Step 2: Data Validation")
            self._validate_data()
            
            # Step 3: Data Transformation
            logger.info("Step 3: Data Transformation")
            self._transform_data()
            
            # Step 4: Feature Store Management
            logger.info("Step 4: Feature Store Management")
            self._manage_feature_store()
            
            logger.info("Data preparation pipeline completed successfully!")
            
        except Exception as e:
            logger.error(f"Data preparation pipeline failed: {str(e)}")
            raise
    
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
            'registration_date': 'datetime'
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
            'transaction_timestamp': 'datetime'
        }
        
        # Validate schemas
        customer_validation = self.data_validator.validate_data_schema(
            self.customer_data, customer_schema
        )
        product_validation = self.data_validator.validate_data_schema(
            self.product_data, product_schema
        )
        transaction_validation = self.data_validator.validate_data_schema(
            self.transaction_data, transaction_schema
        )
        
        # Check data quality
        customer_quality = self.data_validator.check_data_quality(self.customer_data)
        product_quality = self.data_validator.check_data_quality(self.product_data)
        transaction_quality = self.data_validator.check_data_quality(self.transaction_data)
        
        # Validate business rules
        customer_business = self.data_validator.validate_business_rules(self.customer_data)
        transaction_business = self.data_validator.validate_business_rules(self.transaction_data)
        
        # Log validation results
        logger.info(f"Customer data quality score: {customer_quality['quality_score']:.2f}")
        logger.info(f"Product data quality score: {product_quality['quality_score']:.2f}")
        logger.info(f"Transaction data quality score: {transaction_quality['quality_score']:.2f}")
        
        # Store validation results
        self.validation_results = {
            'customer': {
                'schema': customer_validation,
                'quality': customer_quality,
                'business': customer_business
            },
            'product': {
                'schema': product_validation,
                'quality': product_quality
            },
            'transaction': {
                'schema': transaction_validation,
                'quality': transaction_quality,
                'business': transaction_business
            }
        }
    
    def _transform_data(self):
        """Data transformation step"""
        # Clean and transform customer data
        self.customer_data_clean = self.data_transformer.clean_customer_data(
            self.customer_data
        )
        
        # Transform transaction data
        self.customer_aggregated = self.data_transformer.transform_transaction_data(
            self.transaction_data
        )
        
        # Create product features
        self.product_features = self.data_transformer.create_product_features(
            self.product_data
        )
        
        # Create interaction features
        self.interaction_features = self.data_transformer.create_interaction_features(
            self.customer_data_clean,
            self.product_features,
            self.transaction_data
        )
        
        # Normalize numerical features
        numerical_columns = ['age', 'income', 'customer_tenure_days']
        self.customer_data_normalized = self.data_transformer.normalize_features(
            self.customer_data_clean, numerical_columns
        )
        
        logger.info("Data transformation completed successfully")
    
    def _manage_feature_store(self):
        """Feature store management step"""
        # This would typically involve creating feature groups and ingesting features
        # For demonstration purposes, we'll log the feature store operations
        
        feature_groups = [
            'customer-features',
            'product-features', 
            'interaction-features'
        ]
        
        for group in feature_groups:
            logger.info(f"Feature group {group} would be created/updated here")
        
        # In a real implementation, you would:
        # 1. Create feature group definitions
        # 2. Create the feature groups
        # 3. Ingest the transformed features
        
        logger.info("Feature store operations completed")

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
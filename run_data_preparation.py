#!/usr/bin/env python3
"""
Data Preparation Runner Script
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def main():
    print("🚀 Starting AWS ML Data Preparation...")
    
    try:
        # Import after adding to path
        print("Importing AWSConfig...")
        from config.aws_config import AWSConfig
        print("Importing DataIngestion...")
        from data_preparation.data_ingestion import DataIngestion
        
        # Initialize AWS configuration
        print("🔧 Initializing AWS configuration...")
        aws_config = AWSConfig()
        
        # Validate setup
        print("🔍 Validating AWS setup...")
        validation_results = aws_config.validate_setup()
        
        if not validation_results.get('s3_access', False):
            print("❌ S3 access validation failed. Please check your configuration.")
            return False
        
        # Initialize data ingestion
        print("📊 Initializing data ingestion...")
        ingestion = DataIngestion(aws_config)
        
        # Run data ingestion
        print("⬆️  Starting data ingestion process...")
        success = ingestion.ingest_all_sample_data()
        
        if success:
            print("✅ Data preparation completed successfully!")
            print(f"📍 Data stored in S3 bucket: {aws_config.s3_bucket}")
            print(f"📍 Glue database: {aws_config.glue_database}")
            
            # Show some metrics
            metrics = ingestion.monitor_ingestion_performance(year=2023,month=1)
            if metrics:
                print(f"📊 Sample metrics: {metrics}")
            
            return True
        else:
            print("❌ Data preparation failed!")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed:")
        print("pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error during data preparation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
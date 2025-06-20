# scripts/test_s3_read.py
import boto3
import pandas as pd
import os
from dotenv import load_dotenv
import io

load_dotenv()

def test_s3_read():
    """Test reading data from S3"""
    
    bucket_name = os.getenv('ML_BUCKET')
    s3_client = boto3.client('s3')
    
    # Test reading customers.csv
    key = 'raw-data/customers/customers.csv'
    
    try:
        print(f"Testing S3 read: s3://{bucket_name}/{key}")
        
        # Get object
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        
        # Read CSV
        df = pd.read_csv(io.BytesIO(response['Body'].read()))
        
        print(f"✅ Successfully read {len(df)} records")
        print(f"Columns: {list(df.columns)}")
        print(f"Shape: {df.shape}")
        print(f"First few rows:\n{df.head()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading from S3: {e}")
        return False

if __name__ == "__main__":
    test_s3_read()
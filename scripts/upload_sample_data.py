# scripts/upload_sample_data.py
import boto3
import os
import pandas as pd
from dotenv import load_dotenv
import sys
from pathlib import Path

# Load environment variables
load_dotenv()

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check if sample data exists
    sample_files = [
        'data/sample/customers.csv',
        'data/sample/products.csv', 
        'data/sample/transactions.csv'
    ]
    
    missing_files = []
    for file_path in sample_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing sample data files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n💡 Please run first: python scripts/generate_sample_data.py")
        return False
    
    # Check environment variables
    bucket_name = os.getenv('ML_BUCKET')
    if not bucket_name:
        print("❌ ML_BUCKET environment variable not set")
        print("💡 Please run: python scripts/setup_aws_infrastructure.py")
        return False
    
    print("✅ All prerequisites met")
    return True

def verify_aws_access():
    """Verify AWS credentials and S3 access"""
    try:
        # Check AWS credentials
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        print(f"✅ AWS Account verified: {identity['Account']}")
        
        # Check S3 access
        bucket_name = os.getenv('ML_BUCKET')
        s3_client = boto3.client('s3')
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket access verified: {bucket_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ AWS access verification failed: {e}")
        print("💡 Please check your AWS credentials: aws configure")
        return False

def upload_file_with_progress(s3_client, local_file, bucket, s3_key):
    """Upload file with progress indication"""
    try:
        # Get file size for progress
        file_size = os.path.getsize(local_file)
        
        # Read and validate the CSV file
        df = pd.read_csv(local_file)
        record_count = len(df)
        
        print(f"📤 Uploading {os.path.basename(local_file)}")
        print(f"   Records: {record_count:,}")
        print(f"   Size: {file_size:,} bytes")
        print(f"   Destination: s3://{bucket}/{s3_key}")
        
        # Upload the file
        s3_client.upload_file(local_file, bucket, s3_key)
        
        # Verify upload
        response = s3_client.head_object(Bucket=bucket, Key=s3_key)
        uploaded_size = response['ContentLength']
        
        if uploaded_size == file_size:
            print(f"   ✅ Upload successful")
            return True
        else:
            print(f"   ❌ Upload verification failed (size mismatch)")
            return False
            
    except pd.errors.EmptyDataError:
        print(f"   ❌ File is empty or invalid CSV: {local_file}")
        return False
    except pd.errors.ParserError as e:
        print(f"   ❌ CSV parsing error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return False

def create_s3_folder_structure(s3_client, bucket):
    """Ensure S3 folder structure exists"""
    print("📁 Creating S3 folder structure...")
    
    folders = [
        'raw-data/',
        'raw-data/customers/',
        'raw-data/products/',
        'raw-data/transactions/',
        'processed-data/',
        'models/',
        'feature-store/',
        'logs/'
    ]
    
    for folder in folders:
        try:
            # Create empty object to represent folder
            s3_client.put_object(
                Bucket=bucket,
                Key=folder,
                Body=b''
            )
        except Exception as e:
            print(f"   ⚠️  Warning: Could not create folder {folder}: {e}")
    
    print("   ✅ Folder structure created")

def upload_sample_data():
    """Upload generated sample data to S3"""
    
    print("🚀 Starting sample data upload to S3")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        return False
    
    # Verify AWS access
    if not verify_aws_access():
        return False
    
    bucket_name = os.getenv('ML_BUCKET')
    s3_client = boto3.client('s3')
    
    # Create folder structure
    create_s3_folder_structure(s3_client, bucket_name)
    
    # Define file mappings
    data_files = {
        'data/sample/customers.csv': 'raw-data/customers/customers.csv',
        'data/sample/products.csv': 'raw-data/products/products.csv',
        'data/sample/transactions.csv': 'raw-data/transactions/transactions.csv'
    }
    
    print(f"\n📦 Uploading {len(data_files)} files to S3...")
    print("-" * 50)
    
    uploaded_files = []
    failed_files = []
    
    for local_file, s3_key in data_files.items():
        if os.path.exists(local_file):
            success = upload_file_with_progress(s3_client, local_file, bucket_name, s3_key)
            if success:
                uploaded_files.append(s3_key)
            else:
                failed_files.append(local_file)
        else:
            print(f"❌ File not found: {local_file}")
            failed_files.append(local_file)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 UPLOAD SUMMARY")
    print("=" * 50)
    
    if uploaded_files:
        print(f"✅ Successfully uploaded {len(uploaded_files)} files:")
        for file_key in uploaded_files:
            print(f"   📄 s3://{bucket_name}/{file_key}")
    
    if failed_files:
        print(f"\n❌ Failed to upload {len(failed_files)} files:")
        for file_path in failed_files:
            print(f"   📄 {file_path}")
    
    # Verify all uploads
    if len(uploaded_files) == len(data_files):
        print(f"\n🎉 All files uploaded successfully!")
        print(f"💡 Next step: python main.py")
        
        # Optional: Show S3 bucket contents
        print(f"\n📋 Current S3 bucket structure:")
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='raw-data/',
                Delimiter='/'
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    size_mb = obj['Size'] / (1024 * 1024)
                    print(f"   📄 {obj['Key']} ({size_mb:.2f} MB)")
        except Exception as e:
            print(f"   ⚠️  Could not list bucket contents: {e}")
        
        return True
    else:
        print(f"\n⚠️  Upload incomplete. Please check errors above.")
        return False

def verify_uploaded_data():
    """Verify that uploaded data is accessible and valid"""
    print("\n🔍 Verifying uploaded data...")
    
    bucket_name = os.getenv('ML_BUCKET')
    s3_client = boto3.client('s3')
    
    files_to_verify = [
        'raw-data/customers/customers.csv',
        'raw-data/products/products.csv',
        'raw-data/transactions/transactions.csv'
    ]
    
    verification_results = []
    
    for s3_key in files_to_verify:
        try:
            # Get object metadata
            response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            size = response['ContentLength']
            last_modified = response['LastModified']
            
            print(f"   ✅ {s3_key}")
            print(f"      Size: {size:,} bytes")
            print(f"      Modified: {last_modified}")
            
            verification_results.append(True)
            
        except Exception as e:
            print(f"   ❌ {s3_key}: {e}")
            verification_results.append(False)
    
    all_verified = all(verification_results)
    
    if all_verified:
        print("\n✅ All uploaded data verified successfully!")
    else:
        print(f"\n❌ Some files failed verification")
    
    return all_verified

def show_next_steps():
    """Show next steps after successful upload"""
    print("\n" + "🎯 NEXT STEPS")
    print("=" * 50)
    print("1. Verify data in S3:")
    print(f"   aws s3 ls s3://{os.getenv('ML_BUCKET')}/raw-data/ --recursive")
    print("\n2. Run the ML pipeline:")
    print("   python main.py")
    print("\n3. Monitor progress:")
    print("   tail -f ecommerce_ml.log")
    print("\n4. Check processed data:")
    print("   ls -la data/processed/")

def main():
    """Main execution function"""
    try:
        # Upload sample data
        success = upload_sample_data()
        
        if success:
            # Verify uploaded data
            verify_uploaded_data()
            
            # Show next steps
            show_next_steps()
            
            print("\n🎉 Sample data upload completed successfully!")
        else:
            print("\n❌ Sample data upload failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
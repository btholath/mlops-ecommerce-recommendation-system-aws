# scripts/monitor_pipeline.py
import boto3
import json
from datetime import datetime, timedelta

def check_pipeline_status():
    """Monitor pipeline execution status"""
    cloudwatch = boto3.client('cloudwatch')
    
    # Check for recent errors
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    logs_client = boto3.client('logs')
    
    try:
        response = logs_client.filter_log_events(
            logGroupName='/aws/lambda/ecommerce-ml-pipeline',
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            filterPattern='ERROR'
        )
        
        if response['events']:
            print("Recent errors found:")
            for event in response['events']:
                print(f"  {event['message']}")
        else:
            print("No recent errors found")
            
    except Exception as e:
        print(f"Error checking pipeline status: {e}")

if __name__ == "__main__":
    check_pipeline_status()
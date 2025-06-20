# scripts/get_role_arn.py
import boto3
import os
from dotenv import load_dotenv

def get_role_arn():
    """Get the SageMaker role ARN and update .env"""
    load_dotenv()
    
    iam_client = boto3.client('iam')
    
    try:
        # Get existing role
        response = iam_client.get_role(RoleName='SageMakerExecutionRole')
        role_arn = response['Role']['Arn']
        print(f"SageMaker Role ARN: {role_arn}")
        
        # Update .env file
        try:
            with open('.env', 'r') as f:
                lines = f.readlines()
            
            # Update or add SAGEMAKER_ROLE
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('SAGEMAKER_ROLE='):
                    lines[i] = f'SAGEMAKER_ROLE={role_arn}\n'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'SAGEMAKER_ROLE={role_arn}\n')
            
            with open('.env', 'w') as f:
                f.writelines(lines)
            
            print("Updated .env file with correct role ARN")
            
        except Exception as e:
            print(f"Could not update .env file: {e}")
            print(f"Please manually add: SAGEMAKER_ROLE={role_arn}")
            
    except Exception as e:
        print(f"Error getting role ARN: {e}")

if __name__ == "__main__":
    get_role_arn()
import os
import logging
import boto3
from urllib.parse import urlparse
from dotenv import load_dotenv

# -----------------------------------
# Setup Logging
# -----------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s"
)

# -----------------------------------
# Load environment variables
# -----------------------------------
load_dotenv()
REGION = os.getenv("AWS_REGION", "us-east-1")
PREFIX = "sagemaker-xgboost"

# -----------------------------------
# Initialize AWS Clients
# -----------------------------------
sm_client = boto3.client("sagemaker", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)

# -----------------------------------
# Utility: Delete SageMaker Training Artifacts from S3
# -----------------------------------
def delete_s3_artifacts_from_training_job(training_job_name):
    try:
        logging.info(f"Fetching training job: {training_job_name}")
        response = sm_client.describe_training_job(TrainingJobName=training_job_name)
        model_artifact = response["ModelArtifacts"]["S3ModelArtifacts"]
        parsed = urlparse(model_artifact)
        bucket = parsed.netloc
        prefix = parsed.path.lstrip("/").split("/output")[0]
        logging.info(f"Deleting S3 contents under: s3://{bucket}/{prefix}")

        objects = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if "Contents" in objects:
            for obj in objects["Contents"]:
                s3_client.delete_object(Bucket=bucket, Key=obj["Key"])
                logging.info(f"Deleted: {obj['Key']}")
        else:
            logging.info("No objects found in S3 to delete.")
    except Exception as e:
        logging.warning(f"Failed to delete S3 artifacts: {e}")

# -----------------------------------
# Generic Deletion Functions
# -----------------------------------
def delete_resources(resource_type, list_fn, delete_fn, key_name):
    logging.info(f"Looking for {resource_type}s starting with '{PREFIX}'...")
    paginator = sm_client.get_paginator(list_fn)
    for page in paginator.paginate():
        for item in page[key_name]:
            name = item[f"{resource_type}Name"]
            if name.startswith(PREFIX):
                try:
                    logging.info(f"Deleting {resource_type}: {name}")
                    getattr(sm_client, delete_fn)(**{f"{resource_type}Name": name})
                except Exception as e:
                    logging.warning(f"Failed to delete {resource_type} {name}: {e}")

# -----------------------------------
# Cleanup all resources with PREFIX
# -----------------------------------
def cleanup_all():
    logging.info("==== SageMaker Resource Cleanup Started ====")
    delete_resources("Endpoint", "list_endpoints", "delete_endpoint", "Endpoints")
    delete_resources("EndpointConfig", "list_endpoint_configs", "delete_endpoint_config", "EndpointConfigs")
    delete_resources("Model", "list_models", "delete_model", "Models")
    delete_s3_artifacts_from_training_job("sagemaker-xgboost-2025-06-22-07-09-11-969")
    logging.info("==== SageMaker Resource Cleanup Complete ====")

# -----------------------------------
# Display Remaining Endpoints
# -----------------------------------
def show_remaining_endpoints():
    response = sm_client.list_endpoints(MaxResults=50)
    active = [ep for ep in response["Endpoints"] if ep["EndpointStatus"] != "Deleted"]
    if active:
        print("\n== Remaining Active Endpoints ==")
        for ep in active:
            print(f"- {ep['EndpointName']}: {ep['EndpointStatus']}")
    else:
        print("\n✅ All endpoints deleted.")

# -----------------------------------
# Run Cleanup
# -----------------------------------
if __name__ == "__main__":
    cleanup_all()
    show_remaining_endpoints()

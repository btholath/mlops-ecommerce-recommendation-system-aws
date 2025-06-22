"""
cleanup_ml_model_development.py

Deletes resources created by:
- train_xgboost_builtin.py (SageMaker training job and output)
- use_transcribe.py (transcription job)
- use_rekognition.py (no cleanup needed unless collections are created)
- use_translate.py, compare_models.py, interpret_shap.py do not create persistent resources
"""

import boto3
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

region = "us-east-1"
sagemaker_client = boto3.client("sagemaker", region_name=region)
s3 = boto3.resource("s3", region_name=region)
transcribe_client = boto3.client("transcribe", region_name=region)
sts = boto3.client("sts", region_name=region)
account_id = sts.get_caller_identity()["Account"]

bucket = f"sagemaker-{region}-{account_id}"
prefix = "xgboost-builtin-example"

def delete_s3_prefix(bucket_name, prefix):
    try:
        bucket = s3.Bucket(bucket_name)
        bucket.objects.filter(Prefix=prefix).delete()
        logging.info(f"Deleted S3 contents at s3://{bucket_name}/{prefix}")
    except ClientError as e:
        logging.error(f"Failed to delete S3 data: {e}")

def delete_training_jobs(prefix):
    try:
        jobs = sagemaker_client.list_training_jobs(NameContains=prefix)["TrainingJobSummaries"]
        for job in jobs:
            name = job["TrainingJobName"]
            try:
                sagemaker_client.delete_training_job(TrainingJobName=name)
                logging.info(f"Deleted SageMaker training job: {name}")
            except ClientError as e:
                logging.warning(f"Could not delete training job {name}: {e}")
    except ClientError as e:
        logging.error(f"Failed to list/delete training jobs: {e}")

def delete_transcription_job(job_name):
    try:
        transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
        logging.info(f"Deleted Transcribe job: {job_name}")
    except ClientError as e:
        logging.warning(f"Could not delete Transcribe job {job_name}: {e}")

if __name__ == "__main__":
    # Clean up SageMaker training output and jobs
    delete_s3_prefix(bucket, prefix)
    delete_training_jobs(prefix)

    # Clean up Transcribe job
    delete_transcription_job("test-transcription")

    logging.info("Cleanup complete. No persistent resources created by Translate, Rekognition, SHAP, or Scikit-learn scripts.")

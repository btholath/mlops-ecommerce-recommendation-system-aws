import os
import logging
from dotenv import load_dotenv
import boto3
import sagemaker
from sagemaker.model import Model
from sagemaker.serializers import CSVSerializer
from sagemaker.deserializers import JSONDeserializer
from datetime import datetime

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
role = os.getenv("SAGEMAKER_EXECUTION_ROLE")
if not role:
    logging.error("Missing SAGEMAKER_EXECUTION_ROLE in .env file.")
    raise SystemExit(1)

# -----------------------------------
# Initialize SageMaker session and region
# -----------------------------------
session = sagemaker.Session()
region = session.boto_region_name
sm_client = boto3.client("sagemaker", region_name=region)

# -----------------------------------
# Training job name and fetch model artifact
# -----------------------------------
training_job_name = "sagemaker-xgboost-2025-06-22-07-09-11-969"
logging.info(f"Fetching model artifacts from training job: {training_job_name}")

try:
    job_desc = sm_client.describe_training_job(TrainingJobName=training_job_name)
    model_artifact = job_desc["ModelArtifacts"]["S3ModelArtifacts"]
    logging.info(f"Model artifact found at: {model_artifact}")
except Exception as e:
    logging.error(f"Failed to describe training job: {e}")
    raise

# -----------------------------------
# Deploy SageMaker model
# -----------------------------------
image_uri = sagemaker.image_uris.retrieve("xgboost", region=region, version="1.3-1")

xgb_model = Model(
    image_uri=image_uri,
    model_data=model_artifact,
    role=role,
    sagemaker_session=session
)

endpoint_name = f"sagemaker-xgb-endpoint-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
logging.info(f"Deploying model to endpoint: {endpoint_name}")

try:
    predictor = xgb_model.deploy(
        initial_instance_count=1,
        instance_type="ml.m5.large",
        endpoint_name=endpoint_name,
        return_predictor=True
    )
    logging.info("Model successfully deployed.")
except Exception as e:
    logging.error(f"Model deployment failed: {e}")
    raise

# -----------------------------------
# Set serializers and deserializers
# -----------------------------------
predictor.serializer = CSVSerializer()
predictor.deserializer = JSONDeserializer()

# -----------------------------------
# Perform a test prediction
# -----------------------------------
test_input = "0.5,0.3,1.2,0.9,0.1"
try:
    prediction = predictor.predict(test_input)
    logging.info(f"Prediction result for input [{test_input}]: {prediction}")
except Exception as e:
    logging.error(f"Prediction failed: {e}")
    raise

# -----------------------------------
# Optional: Delete endpoint after test
# -----------------------------------
try:
    predictor.delete_endpoint()
    logging.info(f"SageMaker endpoint '{endpoint_name}' deleted.")
except Exception as e:
    logging.warning(f"Failed to delete endpoint '{endpoint_name}': {e}")

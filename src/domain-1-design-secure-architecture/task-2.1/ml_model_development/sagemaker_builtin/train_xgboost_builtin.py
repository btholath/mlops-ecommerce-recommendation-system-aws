import logging
import boto3
import sagemaker
#from sagemaker import get_execution_role
from sagemaker.inputs import TrainingInput
from sagemaker.estimator import Estimator
import os
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

session = sagemaker.Session()
region = session.boto_region_name
#role = get_execution_role()
role = os.getenv("SAGEMAKER_EXECUTION_ROLE")
bucket = session.default_bucket()
prefix = "xgboost-builtin-example"

# Upload example data
s3 = boto3.client("s3")
s3.upload_file("train.csv", bucket, f"{prefix}/train/train.csv")
logging.info(f"Uploaded training data to s3://{bucket}/{prefix}/train/train.csv")

# Setup and launch training
train_input = TrainingInput(f"s3://{bucket}/{prefix}/train", content_type="csv")
xgb = Estimator(
    image_uri=sagemaker.image_uris.retrieve("xgboost", region, "1.3-1"),
    role=role,
    instance_count=1,
    instance_type="ml.m5.large",
    volume_size=5,
    max_run=3600,
    input_mode="File",
    output_path=f"s3://{bucket}/{prefix}/output",
    sagemaker_session=session,
)

xgb.set_hyperparameters(objective="reg:squarederror", num_round=50)
logging.info("Starting SageMaker training job...")
xgb.fit({"train": train_input})
logging.info("Training job completed.")
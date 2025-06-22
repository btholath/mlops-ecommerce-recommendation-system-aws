
# ML Model Development – Task Statement 2.1

This project covers:
- SageMaker built-in algorithms
- AI services: Translate, Transcribe, Rekognition
- Model selection using scikit-learn
- Interpretability with SHAP

## Requirements
- boto3, sagemaker, scikit-learn, shap, matplotlib
- AWS CLI configured
- S3 bucket for SageMaker input/output
- IAM permissions for SageMaker, Translate, Rekognition, Transcribe

## Run Examples
- `python sagemaker_builtin/train_xgboost_builtin.py`
- `python ai_services/use_translate.py`
- `python ai_services/use_transcribe.py`
- `python ai_services/use_rekognition.py`
- `python model_selection/compare_models.py`
- `python model_interpretability/interpret_shap.py`

# Use AWS CLI to list or create a SageMaker execution role
To find your roles:
```bash
aws iam list-roles | grep SageMaker
```

# create a new SageMaker execution role with required policies:
```bash
aws iam create-role \
  --role-name sagemaker-execution-role \
  --assume-role-policy-document file://<(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "sagemaker.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }]
}
EOF
)

aws iam attach-role-policy \
  --role-name sagemaker-execution-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess
```
Required Permissions for Role
Make sure the role you're using has at least:
AmazonSageMakerFullAccess
AmazonS3FullAccess (or S3 bucket access where training data/output lives)


```bash
(.venv) @btholath ➜ .../domain-1-design-secure-architecture/task-2.1/ml_model_development/sagemaker_builtin (main) $ python train_xgboost_builtin.py 
sagemaker.config INFO - Not applying SDK defaults from location: /etc/xdg/sagemaker/config.yaml
sagemaker.config INFO - Not applying SDK defaults from location: /home/vscode/.config/sagemaker/config.yaml
2025-06-22 07:09:10,189 [INFO] Found credentials in shared credentials file: ~/.aws/credentials
2025-06-22 07:09:11,535 [INFO] Found credentials in shared credentials file: ~/.aws/credentials
2025-06-22 07:09:11,901 [INFO] Uploaded training data to s3://sagemaker-us-east-1-637423309379/xgboost-builtin-example/train/train.csv
2025-06-22 07:09:11,928 [INFO] Ignoring unnecessary instance type: None.
2025-06-22 07:09:11,969 [INFO] Starting SageMaker training job...
2025-06-22 07:09:11,969 [INFO] SageMaker Python SDK will collect telemetry to help us better understand our user's needs, diagnose issues, and deliver additional features.
To opt out of telemetry, please disable via TelemetryOptOut parameter in SDK defaults config. For more information, refer to https://sagemaker.readthedocs.io/en/stable/overview.html#configuring-and-using-defaults-with-the-sagemaker-python-sdk.
2025-06-22 07:09:11,976 [INFO] Creating training-job with name: sagemaker-xgboost-2025-06-22-07-09-11-969
2025-06-22 07:09:13 Starting - Starting the training job...
2025-06-22 07:09:28 Starting - Preparing the instances for training...
2025-06-22 07:09:50 Downloading - Downloading input data...
2025-06-22 07:10:35 Downloading - Downloading the training image...
2025-06-22 07:11:16 Training - Training image download completed. Training in progress..[2025-06-22 07:11:20.925 ip-10-0-218-90.ec2.internal:7 INFO utils.py:28] RULE_JOB_STOP_SIGNAL_FILENAME: None
[2025-06-22 07:11:20.962 ip-10-0-218-90.ec2.internal:7 INFO profiler_config_parser.py:111] User has disabled profiler.
[2025-06-22:07:11:20:INFO] Imported framework sagemaker_xgboost_container.training
[2025-06-22:07:11:20:INFO] Failed to parse hyperparameter objective value reg:squarederror to Json.
Returning the value itself
[2025-06-22:07:11:20:INFO] No GPUs detected (normal if no gpus installed)
[2025-06-22:07:11:20:INFO] Running XGBoost Sagemaker in algorithm mode
[2025-06-22:07:11:20:INFO] Determined delimiter of CSV input is ','
[2025-06-22:07:11:20:INFO] files path: /opt/ml/input/data/train
[2025-06-22:07:11:20:INFO] Determined delimiter of CSV input is ','
[2025-06-22:07:11:21:INFO] Single node training.
[2025-06-22:07:11:21:INFO] Train matrix has 5 rows and 11 columns
[2025-06-22 07:11:21.011 ip-10-0-218-90.ec2.internal:7 INFO json_config.py:92] Creating hook from json_config at /opt/ml/input/config/debughookconfig.json.
[2025-06-22 07:11:21.012 ip-10-0-218-90.ec2.internal:7 INFO hook.py:207] tensorboard_dir has not been set for the hook. SMDebug will not be exporting tensorboard summaries.
[2025-06-22 07:11:21.013 ip-10-0-218-90.ec2.internal:7 INFO hook.py:259] Saving to /opt/ml/output/tensors
[2025-06-22 07:11:21.013 ip-10-0-218-90.ec2.internal:7 INFO state_store.py:77] The checkpoint config file /opt/ml/input/config/checkpointconfig.json does not exist.
[2025-06-22:07:11:21:INFO] Debug hook created from config
[0]#011train-rmse:0.39255
[2025-06-22 07:11:21.016 ip-10-0-218-90.ec2.internal:7 INFO hook.py:428] Monitoring the collections: metrics
[2025-06-22 07:11:21.020 ip-10-0-218-90.ec2.internal:7 INFO hook.py:491] Hook is writing from the hook with pid: 7
[1]#011train-rmse:0.30834
[2]#011train-rmse:0.24231
[3]#011train-rmse:0.19052
[4]#011train-rmse:0.14987
[5]#011train-rmse:0.11796
[6]#011train-rmse:0.09289
[7]#011train-rmse:0.07318
[8]#011train-rmse:0.05768
[9]#011train-rmse:0.04549
[10]#011train-rmse:0.03589
[11]#011train-rmse:0.02833
[12]#011train-rmse:0.02238
[13]#011train-rmse:0.01768
[14]#011train-rmse:0.01398
[15]#011train-rmse:0.01106
[16]#011train-rmse:0.00875
[17]#011train-rmse:0.00693
[18]#011train-rmse:0.00549
[19]#011train-rmse:0.00435
[20]#011train-rmse:0.00345
[21]#011train-rmse:0.00273
[22]#011train-rmse:0.00217
[23]#011train-rmse:0.00172
[24]#011train-rmse:0.00137
[25]#011train-rmse:0.00109
[26]#011train-rmse:0.00086
[27]#011train-rmse:0.00068
[28]#011train-rmse:0.00054
[29]#011train-rmse:0.00054
[30]#011train-rmse:0.00053
[31]#011train-rmse:0.00053
[32]#011train-rmse:0.00053
[33]#011train-rmse:0.00053
[34]#011train-rmse:0.00053
[35]#011train-rmse:0.00053
[36]#011train-rmse:0.00053
[37]#011train-rmse:0.00053
[38]#011train-rmse:0.00053
[39]#011train-rmse:0.00053
[40]#011train-rmse:0.00053
[41]#011train-rmse:0.00053
[42]#011train-rmse:0.00053
[43]#011train-rmse:0.00053
[44]#011train-rmse:0.00053
[45]#011train-rmse:0.00053
[46]#011train-rmse:0.00053
[47]#011train-rmse:0.00053
[48]#011train-rmse:0.00053
[49]#011train-rmse:0.00053

2025-06-22 07:11:45 Uploading - Uploading generated training model
2025-06-22 07:11:45 Completed - Training job completed
Training seconds: 115
Billable seconds: 115
2025-06-22 07:12:04,299 [INFO] Training job completed.
(.venv) @btholath ➜ .../domain-1-design-secure-architecture/task-2.1/ml_model_development/sagemaker_builtin (main) $ 
```
Model artifact in S3 (s3://sagemaker-us-east-1-637423309379/xgboost-builtin-example/output/)
✅ Trained using CSV from train.csv
✅ Ready to deploy or evaluate



# Deploy and Predict (inference)
You can now deploy the trained model to a SageMaker endpoint and make predictions.

```bash
aws iam attach-role-policy \
  --role-name sagemaker-execution-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess
```

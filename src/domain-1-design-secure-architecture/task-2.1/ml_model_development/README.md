
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

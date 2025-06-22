
# ML Security Controls on AWS

This project demonstrates AWS security practices aligned with the AWS Machine Learning Engineer – Associate exam, Domain 1 Task Statement 1.3.

## Scripts Included

- **KMS**: Create and rotate keys, encrypt/decrypt data
- **S3**: Encrypt bucket, enable versioning, set lifecycle policies
- **IAM**: Key access policy
- **ACM**: Request TLS certificate
- **RDS**: Snapshot backup
- **Glue**: Classify and tag data
- **CloudWatch**: Monitor access logs

## Requirements

- Python 3.x
- boto3
- AWS CLI configured (`aws configure`)

## Run Example

```bash
cd kms
python create_key.py
```

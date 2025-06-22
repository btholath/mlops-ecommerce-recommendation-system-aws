Task Statement 1.3: Ensure data integrity and prepare data for modeling. Knowledge of:  Pre-training bias metrics for numeric, text, and image data (for example, class imbalance [CI], difference in proportions of labels [DPL])  Strategies to address CI in numeric, text, and image datasets (for example, synthetic data generation, resampling)  Techniques to encrypt data  Data classification, anonymization, and masking  Implications of compliance requirements (for example, personally identifiable information [PII], protected health information [PHI], data residency) 
Skills in:  Validating data quality (for example, by using AWS Glue DataBrew and AWS Glue Data Quality)  Identifying and mitigating sources of bias in data (for example, selection bias, measurement bias) by using AWS tools (for example, SageMaker Clarify)  Preparing data to reduce prediction bias (for example, by using dataset splitting, shuffling, and augmentation)  Configuring data to load into the model training resource (for example, Amazon EFS, Amazon FSx) 


 # single secure_arch_samples.py file that shows—in runnable code—how to implement every data-security control listed in Domain 1, Task 1.3:

✔️ Create & rotate KMS keys
✔️ Encrypt/decrypt blobs and S3 objects at-rest
✔️ Request ACM public certificates (TLS in-transit)
✔️ Apply fine-grained key policies (IAM)
✔️ Back up / replicate S3 data cross-region
✔️ Configure S3 lifecycle retention rules
✔️ Programmatic key-alias rotation

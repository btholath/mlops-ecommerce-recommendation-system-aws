
import boto3
import logging

logging.basicConfig(level=logging.INFO)
acm = boto3.client('acm')

response = acm.request_certificate(
    DomainName='example.com',
    ValidationMethod='DNS'
)
logging.info("Certificate ARN: " + response['CertificateArn'])

# setup.py
from setuptools import setup, find_packages

setup(
    name="ecommerce-ml-project",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "boto3>=1.34.0",
        "pandas>=2.1.4",
        "numpy>=1.24.3",
        "scikit-learn>=1.3.2",
        "sagemaker>=2.202.0",
    ],
    author="Your Name",
    description="E-commerce ML Recommendation System",
    python_requires=">=3.8",
)
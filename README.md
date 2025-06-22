Step-by-Step Execution Instructions
# Step 1: Clone/Create project structure
git clone <your-repo> # or create manually
cd ecommerce-ml-project

# Step 2: Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Step 3: Install dependencies
pip install -r requirements.txt
pip install -e .

# Install the missing dependency
pip install fsspec
pip install fsspec s3fs pyarrow openpyxl

# Also install s3fs for better S3 integration
pip install s3fs

# Install boto3 with pandas extras
pip install boto3[crt] pandas[all]

# Step 4: Configure AWS credentials
aws configure
# Enter your AWS Access Key ID, Secret Access Key, region, and output format

# Step 5: Set up environment variables
cp .env.example .env
# Edit .env with your actual values

# Step 6: Generate sample data
python scripts/generate_sample_data.py

# Step 7: Set up AWS infrastructure (optional, if you need to create resources)
python scripts/setup_aws_infrastructure.py

# Step 8: Upload sample data to S3
aws s3 cp data/sample/customers.csv s3://your-bucket/raw-data/customers/
aws s3 cp data/sample/products.csv s3://your-bucket/raw-data/products/
aws s3 cp data/sample/transactions.csv s3://your-bucket/raw-data/transactions/

# Step 9: Run the main pipeline
python main.py

# Step 10: Check logs
tail -f ecommerce_ml.log



# 11. Running Tests
# Run tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_data_preparation.py -v

# Run with coverage
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html


This comprehensive setup provides:

Complete project structure with proper organization
Environment configuration with AWS credentials and settings
Sample data generation for testing
AWS infrastructure setup automation
Main pipeline execution with error handling and logging
Interactive Jupyter notebooks for exploration
Testing framework with unit tests
Monitoring and logging capabilities
To get started, follow the step-by-step execution instructions. The pipeline is designed to be modular and extensible, making it easy to add new features or modify existing ones as you progress through the other domains of the ML Engineer certification.

# Data Transformation and Feature Engineering (Task Statement 1.2)
# Overview
Data transformation and feature engineering are critical steps in the machine learning pipeline that can significantly impact model performance. This involves converting raw data into a format suitable for machine learning algorithms and creating meaningful features that help models learn patterns effectively.

# Core Concepts
- 1. Data Transformation Types
    - Scaling and Normalization
    - Min-Max Scaling: Scales features to a fixed range (usually 0-1)
    - Standardization (Z-score): Centers data around mean=0, std=1
    - Robust Scaling: Uses median and IQR, less sensitive to outliers
    - Unit Vector Scaling: Scales individual samples to have unit norm
- Encoding Categorical Variables
    - One-Hot Encoding: Creates binary columns for each category
    - Label Encoding: Assigns numeric labels to categories
    - Target Encoding: Uses target variable statistics
    - Binary Encoding: Converts categories to binary representation
- Handling Skewed Data
    - Log Transformation: Reduces right skewness
    - Square Root Transformation: Mild skewness correction
    - Box-Cox Transformation: Parametric power transformation
    - Yeo-Johnson: Handles zero and negative values

Key Takeaways
Scaling is Essential: Different algorithms require different scaling approaches
Prevent Data Leakage: Always fit transformers on training data only
Domain Knowledge: Use domain expertise to create meaningful features
Pipeline Everything: Use scikit-learn pipelines for reproducible workflows
Validate Transformations: Always check the impact of transformations on model performance
Handle Missing Values: Address missing data before feature engineering
Feature Selection: Not all features improve model performance
Cross-Validation: Validate feature engineering choices using proper CV
This comprehensive approach to data transformation and feature engineering provides the foundation for building robust machine learning models that generalize well to new data.

# References
- https://dev.to/shettigarc/easy-github-codespaces-setup-your-app-postgres-and-pgadmin-3b08
# Inside the container terminal
@btholath ➜ /workspaces/mlops-ecommerce-recommendation-system-aws (main) $
# Install Docker CLI & Postgres client utilities (Debian/Ubuntu base image)
sudo apt-get update -y
sudo apt-get install -y docker.io postgresql-client
# still inside the dev-container shell
sudo apt-get update -y
sudo apt-get install -y docker-compose-plugin
# make sure the apt index is up to date
sudo apt-get update

# Docker Compose v2 (adds the `docker compose` sub-command)
sudo apt-get install -y docker-compose-plugin

# Postgres client tools (psql, pg_isready, pg_dump, etc.)
sudo apt-get install -y postgresql-client

# sanity-check
docker compose version          # → Docker Compose X.Y.Z

# ---------------------------------------
# 1. Add the Docker APT repository
# ---------------------------------------
# 0. House-keeping: make sure basic crypto utils are present
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# 1. Add Docker’s GPG key (one-time)
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 2. Add the Docker repo for your debian release (bookworm)
echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

sudo apt-get update

# Docker Compose v2 *plugin* (makes `docker compose` work)
sudo apt-get install -y docker-compose-plugin

# Postgres client utilities (psql, pg_isready, pg_dump, …)
sudo apt-get install -y postgresql-client

sudo apt-get install -y docker-compose   # installs /usr/bin/docker-compose v1.29

# stop & remove the old one
sudo docker compose -f .devcontainer/docker-compose.yml stop db
sudo docker compose -f .devcontainer/docker-compose.yml rm -f db

# bring it up again with the new port
sudo docker compose -f .devcontainer/docker-compose.yml up -d db

sudo docker exec -it 7b3c8bf4e7fa pg_isready -U user
/var/run/postgresql:5432 - accepting connections

export PGPASSWORD=pass
psql -h localhost -p 5432 -U user -d devdb


# any container that publishes 5432?
sudo docker ps --filter "publish=5432"

# or, more generally
sudo lsof -i -P -n | grep ":5432"


# Done – verify
docker compose version     # → Docker Compose version v2.x
psql     --version         # → 15.x
pg_isready --version       # → 15.x




docker --version          # should print the Docker client version
docker compose version    # same here
psql --version            # should show 15.x or 16.x
pg_isready -h localhost

docker compose ps
pg_isready -h localhost -p 5432   # → /var/run/postgresql:5432 - accepting connections
psql -h localhost -U user -d devdb


the Docker host.
Your app container and the db container sit side-by-side on the
devcontainer_backend bridge network, so they talk to each other through that
network, not through 127.0.0.1.

Think of it like this
┌─────────────┐            hostname=app  (your VS Code terminal runs here)
│ devcontainer│──bridge──▶ hostname=db   (Postgres lives here)
└─────────────┘

# [1] Connect with the service name (db)
# in the Codespace terminal (no sudo required)
export PGPASSWORD=pass
psql -h db -U user -d devdb          # ← works
Docker Compose automatically puts a DNS entry for each service on the shared network, so db resolves to the container’s IP.

# [2] Connect with the container name (also works)
psql -h devcontainer-db-1 -U user -d devdb

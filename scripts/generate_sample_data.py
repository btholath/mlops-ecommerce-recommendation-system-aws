# scripts/generate_sample_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_sample_data():
    """Generate sample data for testing"""
    
    # Set random seed for reproducibility
    np.random.seed(42)
    random.seed(42)
    
    # Generate customer data
    n_customers = 1000
    customers = []
    
    for i in range(n_customers):
        customer = {
            'customer_id': f'CUST_{i:06d}',
            'age': np.random.randint(18, 80),
            'gender': np.random.choice(['Male', 'Female', 'Other']),
            'income': np.random.normal(50000, 15000),
            'location': np.random.choice(['New York', 'California', 'Texas', 'Florida', 'Illinois']),
            'registration_date': datetime.now() - timedelta(days=np.random.randint(1, 1000))
        }
        customers.append(customer)
    
    customer_df = pd.DataFrame(customers)
    
    # Generate product data
    categories = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports']
    n_products = 500
    products = []
    
    for i in range(n_products):
        product = {
            'product_id': f'PROD_{i:06d}',
            'category': np.random.choice(categories),
            'price': np.random.uniform(10, 500),
            'product_description': f'Sample product description for product {i}'
        }
        products.append(product)
    
    product_df = pd.DataFrame(products)
    
    # Generate transaction data
    n_transactions = 5000
    transactions = []
    
    for i in range(n_transactions):
        transaction = {
            'transaction_id': f'TXN_{i:08d}',
            'customer_id': np.random.choice(customer_df['customer_id']),
            'product_id': np.random.choice(product_df['product_id']),
            'transaction_amount': np.random.uniform(10, 300),
            'transaction_timestamp': datetime.now() - timedelta(days=np.random.randint(1, 365))
        }
        transactions.append(transaction)
    
    transaction_df = pd.DataFrame(transactions)
    
    # Create data directories
    os.makedirs('data/sample', exist_ok=True)
    
    # Save sample data
    customer_df.to_csv('data/sample/customers.csv', index=False)
    product_df.to_csv('data/sample/products.csv', index=False)
    transaction_df.to_csv('data/sample/transactions.csv', index=False)
    
    print("Sample data generated successfully!")
    print(f"Customers: {len(customer_df)}")
    print(f"Products: {len(product_df)}")
    print(f"Transactions: {len(transaction_df)}")

if __name__ == "__main__":
    generate_sample_data()
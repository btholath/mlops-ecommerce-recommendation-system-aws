# src/data_preparation/data_transformation.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
import boto3
import json
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class DataTransformer:
    """
    Comprehensive data transformation pipeline for e-commerce recommendation system
    """
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.vectorizers = {}
        
    def clean_customer_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess customer data
        """
        logger.info("Starting customer data cleaning")
        
        # Handle missing values
        df['age'] = df['age'].fillna(df['age'].median())
        df['income'] = df['income'].fillna(df['income'].median())
        df['registration_date'] = pd.to_datetime(df['registration_date'])
        
        # Create customer tenure feature
        df['customer_tenure_days'] = (
            datetime.now() - df['registration_date']
        ).dt.days
        
        # Clean categorical data
        df['gender'] = df['gender'].fillna('Unknown')
        df['location'] = df['location'].fillna('Unknown')
        
        # Remove outliers (basic approach)
        q1_age = df['age'].quantile(0.25)
        q3_age = df['age'].quantile(0.75)
        iqr_age = q3_age - q1_age
        df = df[
            (df['age'] >= q1_age - 1.5 * iqr_age) & 
            (df['age'] <= q3_age + 1.5 * iqr_age)
        ]
        
        logger.info(f"Customer data cleaning completed. Shape: {df.shape}")
        return df
    
    def transform_transaction_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Transform transaction/purchase data
        """
        logger.info("Starting transaction data transformation")
        
        # Convert timestamps
        df['transaction_timestamp'] = pd.to_datetime(df['transaction_timestamp'])
        df['transaction_date'] = df['transaction_timestamp'].dt.date
        
        # Create time-based features
        print("df['transaction_timestamp'] = ", df['transaction_timestamp'] )
        df['hour_of_day'] = df['transaction_timestamp'].dt.hour
        df['day_of_week'] = df['transaction_timestamp'].dt.dayofweek
        df['month'] = df['transaction_timestamp'].dt.month
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Calculate recency features
        max_date = df['transaction_timestamp'].max()
        df['days_since_transaction'] = (
            max_date - df['transaction_timestamp']
        ).dt.days
        
        # Aggregate customer-level features
        customer_agg = df.groupby('customer_id').agg({
            'transaction_amount': ['sum', 'mean', 'count', 'std'],
            'days_since_transaction': 'min',
            'product_id': 'nunique'
        }).reset_index()
        
        # Flatten column names
        customer_agg.columns = [
            'customer_id', 'total_spent', 'avg_transaction_amount',
            'transaction_count', 'transaction_amount_std',
            'recency_days', 'unique_products_purchased'
        ]
        
        # Fill NaN values
        customer_agg['transaction_amount_std'] = customer_agg[
            'transaction_amount_std'
        ].fillna(0)
        
        logger.info(f"Transaction transformation completed. Shape: {customer_agg.shape}")
        logger.info(f"Transaction transformation completed. Shape: {customer_agg.shape}")
        return customer_agg, df

    
    def create_product_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create product-level features
        """
        logger.info("Creating product features")
        
        # Text preprocessing for product descriptions
        if 'product_description' in df.columns:
            # Basic text cleaning
            df['product_description'] = df['product_description'].fillna('')
            df['description_length'] = df['product_description'].str.len()
            df['description_word_count'] = df['product_description'].str.split().str.len()
            
            # TF-IDF vectorization (limited features for demo)
            tfidf = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            tfidf_features = tfidf.fit_transform(df['product_description'])
            tfidf_df = pd.DataFrame(
                tfidf_features.toarray(),
                columns=[f'tfidf_{i}' for i in range(100)]
            )
            
            df = pd.concat([df.reset_index(drop=True), tfidf_df], axis=1)
            self.vectorizers['product_tfidf'] = tfidf
        
        # Price-based features
        if 'price' in df.columns:
            df['price_log'] = np.log1p(df['price'])
            df['price_category'] = pd.cut(
                df['price'], 
                bins=[0, 25, 100, 500, float('inf')],
                labels=['low', 'medium', 'high', 'premium']
            )
        
        # Category encoding
        if 'category' in df.columns:
            le_category = LabelEncoder()
            df['category_encoded'] = le_category.fit_transform(df['category'])
            self.encoders['category'] = le_category
        
        logger.info(f"Product features created. Shape: {df.shape}")
        return df
    
    def create_interaction_features(self, customer_df: pd.DataFrame, 
                                  product_df: pd.DataFrame,
                                  transaction_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create customer-product interaction features
        """
        logger.info("Creating interaction features")
        
        # Customer-product interaction matrix
        interaction_features = []
        
        for _, customer in customer_df.iterrows():
            customer_id = customer['customer_id']
            customer_transactions = transaction_df[
                transaction_df['customer_id'] == customer_id
            ]
            
            if len(customer_transactions) == 0:
                continue
            
            # Customer behavior features
            features = {
                'customer_id': customer_id,
                'avg_days_between_purchases': 0,
                'preferred_category': None,
                'avg_price_range': customer_transactions['transaction_amount'].mean(),
                'purchase_frequency': len(customer_transactions),
                'seasonal_preference': customer_transactions['month'].mode().iloc[0] if len(customer_transactions) > 0 else 1
            }
            
            # Calculate days between purchases
            if len(customer_transactions) > 1:
                transaction_dates = sorted(customer_transactions['transaction_timestamp'])
                date_diffs = [(transaction_dates[i] - transaction_dates[i-1]).days 
                             for i in range(1, len(transaction_dates))]
                features['avg_days_between_purchases'] = np.mean(date_diffs)
            
            interaction_features.append(features)
        
        interaction_df = pd.DataFrame(interaction_features)
        logger.info(f"Interaction features created. Shape: {interaction_df.shape}")
        
        return interaction_df
    
    def normalize_features(self, df: pd.DataFrame, 
                          numerical_columns: List[str]) -> pd.DataFrame:
        """
        Normalize numerical features
        """
        logger.info("Normalizing numerical features")
        
        for col in numerical_columns:
            if col in df.columns:
                scaler = StandardScaler()
                df[f'{col}_normalized'] = scaler.fit_transform(df[[col]])
                self.scalers[col] = scaler
        
        return df
    
    def handle_missing_values(self, df: pd.DataFrame, 
                            strategy: Dict[str, str] = None) -> pd.DataFrame:
        """
        Comprehensive missing value handling
        """
        logger.info("Handling missing values")
        
        if strategy is None:
            strategy = {
                'numerical': 'median',
                'categorical': 'mode',
                'text': 'empty_string'
            }
        
        for column in df.columns:
            if df[column].isnull().sum() > 0:
                if df[column].dtype in ['int64', 'float64']:
                    if strategy['numerical'] == 'median':
                        df[column].fillna(df[column].median(), inplace=True)
                    elif strategy['numerical'] == 'mean':
                        df[column].fillna(df[column].mean(), inplace=True)
                elif df[column].dtype == 'object':
                    if strategy['categorical'] == 'mode':
                        mode_value = df[column].mode()
                        if len(mode_value) > 0:
                            df[column].fillna(mode_value.iloc[0], inplace=True)
                    elif strategy['text'] == 'empty_string':
                        df[column].fillna('', inplace=True)
        
        logger.info("Missing value handling completed")
        return df
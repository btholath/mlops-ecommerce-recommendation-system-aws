# src/feature/advanced_transformation_techniques/custom_transformers.py

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample DataFrame for demo purposes
def generate_sample_data(n_samples=1000) -> pd.DataFrame:
    np.random.seed(42)
    return pd.DataFrame({
        'age': np.random.normal(35, 10, n_samples),
        'income': np.random.exponential(50000, n_samples),
        'credit_score': np.random.normal(650, 100, n_samples),
        'category': np.random.choice(['A', 'B', 'C', 'D'], n_samples)
    })

# Custom Transformer to cap outliers
class OutlierCapper(BaseEstimator, TransformerMixin):
    """Cap outliers at specified percentiles"""
    def __init__(self, lower_percentile=5, upper_percentile=95):
        self.lower_percentile = lower_percentile
        self.upper_percentile = upper_percentile

    def fit(self, X, y=None):
        self.lower_bounds_ = np.percentile(X, self.lower_percentile, axis=0)
        self.upper_bounds_ = np.percentile(X, self.upper_percentile, axis=0)
        return self

    def transform(self, X):
        return np.clip(X, self.lower_bounds_, self.upper_bounds_)


# Custom Transformer to create interaction features
class FeatureInteraction(BaseEstimator, TransformerMixin):
    """Create interaction features between specified pairs of columns"""
    def __init__(self, feature_pairs):
        self.feature_pairs = feature_pairs

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        for col1, col2 in self.feature_pairs:
            X[f"{col1}_{col2}_interaction"] = X[col1] * X[col2]
        return X


if __name__ == "__main__":
    # Generate sample data
    df = generate_sample_data()

    # Define feature sets
    numerical_features = ['age', 'income', 'credit_score']
    categorical_features = ['category']

    logger.info("Building preprocessing pipeline...")

    # Define pipelines
    numerical_transformer = Pipeline(steps=[
        ('outlier_capper', OutlierCapper(lower_percentile=5, upper_percentile=95)),
        ('scaler', StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
    ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    # Combine transformers
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_features),
            ('cat', categorical_transformer, categorical_features)
        ]
    )

    # Apply transformation
    X_preprocessed = preprocessor.fit_transform(df[numerical_features + categorical_features])

    logger.info(f"✅ Original shape: {df[numerical_features + categorical_features].shape}")
    logger.info(f"✅ Transformed shape: {X_preprocessed.shape}")

2. Feature Engineering Pipeline
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import FunctionTransformer

def create_ratio_features(X):
    """Create ratio-based features"""
    X_new = X.copy()
    X_new['age_income_ratio'] = X_new['age'] / (X_new['income'] / 1000 + 1)
    X_new['credit_age_product'] = X_new['credit_score'] * X_new['age']
    return X_new

def create_binned_features(X):
    """Create binned versions of continuous features"""
    X_new = X.copy()
    X_new['age_binned'] = pd.cut(X_new['age'], bins=5, labels=False)
    X_new['income_binned'] = pd.qcut(X_new['income'], q=4, labels=False, duplicates='drop')
    return X_new

# Create feature engineering pipeline
feature_engineering_pipeline = Pipeline([
    ('ratio_features', FunctionTransformer(create_ratio_features, validate=False)),
    ('binned_features', FunctionTransformer(create_binned_features, validate=False)),
    ('scaler', StandardScaler())
])

# Apply pipeline
X_engineered = feature_engineering_pipeline.fit_transform(X)
print(f"Feature engineered shape: {X_engineered.shape}")
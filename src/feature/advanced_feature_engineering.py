import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import PolynomialFeatures
import logging
import warnings
import os

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_polynomial_features(df: pd.DataFrame, cols: list, degree: int = 2, interaction_only: bool = True) -> pd.DataFrame:
    logger.info("Generating polynomial features")
    poly = PolynomialFeatures(degree=degree, include_bias=False, interaction_only=interaction_only)
    poly_array = poly.fit_transform(df[cols])
    poly_names = poly.get_feature_names_out(cols)
    
    df_poly = pd.DataFrame(poly_array, columns=poly_names, index=df.index)
    logger.debug(f"Polynomial features created: {poly_names}")
    return pd.concat([df, df_poly], axis=1)


def apply_binning(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Applying binning to age and income")
    df['age_bins'] = pd.cut(df['age'], bins=5, labels=['Very Young', 'Young', 'Middle', 'Mature', 'Senior'])
    df['income_quartiles'] = pd.qcut(df['income'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
    return df


def apply_log_transform(df: pd.DataFrame, column: str = 'income') -> pd.DataFrame:
    logger.info("Applying log transformation to income")
    df['income_log'] = np.log1p(df[column])  # Handles zeros
    return df


def create_feature_interactions(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Creating interaction features")
    df['age_income_ratio'] = df['age'] / (df['income'] / 1000 + 1e-9)  # prevent division by zero
    df['credit_age_interaction'] = df['credit_score'] * df['age']
    return df

def visualize_transformations(df: pd.DataFrame, save_dir: str = "src/feature", filename: str = "feature_transformations.png"):
    logger.info("Visualizing and saving feature transformations")

    # Ensure the directory exists
    os.makedirs(save_dir, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Original income distribution
    axes[0].hist(df['income'], bins=50, alpha=0.7)
    axes[0].set_title('Original Income Distribution')
    axes[0].set_xlabel('Income')

    # Log transformed income
    axes[1].hist(df['income_log'], bins=50, alpha=0.7, color='orange')
    axes[1].set_title('Log Transformed Income')
    axes[1].set_xlabel('Log(Income + 1)')

    # Binned age
    df['age_bins'].value_counts().plot(kind='bar', ax=axes[2])
    axes[2].set_title('Age Distribution (Binned)')
    axes[2].set_xlabel('Age Bins')
    axes[2].tick_params(axis='x', rotation=45)

    plt.tight_layout()

    # Save to file
    file_path = os.path.join(save_dir, filename)
    plt.savefig(file_path)
    plt.close()

    logger.info(f"Saved transformation chart to {file_path}")



def run_advanced_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df = generate_polynomial_features(df, ['age', 'credit_score'])
    df = apply_binning(df)
    df = apply_log_transform(df)
    df = create_feature_interactions(df)
    visualize_transformations(df)
    logger.info("Advanced feature engineering complete")
    return df


# Entry point for testing
if __name__ == "__main__":
    # Sample data (replace with real data as needed)
    np.random.seed(42)
    sample_data = {
        'age': np.random.normal(35, 10, 1000),
        'income': np.random.exponential(50000, 1000),
        'credit_score': np.random.normal(650, 100, 1000)
    }
    df_sample = pd.DataFrame(sample_data)

    df_transformed = run_advanced_feature_engineering(df_sample)

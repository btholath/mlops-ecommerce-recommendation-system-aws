import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
import matplotlib.pyplot as plt

def generate_sample_data(seed=42, size=1000):
    np.random.seed(seed)
    return pd.DataFrame({
        'age': np.random.normal(35, 10, size),
        'income': np.random.exponential(50000, size),
        'credit_score': np.random.normal(650, 100, size),
        'category': np.random.choice(['A', 'B', 'C', 'D'], size),
        'target': np.random.binomial(1, 0.3, size)
    })

def apply_scalers(df: pd.DataFrame, columns: list) -> dict:
    """Apply various scalers and return a dict of scaled DataFrames"""
    scalers = {
        'Standard': StandardScaler(),
        'MinMax': MinMaxScaler(),
        'Robust': RobustScaler()
    }
    
    scaled_dfs = {}
    for name, scaler in scalers.items():
        df_scaled = df.copy()
        df_scaled[columns] = scaler.fit_transform(df[columns])
        scaled_dfs[name] = df_scaled
    
    return scaled_dfs

def plot_scaling_comparison(original_df: pd.DataFrame, scaled_dfs: dict, column: str, save_path: str = None):
    """Plot histogram comparisons for a given column across scaled DataFrames and optionally save it."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.ravel()

    # Plot original
    original_df[column].hist(bins=50, ax=axes[0], alpha=0.7)
    axes[0].set_title(f'Original {column} Distribution')
    axes[0].set_xlabel(column)

    # Plot scaled versions
    for i, (name, df_scaled) in enumerate(scaled_dfs.items(), start=1):
        df_scaled[column].hist(bins=50, ax=axes[i], alpha=0.7)
        axes[i].set_title(f'{name} Scaled {column}')
        axes[i].set_xlabel(f'{name} Scaled {column}')

    plt.tight_layout()

    # Save if path is provided
    if save_path:
        plt.savefig('src/feature/'+save_path)
        print(f"✅ Diagram saved to {save_path}")

    plt.show()


def main():
    df = generate_sample_data()
    numerical_cols = ['age', 'income', 'credit_score']
    scaled_dfs = apply_scalers(df, numerical_cols)
    
    # Save the diagram as a PNG
    plot_scaling_comparison(df, scaled_dfs, column='income', save_path='scaling_comparison.png')


if __name__ == "__main__":
    main()

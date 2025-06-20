import numpy as np
import pandas as pd
import logging
from sklearn.feature_selection import (
    SelectKBest, f_classif, RFE, SelectFromModel, mutual_info_classif
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_sample_data(n_samples=1000) -> pd.DataFrame:
    """Generate sample dataset for feature selection demonstration."""
    np.random.seed(42)
    data = {
        'age': np.random.normal(35, 10, n_samples),
        'income': np.random.exponential(50000, n_samples),
        'credit_score': np.random.normal(650, 100, n_samples),
        'category_label': np.random.choice([0, 1, 2, 3], n_samples),
        'category_target': np.random.uniform(0, 1, n_samples),
        'target': np.random.binomial(1, 0.3, n_samples)
    }
    logger.info("Sample data generated")
    return pd.DataFrame(data)


def perform_feature_selection(df: pd.DataFrame):
    """Apply multiple feature selection techniques and log results."""
    X = df[['age', 'income', 'credit_score', 'category_label', 'category_target']].copy()
    y = df['target']

    # Handle missing values
    X = X.fillna(X.mean())

    logger.info("Performing Univariate Feature Selection (ANOVA)")
    selector_univariate = SelectKBest(score_func=f_classif, k=3)
    X_selected_univariate = selector_univariate.fit_transform(X, y)
    selected_features_univariate = X.columns[selector_univariate.get_support()].tolist()

    logger.info("Performing Recursive Feature Elimination (RFE)")
    estimator = LogisticRegression(random_state=42, max_iter=1000)
    selector_rfe = RFE(estimator, n_features_to_select=3)
    X_selected_rfe = selector_rfe.fit_transform(X, y)
    selected_features_rfe = X.columns[selector_rfe.get_support()].tolist()

    logger.info("Performing Feature Selection with Tree-Based Model")
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    selector_tree = SelectFromModel(rf, threshold='median')
    X_selected_tree = selector_tree.fit_transform(X, y)
    selected_features_tree = X.columns[selector_tree.get_support()].tolist()

    logger.info("Computing Mutual Information Scores")
    mi_scores = mutual_info_classif(X, y, random_state=42)
    mi_results = pd.DataFrame({
        'feature': X.columns,
        'mi_score': mi_scores
    }).sort_values('mi_score', ascending=False)

    # Display results
    print("\n📊 Feature Selection Results:")
    print(f"✔️ Univariate Selection: {selected_features_univariate}")
    print(f"✔️ RFE Selection: {selected_features_rfe}")
    print(f"✔️ Tree-based Selection: {selected_features_tree}")

    print("\n📈 Mutual Information Scores:")
    print(mi_results.to_string(index=False))


if __name__ == "__main__":
    df = generate_sample_data()
    perform_feature_selection(df)

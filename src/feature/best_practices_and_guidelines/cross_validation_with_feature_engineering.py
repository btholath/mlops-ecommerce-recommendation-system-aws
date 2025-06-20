
3. Cross-Validation with Feature Engineering
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline

# Complete pipeline with feature engineering and model
complete_pipeline = Pipeline([
    ('feature_engineering', feature_engineering_pipeline),
    ('classifier', LogisticRegression(random_state=42))
])

# Cross-validation
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(complete_pipeline, X, y, cv=cv, scoring='accuracy')

print(f"Cross-validation scores: {cv_scores}")
print(f"Mean CV accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
1. Data Leakage Prevention
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression

# Correct way: Fit transformers only on training data
X = df[['age', 'income', 'credit_score']].fillna(0)
y = df['target']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# CORRECT: Fit scaler on training data only
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)  # Only transform, don't fit

# Train model
model = LogisticRegression(random_state=42)
model.fit(X_train_scaled, y_train)

# Evaluate
y_pred = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
print(f"Correct approach accuracy: {accuracy:.3f}")

# INCORRECT example (for demonstration)
# This would cause data leakage:
# X_scaled_wrong = scaler.fit_transform(X)  # Fitting on entire dataset
# X_train_wrong, X_test_wrong, y_train, y_test = train_test_split(X_scaled_wrong, y, test_size=0.2)
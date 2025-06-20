import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from category_encoders import TargetEncoder, BinaryEncoder

# Sample dataset
np.random.seed(42)
data = {
    'category': np.random.choice(['A', 'B', 'C', 'D'], 100),
    'target': np.random.binomial(1, 0.3, 100)
}
df = pd.DataFrame(data)

# Original categorical data
print("Original categories:\n", df['category'].value_counts())

# 1. Label Encoding
label_encoder = LabelEncoder()
df['category_label'] = label_encoder.fit_transform(df['category'])

# 2. One-Hot Encoding
df_onehot = pd.get_dummies(df, columns=['category'], prefix='category')

# 3. Target Encoding
target_encoder = TargetEncoder()
df['category_target'] = target_encoder.fit_transform(df['category'], df['target'])

# 4. Binary Encoding
binary_encoder = BinaryEncoder()
df_binary = binary_encoder.fit_transform(df['category'])
df = pd.concat([df, df_binary], axis=1)

# Output encoding results
print("\nEncoding Results:")
print("Label Encoded:\n", df[['category', 'category_label']].drop_duplicates())
print("Target Encoded (sample):\n", df[['category', 'category_target']].head())
print("Binary Encoded columns:\n", df_binary.head())

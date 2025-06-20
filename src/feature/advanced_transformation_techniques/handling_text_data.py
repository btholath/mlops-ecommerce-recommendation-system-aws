
#Handling Text Data
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import normalize
import re

# Sample text data
text_data = [
    "Machine learning is fascinating and powerful",
    "Data science requires statistical knowledge",
    "Python is great for data analysis",
    "Statistical learning theory is important",
    "Feature engineering improves model performance"
]

# Text preprocessing function
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

# Apply preprocessing
clean_text = [preprocess_text(text) for text in text_data]

# 1. Bag of Words
count_vectorizer = CountVectorizer(max_features=100, stop_words='english')
bow_features = count_vectorizer.fit_transform(clean_text)

# 2. TF-IDF
tfidf_vectorizer = TfidfVectorizer(max_features=100, stop_words='english', ngram_range=(1, 2))
tfidf_features = tfidf_vectorizer.fit_transform(clean_text)

print("Text Feature Extraction:")
print(f"Vocabulary size (BoW): {len(count_vectorizer.vocabulary_)}")
print(f"Vocabulary size (TF-IDF): {len(tfidf_vectorizer.vocabulary_)}")
print(f"Feature matrix shape: {tfidf_features.shape}")
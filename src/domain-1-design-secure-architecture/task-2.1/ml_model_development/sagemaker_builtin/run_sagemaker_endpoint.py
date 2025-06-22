from sagemaker.predictor import Predictor
from sagemaker.serializers import CSVSerializer
from sagemaker.deserializers import JSONDeserializer

# Replace with your actual endpoint name
endpoint_name = "sagemaker-xgboost-2025-06-22-07-18-06-675"  # your-endpoint-name

predictor = Predictor(
    endpoint_name=endpoint_name,
    serializer=CSVSerializer(),
    deserializer=JSONDeserializer()
)

# Example test input: match the feature format used in training
response = predictor.predict("0.5,0.3,1.2,0.9,0.1")
print("Prediction:", response)

import logging
import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

rekognition = boto3.client("rekognition")

with open("image.jpg", "rb") as image_file:
    response = rekognition.detect_labels(Image={"Bytes": image_file.read()}, MaxLabels=5)

for label in response["Labels"]:
    logging.info(f"{label['Name']}: {label['Confidence']:.2f}%")
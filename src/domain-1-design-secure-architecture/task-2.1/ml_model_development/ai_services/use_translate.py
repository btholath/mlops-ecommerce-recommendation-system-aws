import logging
import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

translate = boto3.client("translate")

text = "Hello, how are you?"
response = translate.translate_text(
    Text=text,
    SourceLanguageCode="en",
    TargetLanguageCode="fr"
)

logging.info(f"Original: {text}")
logging.info(f"Translated: {response['TranslatedText']}")
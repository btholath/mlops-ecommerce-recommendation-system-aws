import logging
import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

transcribe = boto3.client("transcribe")

job_name = "test-transcription"
job_uri = "s3://your-audio-bucket/sample.wav"

logging.info(f"Starting Transcription Job: {job_name}")
transcribe.start_transcription_job(
    TranscriptionJobName=job_name,
    Media={"MediaFileUri": job_uri},
    MediaFormat="wav",
    LanguageCode="en-US"
)
logging.info("Transcription job started.")
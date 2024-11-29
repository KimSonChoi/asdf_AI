import boto3
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

def connect_s3():
    endpoint_url = os.getenv('NCP_STORAGE_ENDPOINT')
    access_key = os.getenv('NCP_STORAGE_ACCESS_KEY')
    secret_key = os.getenv('NCP_STORAGE_SECRET_KEY')
    s3 = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    bucket_name = os.getenv("NCP_STORAGE_BUCKET_NAME")
    logger.info("S3 connected")
    return s3, bucket_name

def upload_file_to_s3(s3, BUCKET_NAME, file_path, object_path):
    s3.upload_file(file_path, BUCKET_NAME, object_path, ExtraArgs={'ACL':'public-read'})

def download_file_from_s3(s3, BUCKET_NAME, object_path, file_path):
    s3.download_file(BUCKET_NAME, object_path, file_path)
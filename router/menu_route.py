from fastapi import APIRouter, Depends, HTTPException
import os, sys, time
from loguru import logger
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
sys.path.append(r'../')

from ksc_AI.models.image import Image
from ksc_AI.utils.local_storage import connect_s3, upload_file_to_s3, download_file_from_s3
from ksc_AI.utils.clova_ocr import image_to_df, image_figure

menu_router = APIRouter()

DATA_DIR = os.getenv('DATA_DIR')
OCR_DATA_DIR = os.getenv('OCR_DATA_DIR')

s3 = None
BUCKET_NAME = None

def get_connect_s3():
    global s3, BUCKET_NAME
    if s3 is None:
        s3, BUCKET_NAME = connect_s3()

@menu_router.post("")
async def ocr_upload(image: Image = Depends()):
    result_dir = os.getenv('RESULT_DIR')
    image = image.model_dump()

    image_key = image['key'].split('/')[-1].split('.')[0]
    logger.info(f"Image key: {image_key}")
    file_path = os.path.join(OCR_DATA_DIR, f'{image_key}.jpg')
    result_path = os.path.join(OCR_DATA_DIR, f'{image_key}_result.jpg')
    download_file_from_s3(s3, BUCKET_NAME, image['key'], file_path)
    ocr_df = image_to_df(image_key)
    image_figure(ocr_df, image_key)
    upload_file_to_s3(s3, BUCKET_NAME, result_path, f'{result_dir}{image_key}_result.jpg')
    return {"message": "Image uploaded"}

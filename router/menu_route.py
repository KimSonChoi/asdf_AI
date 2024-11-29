from fastapi import APIRouter, Depends, HTTPException
import os, sys, time
from loguru import logger
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_models.image import Image
from utils.local_storage import connect_s3, upload_file_to_s3, download_file_from_s3
from utils.clova_ocr import image_to_df, image_figure, matching_menu
from config.chromadb import connect_db

menu_router = APIRouter()

DATA_DIR = os.getenv('DATA_DIR')
OCR_DATA_DIR = os.getenv('OCR_DATA_DIR')
STORAGE_ENDPOINT = os.getenv('NCP_STORAGE_ENDPOINT')

s3 = None
BUCKET_NAME = None

collection = None

def get_connect_s3():
    global s3, BUCKET_NAME
    if s3 is None:
        s3, BUCKET_NAME = connect_s3()

def get_connect_db():
    global collection
    if collection is None:
        collection = connect_db()

@menu_router.post("")
async def ocr_upload(image: Image = Depends()):
    before_dir = os.getenv('BEFORE_DIR')
    result_dir = os.getenv('RESULT_DIR')
    image = image.model_dump()

    image_key = image['key']
    extension = image['extension']
    logger.info(f"Image key: {image_key}")
    file_path = os.path.join(OCR_DATA_DIR, f'{image_key}.{extension}')
    result_path = os.path.join(OCR_DATA_DIR, f'{image_key}_result.{extension}')
    download_file_from_s3(s3, BUCKET_NAME, f'{before_dir}{image_key}.{extension}', file_path)
    ocr_df = image_to_df(image_key, extension)
    image_figure(ocr_df, image_key, extension)
    upload_file_to_s3(s3, BUCKET_NAME, result_path, f'{result_dir}{image_key}_result.{extension}')

    storage_path = f'{STORAGE_ENDPOINT}/{BUCKET_NAME}/{result_dir}{image_key}_result.{extension}'
    response = {
        "key": image_key,
        "result_path": storage_path
    }
    return response


@menu_router.get("/{image_key}")
async def ocr_result(image_key: str):
    data_dir = os.getenv('OCR_DATA_DIR')
    logger.info(f"Image key: {image_key}")
    data_path = f'{data_dir}/{image_key}.csv'
    df = pd.read_csv(data_path)
    menu_dict = matching_menu(df, collection)
    return menu_dict
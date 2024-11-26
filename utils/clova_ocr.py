import os
import sys
import requests
import uuid
import time
import json
import pandas as pd
from dotenv import load_dotenv
from PIL import Image, ImageDraw
import re

sys.path.append(r'../')
load_dotenv()

OCR_DATA_DIR = os.getenv('OCR_DATA_DIR')

api_url = os.getenv('CLOVA_API_URL')
secret_key = os.getenv('CLOVA_SECRET_KEY')

request_json = {
    'images': [
        {
            'format': 'jpg',
            'name': 'demo'
        }
    ],
    'requestId': str(uuid.uuid4()),
    'version': 'V2',
    'timestamp': int(round(time.time() * 1000))
}

payload = {'message': json.dumps(request_json).encode('UTF-8')}
headers = {
    'X-OCR-SECRET': secret_key
}
def image_to_df(image_key):
    files = [
        ('file', open(f'{OCR_DATA_DIR}/{image_key}.jpg', 'rb'))
    ]

    response = requests.post(api_url, headers=headers, files=files, data=payload)

    df = pd.DataFrame()
    for i in response.json()['images'][0]['fields']:
        text = i['inferText']
        bounding = i['boundingPoly']['vertices']
        df = pd.concat([df, pd.DataFrame([[text, bounding]], columns=['text', 'bounding'])], axis=0)

    df.reset_index(drop=True, inplace=True)
    df.to_csv(f'{OCR_DATA_DIR}/{image_key}.csv', index=False)

    return df

def image_figure(ocr_df, image_key):
    image_path = f'{OCR_DATA_DIR}/{image_key}.jpg'
    gray_image_path = f'{OCR_DATA_DIR}/{image_key}_gray.jpg'
    result_image_path = f'{OCR_DATA_DIR}/{image_key}_result.jpg'

    image = Image.open(image_path)
    gray_image = image.convert('L')
    gray_image.save(gray_image_path)

    gray_image = Image.open(gray_image_path).convert('RGB')
    draw = ImageDraw.Draw(gray_image)

    text = ocr_df['text']
    bounding = [i for i in ocr_df['bounding']]

    # 1-2. text 정제 - 불필요한 문자 제거
    text = [re.sub(r'[^가-힣0-9a-zA-Z\s]', '', i) for i in text]

    # 2. 가까운 박스들을 하나로 합치기

    # bounding box를 x축을 기준으로 정렬
    for i, box in enumerate(bounding):
        new_box = [{'x': round(point['x'], -1), 'y': round(point['y'], -1)} for point in box]
        bounding[i] = (new_box, text[i])

    boxes = sorted(bounding, key=lambda x: (x[0][0]['y'], x[0][0]['x']))

    # distance 기준 부합 + 종류가 같은 박스들을 하나로 합치기
    text_pairs = []
    for i in range(len(boxes)):
        # 숫자로만 이루어진 경우 리스트에 추가
        is_digit = all(char.isdigit() for char in boxes[i][1]) and len(boxes[i][1]) > 1
        if i == 0:
            text_pairs.append([boxes[i][0], boxes[i][1], is_digit])
            continue

        current_box = text_pairs[-1][0]
        if abs(current_box[1]['x'] - boxes[i][0][0]['x']) < 400 and abs(
                current_box[1]['y'] - boxes[i][0][0]['y']) < 100 and text_pairs[-1][2] == is_digit:
            new_box = [current_box[0], boxes[i][0][1], boxes[i][0][2], current_box[3]]
            new_pair = [new_box, text_pairs[-1][1] + boxes[i][1], is_digit]
            text_pairs.pop()
            text_pairs.append(new_pair)
        else:
            text_pairs.append([boxes[i][0], boxes[i][1], is_digit])

    # draw boxes and texts
    for (box, text, score) in text_pairs:
        (top_left, top_right, bottom_right, bottom_left) = box[0], box[1], box[2], box[3]
        # print(top_left, top_right, bottom_right, bottom_left)
        top_left = (top_left['x'], top_left['y'])
        bottom_right = (bottom_right['x'], bottom_right['y'])
        bottom_left = (bottom_left['x'], bottom_left['y'])

        crop_image = image.crop((top_left[0], top_left[1], bottom_right[0], bottom_right[1]))
        gray_image.paste(crop_image, box=(int(top_left[0]), int(top_left[1])))
        # gray_image.paste(crop_image, box=(0, 0))

        draw.rectangle([top_left, bottom_right], outline='red', width=3)
        # draw.text(bottom_left, text, font=font, fill='red')

        # 3. 이미지 저장
        gray_image.save(result_image_path)

    return result_image_path

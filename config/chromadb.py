import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def connect_db():
    db_dir = os.getenv('DB_DIR')
    chroma_client = chromadb.PersistentClient(db_dir)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv('OPENAI_API_KEY'),
        model_name=os.getenv('OPENAI_MODEL_NAME')
    )

    collection = chroma_client.get_collection('food_list', embedding_function=openai_ef)

    return collection
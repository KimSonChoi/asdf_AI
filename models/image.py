from pydantic import BaseModel, Field
from fastapi import UploadFile

class Image(BaseModel):
    key: str = Field(..., title="Image Key")
    class Example:
        url = "example123"
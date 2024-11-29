from pydantic import BaseModel, Field
from fastapi import UploadFile

class Image(BaseModel):
    key: str = Field(..., title="Image Key")
    extension: str = Field(..., title="Filename Extension")
    class Example:
        url = "example123"
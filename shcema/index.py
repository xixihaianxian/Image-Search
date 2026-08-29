from pydantic import Field,BaseModel
from fastapi.encoders import jsonable_encoder
from jsonablr import encode
from typing import Optional
import json

def success_response(message:str,data:Optional[str]=None):
    return {
        "status":200,
        "message":message,
        "data":encode(data),
    }

if __name__=="__main__":
    pass
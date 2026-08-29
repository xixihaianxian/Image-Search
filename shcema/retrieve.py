from pydantic import BaseModel,Field,ConfigDict
from typing import Optional

class LogLocal(BaseModel):
    dir_path:str=Field(validation_alias="dirPath",serialization_alias="dirPath")
    model_config=ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
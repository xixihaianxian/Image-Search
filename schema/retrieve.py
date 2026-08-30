from pydantic import BaseModel,Field,ConfigDict
from typing import Optional

class LocalImage(BaseModel):
    image_path:str=Field(validation_alias="imagePath",serialization_alias="imagePath")
    model_config=ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

class LocalDir(BaseModel):
    folder:str=Field(validation_alias="folderPath",serialization_alias="folderPath")
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

class ImageInfo(BaseModel):
    name:str=Field(validation_alias="name",serialization_alias="name")
    image_url:str=Field(validation_alias="imageUrl",serialization_alias="imageUrl")
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
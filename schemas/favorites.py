from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class FavoriteResponse(BaseModel):
    id: int = Field(gt=0)
    directory_id: int = Field(gt=0)
    favorite_name: str = Field(min_length=2)
    directory_path: Optional[str] = Field()
    directory_class: int = Field(examples=[0])

class FavoriteCreate(BaseModel):
    directory_id: int = Field(gt=0,examples=[2])
    favorite_name: str = Field(min_length=2,examples=["お気に入りディレクトリ"])

class FavoriteUpdate(BaseModel):
    id: int = Field(gt=0)
    favorite_name: str = Field(min_length=2)

class FavoriteDelete(BaseModel):
    id: int = Field(gt=0)
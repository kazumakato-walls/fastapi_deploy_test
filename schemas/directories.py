from pydantic import BaseModel, Field
from typing import Optional

class DirectoryCreate(BaseModel):
    directory_id: Optional[int] = Field(None, ge=1)
    directory_name: str = Field(min_length=1, examples=["フォルダ名"])
    open_flg: bool = Field(examples=[False])

class DirectoryRename(BaseModel):
    directory_id: int = Field(gt=0, examples=[1])
    new_directory_name: str = Field(min_length=1, examples=["新しいフォルダ名"])

class DirectoryDelete(BaseModel):
    directory_id: int = Field(gt=0, examples=[1])
    
class DirectoryResponse(BaseModel):
    directory_id: int = Field(gt=0, examples=[1])
    directory_name: str = Field(min_length=1, examples=["フォルダ名"])
    path: Optional[str] = Field(None)
    directory_class: int = Field(gt=0, examples=[1])

class DirectoryGetResponse(BaseModel):
    directory_id: int = Field(gt=0, examples=[1])
    file_name: str = Field(min_length=2, examples=["ファイル名"])
    file_size: Optional[str] = Field(min_length=1, examples=["KB"])
    filetype_name: Optional[str] = Field(min_length=1, examples=[".txt"])
    update_at: Optional[str] = Field(min_length=1, examples=["2022-01-01 00:00:00"])
    icon_id: Optional[int] = Field(gt=0, examples=[1])

class DirectoryDownload(BaseModel):
    directory_id: int = Field(gt=0, examples=[1])
    local_download_path: str = Field(min_length=1, examples=["ダウンロードパス"])

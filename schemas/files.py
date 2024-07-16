from typing import Optional
from pydantic import BaseModel, Field

class FileGetResponse(BaseModel):
    id: int = Field(gt=0, examples=[1])
    file_name: Optional[str]  = Field(min_length=0, examples=["ファイル名"])
    file_size: Optional[str] = Field(min_length=1, examples=["KB"])
    filetype_name: Optional[str] = Field(min_length=1, examples=[".txt"])
    file_update_at: Optional[str] = Field(min_length=1, examples=["2022-01-01 00:00:00"])
    icon_id: Optional[int] = Field(gt=0, examples=[1])

class FileUploadResponse(BaseModel):
    directory_id: Optional[int] = Field(gt=0, examples=[1])
    file_id: int = Field(gt=0, examples=[1])
    file_name: str = Field(min_length=2, examples=["ファイル名"])
    file_size: int = Field(gt=0, examples=[1])

class FileRenameResponse(BaseModel):
    directory_id: int = Field(gt=0, examples=[1])
    file_id: int = Field(gt=0, examples=[1])
    old_directory_name: str = Field(min_length=1, examples=["旧ファイル名"])
    new_directory_name: str = Field(min_length=1, examples=["新ファイル名"])

class FileDeleteResponse(BaseModel):
    directory_id: int = Field(gt=0, examples=[1])
    file_id: int = Field(gt=0, examples=[1])
    file_name: str = Field(min_length=1, examples=["ファイル名"])

class FileGet(BaseModel):
    directory_id: Optional[int] = Field(None, gt=0, examples=[1])

class FileDownload(BaseModel):
    file_id: int = Field(gt=0, examples=[1])

class FileUploadData(BaseModel):
    directory_id: Optional[int] = Field(gt=0, examples=[1])

class FileRename(BaseModel):
    file_id: int = Field(gt=0, examples=[1])
    new_file_name: str = Field(min_length=1, examples=["新ファイル名"])

class FileDelete(BaseModel):
    file_id: int = Field(gt=0, examples=[1])

class FileGetStorage(BaseModel):
    company_id: int = Field(gt=0, examples=[1])
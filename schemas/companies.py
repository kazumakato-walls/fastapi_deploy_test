from datetime import datetime
from pydantic import BaseModel, Field
         
class CompanyCreate(BaseModel):
    industry_id: int = Field(gt=0, examples=[1])
    region_id: int = Field(gt=0, examples=[1])
    storage_name: str = Field(min_length=3, examples=["ストレージ名"])
    company_name: str = Field(min_length=2, examples=["株式会社walls"])
    tell: str = Field(min_length=10, examples=["090-0011-2233"])
    storage: int = Field(gt=0, examples=[1048576])

class CompanyUpdate(BaseModel):
    id: int = Field(gt=0, examples=[1])
    industry_id: int = Field(gt=0, examples=[1])
    region_id: int = Field(gt=0, examples=[1])
    company_name: str = Field(min_length=2, examples=["株式会社walls"])
    tell: str = Field(min_length=10, examples=["090-0011-2233"])
    storage: int = Field(gt=0, examples=[1048576])

class CompanyResponse(BaseModel):
    id: int = Field(gt=0, examples=[1])
    storage_name: str = Field(min_length=2, examples=["ストレージ名"])
    company_name: str = Field(min_length=2, examples=["株式会社walls"])
    tell: str = Field(min_length=10, examples=["090-0011-2233"])
    storage: int = Field(gt=0, examples=[5])

class CompanyDirectoryCreate(BaseModel):
    id: int = Field(gt=0, examples=[1])
    directory_id: int = Field(gt=0, examples=[1])
    storage_name: str = Field(min_length=2, examples=["ストレージ名"])
    company_name: str = Field(min_length=2, examples=["株式会社walls"])
    tell: str = Field(min_length=10, examples=["090-0011-2233"])
    storage: int = Field(gt=0, examples=[5])
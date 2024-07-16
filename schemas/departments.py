from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
         
class DepartmentCreate(BaseModel):
    department_name: str = Field(min_length=2, examples=["開発部"])
    storage: int = Field(gt=0, examples=[1])

class DepartmentUpdate(BaseModel):
    id: int = Field(gt=0, examples=[1])
    department_name: Optional[str] = Field(min_length=2, examples=["開発部"])

class DepartmentResponse(BaseModel):
    id: int = Field(gt=0, examples=[1])
    company_id: int = Field(gt=0, examples=[1])
    department_name: str = Field(min_length=2, examples=["開発部"])
    storage: int = Field(gt=0, examples=[1])
    create_at: datetime = Field(examples=[datetime.now()])
    create_acc: int = Field(gt=0, examples=[1])
    update_at: Optional[datetime] = Field(examples=[datetime.now()])
    update_acc: Optional[int] = Field(gt=0, examples=[1])

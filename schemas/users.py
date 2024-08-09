from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class ItemStatus(str, Enum):
    man = "男"
    woman = "女"
    other = "その他"

class UserSignup(BaseModel):
    personal_id: str = Field(min_length=6, examples=["test1234"])
    secret_key: str = Field(min_length=8, examples=["abcdefghi"])

class UserCreate(BaseModel):
    company_id: int = Field(gt=0, examples=[1])
    department_id: int = Field(gt=0, examples=[1])
    personal_id: str = Field(min_length=6, examples=["test1234"])
    user_name: str = Field(min_length=2, examples=["Walls太郎"])
    # name_kana: str = Field(min_length=2, examples=["うぉーるずたろう"])
    # password: str = Field(min_length=8, examples=["test1234"])
    # email: str = Field(min_length=8, examples=["test@walls-inc.com"])
    storage: int = Field(gt=1, examples=[1048576])
    # permission: bool = Field()
    # admin: bool = Field()
    # delete_flg: bool = Field(examples=[False])

class UserAll(BaseModel):
    id: int = Field(gt=0, examples=[1])
    company_id: int = Field(gt=0, examples=[1])
    department_id: int = Field(gt=0, examples=[1])
    personal_id: str = Field(min_length=6, examples=["test1234"])
    user_name: str = Field(min_length=2, examples=["Walls太郎"])
    name_kana: str = Field(min_length=2, examples=["うぉーるずたろう"])
    password: str = Field(min_length=8, examples=["test1234"])
    email: str = Field(min_length=8, examples=["test@walls-inc.com"])
    storage: int = Field(gt=0, examples=[1])
    salt: str = Field()
    age: date = Field(examples=['1999-01-01'])
    sex: Optional[ItemStatus] = Field(None, examples=[ItemStatus.man])
    permission: bool = Field()
    admin: bool = Field()

class UserGetResponse(BaseModel):
    department_name: str = Field(min_length=2, examples=["部署名"])
    user_name: str = Field(min_length=2, examples=["Walls太郎"])
    name_kana: Optional[str] = Field(min_length=2, examples=["うぉーるずたろう"])
    email: Optional[str] = Field(min_length=8, examples=["test@walls-inc.com"])
    age: Optional[date] = Field(examples=['1999-01-01'])
    sex: Optional[ItemStatus] = Field(None, examples=[ItemStatus.man])

class UserAdminGetResponse(BaseModel):
    id: int = Field(gt=0, examples=[1])
    company_id: int = Field(gt=0, examples=[1])
    user_name: str = Field(min_length=2, examples=["Walls太郎"])
    name_kana: Optional[str] = Field(min_length=2, examples=["うぉーるずたろう"])
    email: Optional[str] = Field(min_length=8, examples=["test@walls-inc.com"])
    age: Optional[date] = Field(examples=['1999-01-01'])
    sex: Optional[ItemStatus] = Field(None, examples=[ItemStatus.man])
    admin: bool = Field()

class UserResponse(BaseModel):
    personal_id: str = Field(min_length=6, examples=["test1234"])
    user_name: str = Field(min_length=2, examples=["Walls太郎"])
    storage: int = Field(gt=0, examples=[5])

class UserUpdateResponse(BaseModel):
    department_id: int = Field(gt=0, examples=[1])
    user_name: str = Field(min_length=2, examples=["Walls太郎"])
    name_kana: Optional[str] = Field(min_length=2, examples=["うぉーるずたろう"])
    email: Optional[str] = Field(min_length=8, examples=["test@walls-inc.com"])
    age: Optional[date] = Field(examples=['1999-01-01'])
    sex: Optional[ItemStatus] = Field(None, examples=[ItemStatus.man])

class UserUpdate(BaseModel):
    department_id: int = Field(gt=0, examples=[1])
    user_name: str = Field(min_length=2, examples=["Walls太郎"])
    name_kana: Optional[str] = Field(min_length=2, examples=["うぉーるずたろう"])
    email: Optional[str] = Field(min_length=8, examples=["test@walls-inc.com"])
    age: Optional[date] = Field(examples=['1999-01-01'])
    sex: Optional[ItemStatus] = Field(None, examples=[ItemStatus.man])
    # icon: str = Field(min_length=2, examples=["アイコン"])

class UserPasswordUpdate(BaseModel):
    password: str = Field(min_length=8, examples=["abcdefghi"])
    new_password: str = Field(min_length=8, examples=["abcdefghi"])

class UserAdminUpdate(BaseModel):
    company_id: int = Field(gt=0, examples=[1])
    department_id: int = Field(gt=0, examples=[1])
    user_name: str = Field(min_length=2, examples=["Walls太郎"])
    name_kana: Optional[str] = Field(min_length=2, examples=["うぉーるずたろう"])
    email: Optional[str] = Field(min_length=8, examples=["test@walls-inc.com"])
    storage: int = Field(gt=0, examples=[1])
    age: Optional[date] = Field(examples=['1999-01-01'])
    sex: Optional[ItemStatus] = Field(None, examples=[ItemStatus.man])
    admin: bool = Field()

class UserDelete(BaseModel):
    user_id: int = Field(gt=0, examples=[1])
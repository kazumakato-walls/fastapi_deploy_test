from hmac import new
from fastapi import Depends, APIRouter, status,HTTPException
import re
from models import Company, Department, Directory, Industry
from typing import Annotated
from db import get_db
from sqlalchemy.orm import Session
from schemas.auth import DecodedToken
from auth import get_current_user
from azure_access import add_azure_share_client, delete_azure_share_client
from schemas.companies import CompanyCreate,CompanyResponse,CompanyUpdate,CompanyDirectoryCreate
from datetime import datetime
from pydantic import BaseModel

class OAuth2PasswordRequestFormCustom(BaseModel):
    industry_id: str   
    region_id: str
    storage_name: str
    company_name: str
    tell: str
    storage: str

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[DecodedToken, Depends(get_current_user)]
FormDependency = Annotated[OAuth2PasswordRequestFormCustom, Depends()]

router = APIRouter(prefix="/company",tags=["company"])
@router.get('/get_all',status_code=status.HTTP_200_OK)
async def queryParam(db: DbDependency):
    item = db.query(Company).all()
    return item

# ストレージ名の形式チェック
def is_valid_share_name(share_name: str) -> bool:
    # 名前の長さをチェック
    if len(share_name) < 3 or len(share_name) > 63:
        return False

    # 名前の形式をチェック（英小文字、数字、およびハイフンのみを含む）
    # 最初と最後の文字は英小文字または数字
    # 連続するハイフンは許可されない
    if not re.match(r'^[a-z0-9](-?[a-z0-9])+$', share_name):
        return False

    # 連続するハイフンが存在するかチェック
    if '--' in share_name:
        return False

    return True

# 会社情報の取得（全件）
@router.get('/get_all',status_code=status.HTTP_200_OK)
async def queryParam(db: DbDependency):
    item = db.query(Company).all()
    return item

# 会社情報の取得
@router.get('/get_company', response_model=CompanyResponse, status_code=status.HTTP_200_OK)
async def get_company(db: DbDependency, user: UserDependency, company_id: int):
    company = db.query(Company)\
        .filter(
            Company.id == company_id
            )\
        .first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_response = CompanyResponse(
        id=company.id,
        storage_name=company.storage_name,
        company_name=company.company_name,
        tell=company.tell,
        storage=company.storage
        )
    
    return company_response

# 会社情報の追加
@router.post("/add_company", status_code=status.HTTP_201_CREATED)
async def create(db: DbDependency, user: UserDependency, user_create: CompanyCreate):
    # 権限チェック
    if user.admin != True:
        raise HTTPException(status_code=403, detail="No authority")
    
    # ストレージ名の形式チェック
    if not is_valid_share_name(user_create.storage_name):
        raise HTTPException(status_code=400, detail="Invalid storage name")
    
    # 会社情報を全権取得後、会社名の重複チェックを行う
    company_query_all = db.query(Company).all()
    if company_query_all:
        for company in company_query_all:
            if company.company_name == user_create.company_name:
                raise HTTPException(status_code=409, detail="Company name already exists")
            if company.storage_name == user_create.storage_name:
                raise HTTPException(status_code=409, detail="Storage name already exists")






    # # 会社名の重複チェック
    # company_query = db.query(Company)\
    #     .filter(
    #         Company.company_name == user_create.company_name
    #         )\
    #     .first()
    
    # if company_query:
    #     raise HTTPException(status_code=409, detail="Company name already exists")
    
    # # storage_nameの重複チェック
    # company_query = db.query(Company)\
    #     .filter(
    #         Company.storage_name == user_create.storage_name
    #         )\
    #     .first()

    # if company_query:
    #     raise HTTPException(status_code=409, detail="Storage name already exists")

    # Azureのストレージを作成
    add_azure_share_client(user_create.storage_name)

    new_company = Company(
        industry_id = user_create.industry_id,
        region_id = user_create.region_id,
        storage_name = user_create.storage_name,
        company_name = user_create.company_name,
        tell = user_create.tell,
        storage = user_create.storage,
        create_at = datetime.now(),
        update_at = datetime.now()
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    # 追加した会社IDに紐づく部署情報を作成
    new_department = Department(
        company_id = new_company.id,
        department_name = 'なし',
        storage = new_company.storage,
        create_at = datetime.now(),
        create_acc = user.user_id,
        update_at = datetime.now(),
        update_acc = user.user_id
    )

    db.add(new_department)
    db.commit()
    db.refresh(new_department)


    # directory_name,pathなし、directory_class=0のデータを作成
    new_directory = Directory(
        company_id = new_company.id,
        directory_class = 0,
        open_flg = True,
        delete_flg = False,
        create_at = datetime.now(),
        create_acc = user.user_id,
        update_at = datetime.now(),
        update_acc = user.user_id
    )

    db.add(new_directory)
    db.commit()
    db.refresh(new_directory)

    new_company_create = CompanyDirectoryCreate(
        id=new_company.id,
        directory_id=new_directory.id,
        storage_name=new_company.storage_name,
        company_name=new_company.company_name,
        tell=new_company.tell,
        storage=new_company.storage
        )
    
    return new_company_create

# 会社情報の追加
@router.post("/add_company2", status_code=status.HTTP_201_CREATED)
async def create(db: DbDependency, user: UserDependency,user_create: CompanyCreate ):
    return user_create

# 会社情報の更新
@router.put("/update_company", status_code=status.HTTP_200_OK)
async def update(db: DbDependency, user: UserDependency, user_update: CompanyUpdate):
    if user.admin != True:
        raise HTTPException(status_code=403, detail="No authority")
    
    # 会社情報を全権取得後、会社名の重複チェックを行う
    company_query_all = db.query(Company).all()
    if company_query_all:
        for company in company_query_all:
            if company.company_name == user_update.company_name:
                raise HTTPException(status_code=409, detail="Company name already exists")
    else:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_query = db.query(Company)\
        .filter(Company.id == user_update.id)\
        .first()
    
    if not company_query:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_query.company_name = user_update.company_name
    company_query.industry_id = user_update.industry_id
    company_query.region_id = user_update.region_id
    company_query.tell = user_update.tell
    company_query.storage = user_update.storage
    company_query.update_at = datetime.now()

    db.commit()
    db.refresh(company_query)

    company_update = CompanyResponse(
        id=company_query.id,
        company_name=company_query.company_name,
        storage_name=company_query.storage_name,
        tell=company_query.tell,
        storage=company_query.storage
        )
    
    return company_update

# 会社情報の削除
@router.delete("/delete_company", status_code=status.HTTP_204_NO_CONTENT)
async def delete(db: DbDependency, user: UserDependency, company_id: int):
    if user.admin != True:
        raise HTTPException(status_code=403, detail="No authority")
    
    company_query = db.query(Company)\
        .filter(
            Company.id == company_id
            )\
        .first()

    if not company_query:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # share_clientの削除
    delete_azure_share_client(company_query.storage_name)

    db.delete(company_query)
    db.commit()

    return {"message": "Company deleted successfully."}
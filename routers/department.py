from hmac import new
from fastapi import Depends, APIRouter, status,HTTPException,Response
from models import Department
from typing import Annotated, List
from db import get_db
from sqlalchemy.orm import Session
from schemas.auth import DecodedToken
from auth import get_current_user
from schemas.departments import DepartmentCreate,DepartmentResponse,DepartmentUpdate
from datetime import datetime

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[DecodedToken, Depends(get_current_user)]
router = APIRouter(prefix="/department",tags=["department"])

# ストレージサイズをKB,MB,GBに変換
def convert_storage(storage: int) -> str:
    if storage < 1024:
        return f"{storage}KB"
    elif storage < 1024 ** 2:
        return f"{storage / 1024:.2f}MB"
    else:
        return f"{storage / 1024 ** 2:.2f}GB"
    
# ファイルサイズをKB,MB,GBに変換
def convert_file_size(size_in_bytes: int) -> str:
    size_in_kb = size_in_bytes / 1024
    if size_in_kb < 1:
        return "1KB"  # 1KB以下の場合は切り上げて1KBとする
    if size_in_kb >= 1048576:  # 1GB以上の場合
        size_in_gb = size_in_kb / 1024 / 1024
        return f"{round(size_in_gb, 1)}GB"
    if size_in_kb >= 10240:  # 10MB以上の場合
        size_in_mb = size_in_kb / 1024
        return f"{round(size_in_mb, 1)}MB"
    return f"{round(size_in_kb, 1)}KB"
    
# 部署情報の取得
@router.get('/get_all_department', response_model=List[DepartmentResponse], status_code=status.HTTP_200_OK)
async def get_all_department(db: DbDependency, company_id: int):
    query_department_result = db.query(Department)\
        .filter(
            Department.company_id == company_id
        ).all()  
# async def get_all_department(db: DbDependency):
#     query_department_result = db.query(Department).all()
    
    if not query_department_result:
        raise HTTPException(status_code=404, detail="Department not found")
    
    department_response = [
        DepartmentResponse(
            id=department.id,
            company_id=department.company_id,
            department_name=department.department_name,
            storage=department.storage,
            create_at=department.create_at,
            create_acc=department.create_acc,
            update_at=department.update_at,
            update_acc=department.update_acc
        ) for department in query_department_result
    ]
    
    return department_response

# 各社部署情報の取得
@router.get('/get_department', response_model=List[DepartmentResponse], status_code=status.HTTP_200_OK)
async def get_department(db: DbDependency, user: UserDependency):
    query_department_result = db.query(
        Department.id,
        Department.company_id,
        Department.department_name,
        Department.storage,
        Department.create_at,
        Department.create_acc,
        Department.update_at,
        Department.update_acc
    ).filter(
            Department.company_id == user.company_id,
        ).all()
    
    if not query_department_result:
        raise HTTPException(status_code=404, detail="Department not found")
    
    department_response = [
        DepartmentResponse(
            id=department.id,
            company_id=department.company_id,
            department_name=department.department_name,
            storage=department.storage,
            create_at=department.create_at,
            create_acc=department.create_acc,
            update_at=department.update_at,
            update_acc=department.update_acc
        ) for department in query_department_result
    ]
    
    return department_response

# 部署情報の登録
@router.post('/create_department', response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(db: DbDependency, user: UserDependency, department_create: DepartmentCreate):

# department_nameの重複チェック
    query_department_result = db.query(Department)\
        .filter(
            Department.company_id == user.company_id,
            Department.department_name == department_create.department_name
        ).first()
    
    if query_department_result:
        raise HTTPException(status_code=400, detail="Department already exists")

    new_department = Department(
        company_id=user.company_id,
        department_name=department_create.department_name,
        storage=department_create.storage,
        create_at=datetime.now(),
        create_acc=user.user_id,
        update_at=datetime.now(),
        update_acc=user.user_id
    )

    db.add(new_department)
    db.commit()
    db.refresh(new_department)
    
    department_response = DepartmentResponse(
        id=new_department.id,
        company_id=new_department.company_id,
        department_name=new_department.department_name,
        storage=new_department.storage,
        create_at=new_department.create_at,
        create_acc=new_department.create_acc,
        update_at=new_department.update_at,
        update_acc=new_department.update_acc
        )
    
    return department_response

# テスト用部署情報の登録
@router.post('/create_test_department', response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_test_department(db: DbDependency, user: UserDependency, department_create: DepartmentCreate):

# department_nameの重複チェック
    query_department_result = db.query(Department)\
        .filter(
            Department.company_id == department_create.company_id,
            Department.department_name == department_create.department_name
        ).first()
    
    if query_department_result:
        raise HTTPException(status_code=400, detail="Department already exists")

    new_department = Department(
        company_id=department_create.company_id,
        department_name=department_create.department_name,
        storage=department_create.storage,
        create_at=datetime.now(),
        create_acc=user.user_id,
        update_at=datetime.now(),
        update_acc=user.user_id
    )

    db.add(new_department)
    db.commit()
    db.refresh(new_department)
    
    department_response = DepartmentResponse(
        id=new_department.id,
        company_id=new_department.company_id,
        department_name=new_department.department_name,
        create_at=new_department.create_at,
        create_acc=new_department.create_acc,
        update_at=new_department.update_at,
        update_acc=new_department.update_acc
        )
    
    return department_response

# 部署情報の更新
@router.put('/update_department', response_model=DepartmentResponse, status_code=status.HTTP_200_OK)
async def update_department(db: DbDependency, user: UserDependency, department_update: DepartmentUpdate):
    query_department_result = db.query(Department)\
        .filter(
            Department.company_id == user.company_id,
            Department.id == department_update.id,
            Department.department_name != department_update.department_name
        ).first()
    
    if not query_department_result:
        raise HTTPException(status_code=404, detail="Department not found")
    
    query_department_result.department_name = department_update.department_name
    query_department_result.update_at = datetime.now()
    query_department_result.update_acc = user.user_id
    
    db.commit()
    db.refresh(query_department_result)
    
    department_response = DepartmentResponse(
        id=query_department_result.id,
        company_id=query_department_result.company_id,
        department_name=query_department_result.department_name,
        storage=query_department_result.storage,
        create_at=query_department_result.create_at,
        create_acc=query_department_result.create_acc,
        update_at=query_department_result.update_at,
        update_acc=query_department_result.update_acc
    )
    
    return department_response

# 部署情報の削除
@router.delete('/delete_department', status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(db: DbDependency, user: UserDependency, department_id: int, response: Response):
    query_department_result = db.query(Department)\
        .filter(
            Department.company_id == user.company_id,
            Department.id == department_id
        ).first()
    
    if not query_department_result:
        raise HTTPException(status_code=404, detail="Department not found")
    
    db.delete(query_department_result)
    db.commit()
    
    response.headers["Message"] = "Department deleted successfully"
from datetime import timedelta
from typing import Annotated, List
from fastapi import Response, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from schemas.users import UserCreate,UserResponse, UserGetResponse, UserAdminGetResponse, UserSignup, UserUpdateResponse, UserUpdate, UserAdminUpdate, UserPasswordUpdate
from schemas.auth import Token
from db import get_db
from models import User, Department, Company, Department
import hashlib
import base64
import os
from dotenv import load_dotenv
from auth import get_current_user, create_access_token
from schemas.auth import DecodedToken
from datetime import datetime
from pydantic import BaseModel
from starlette.status import HTTP_200_OK

# .envファイルを読み込む
load_dotenv()

class OAuth2PasswordRequestFormCustom(BaseModel):
    personal_id: str
    password: str
DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[DecodedToken, Depends(get_current_user)]
FormDependency = Annotated[OAuth2PasswordRequestFormCustom, Depends()]
router = APIRouter(prefix="/user", tags=["User"])
CREATE_SECRET_KEY = os.getenv('secret_key')

#初期ユーザー作成機能
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(db: DbDependency,user_create: UserSignup):

    salt = base64.b64encode(os.urandom(32))
    hashed_password = hashlib.pbkdf2_hmac(
        "sha256", user_create.personal_id.encode(), salt, 1000
    ).hex()

    # 入力されたハッシュ値とCREATE_SECRET_KEYのハッシュ値が一致しない場合、エラーを返す
    if hashlib.sha256(CREATE_SECRET_KEY.encode()).hexdigest() != user_create.secret_key:
        raise HTTPException(status_code=401, detail="Incorrect_secret_key")

    new_user = User(
        company_id=1,
        department_id=1,
        personal_id=user_create.personal_id,
        user_name="admin",
        password=hashed_password,
        salt=salt.decode(),
        storage=1048576,
        permission=False,
        admin=True,
        delete_flg=False,
        create_at= datetime.now()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_user_create = UserResponse(
        personal_id=new_user.personal_id,
        user_name=new_user.user_name,
        storage=new_user.storage
        )
    
    return new_user_create


#ユーザー作成機能
#saltとはパスワードをハッシュ化する際に使用するランダムな値
#パスワードと組み合わせてハッシュ化することで同じパスワードでも異なるハッシュ値を生成する仕組みを作る。
@router.post("/create_user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(db: DbDependency, user: UserDependency, user_create: UserCreate):

    # personal_idの重複チェック
    user_query = db.query(User)\
        .filter(User.personal_id == user_create.personal_id)\
        .first()
    
    if user_query:
        raise HTTPException(status_code=400, detail="Personal_id already exists")

    salt = base64.b64encode(os.urandom(32))
    hashed_password = hashlib.pbkdf2_hmac(
        "sha256", user_create.personal_id.encode(), salt, 1000
    ).hex()

    new_user = User(
        company_id=user_create.company_id,
        department_id=user_create.department_id,
        personal_id=user_create.personal_id,
        user_name=user_create.user_name,
        password=hashed_password,
        salt=salt.decode(),
        storage=user_create.storage,
        permission=False,
        admin=False,
        delete_flg=False,
        create_at= datetime.now()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    new_user_create = UserResponse(
        personal_id=new_user.personal_id,
        user_name=new_user.user_name,
        storage=new_user.storage
        )
    return new_user_create

#ログイン機能
@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(db: DbDependency, response:Response, form_data: FormDependency):

    user = db.query(User)\
           .filter(User.personal_id == form_data.personal_id\
                  ,User.delete_flg == "false"\
                  )\
                  .first()
    # #ユーザー存在チェック
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect personal_id")

    hashed_password = hashlib.pbkdf2_hmac(
        "sha256", form_data.password.encode(), user.salt.encode(), 1000
    ).hex()
    #パスワードチェック
    if user.password != hashed_password:
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_access_token(
        db, user.personal_id, timedelta(days=30)
        # user.username, user.id, timedelta(minutes=5)        
    )
    response.status_code = HTTP_200_OK
    response.set_cookie(
        key="access_token",value=f"Beaere {token}",httponly=True,samesite="none",secure=True
    )
    # return {"message": "Successfully logged-in"}
    # return response
    return {"access_token": token, "token_type": "bearer"}
    
#ログアウト機能
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged-out"}

#ユーザー情報取得機能
@router.get("/get_user", response_model=UserGetResponse, status_code=status.HTTP_200_OK)
async def get_user(db: DbDependency, user: UserDependency):
    user_query = db.query(
        User.user_name,
        User.name_kana,
        User.email,
        User.storage,
        User.age,
        User.sex,
        Department.department_name
        )\
        .select_from(User)\
        .outerjoin(Department, User.department_id == Department.id)\
        .filter(User.id == user.user_id)\
        .first()
    
    if not user_query:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_info = UserGetResponse(
        user_name=user_query.user_name,
        name_kana=user_query.name_kana,
        email=user_query.email,
        age=user_query.age,
        sex=user_query.sex,
        department_name=user_query.department_name,
    )
    return user_info

#全てのユーザー情報取得機能(Admin権限)
@router.get("/get_all_user", status_code=status.HTTP_200_OK)
async def get_all_user(db: DbDependency, user: UserDependency):
    if not user.admin:
        raise HTTPException(status_code=403, detail="No authority")
    
    result = (db.query(User.id,
                       User.company_id,
                       Company.company_name,
                       User.department_id,
                       Department.department_name,
                       User.user_name,
                       User.name_kana,
                       User.email,
                       User.storage,
                       User.age,
                       User.sex,
                       User.permission,
                       User.admin,
                       )
        .select_from(User)
        .outerjoin(Company,
                   User.company_id == Company.id
                  )
        .outerjoin(Department,
                   User.department_id == Department.id
                  )
        .filter(User.delete_flg == "false")
        .order_by(User.company_id)
        .all()
    )

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    return result

# ユーザー情報更新機能
@router.put("/update_user", response_model=UserUpdateResponse, status_code=status.HTTP_200_OK)
async def update_user(db: DbDependency, user: UserDependency, user_update: UserUpdate):
    user_query = db.query(User)\
        .filter(
            User.id == user.user_id,
            )\
        .first()

    if not user_query:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_query.department_id = user_update.department_id
    user_query.user_name = user_update.user_name
    user_query.name_kana = user_update.name_kana
    user_query.email = user_update.email
    user_query.age = user_update.age
    user_query.sex = user_update.sex
    # user_query.icon = user_update.icon
    user_query.update_at = datetime.now()

    db.commit()
    db.refresh(user_query)

    user_update = UserUpdateResponse(
        department_id=user_query.department_id,
        user_name=user_query.user_name,
        name_kana=user_query.name_kana,
        email=user_query.email,
        age=user_query.age,
        sex=user_query.sex,
        # icon=user_query.icon
    )

    return user_update

# ユーザー情報更新機能(Admin権限)
@router.put("/update_user_admin", status_code=status.HTTP_200_OK)
async def update_user_admin(db: DbDependency, user: UserDependency, user_update: UserAdminUpdate):
    if not user.admin:
        raise HTTPException(status_code=403, detail="No authority")

    user_query = db.query(User)\
        .filter(
            User.id == user.user_id,
            User.delete_flg == "false"
            )\
        .first()

    if not user_query:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_query.company_id = user_update.company_id
    user_query.department_id = user_update.department_id
    user_query.user_name = user_update.user_name
    user_query.name_kana = user_update.name_kana
    user_query.email = user_update.email
    user_query.storage = user_update.storage
    # user_query.permission = user_update.permission
    user_query.admin = user_update.admin
    user_query.update_at = datetime.now()

    db.commit()
    db.refresh(user_query)

    user_update = UserAdminGetResponse(
        id=user_query.id,
        company_id=user_query.company_id,
        department_id=user_query.department_id,
        user_name=user_query.user_name,
        name_kana=user_query.name_kana,
        email=user_query.email,
        storage=user_query.storage,
        age=user_query.age,
        sex=user_query.sex,
        admin=user_query.admin
    )

    return user_update

# ユーザーpassword更新機能
@router.put("/update_password", status_code=status.HTTP_200_OK)
async def update_password(db: DbDependency, user: UserDependency, user_password_update: UserPasswordUpdate):
    user_query = db.query(User)\
        .filter(
            User.id == user.user_id,
            )\
        .first()

    if not user_query:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 現在のパスワードが正しいかチェック
    check_password = hashlib.pbkdf2_hmac(
        "sha256", user_password_update.password.encode(), user_query.salt.encode(), 1000
    ).hex()
    if user_query.password != check_password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    # 新旧パスワードが同じ場合、エラーを返す
    if user_password_update.password == user_password_update.new_password:
        raise HTTPException(status_code=400, detail="New password is the same as the current password")
    
    # 新しいパスワードをハッシュ化
    salt = base64.b64encode(os.urandom(32))
    hashed_password = hashlib.pbkdf2_hmac(
        "sha256", user_password_update.new_password.encode(), salt, 1000
    ).hex()

    user_query.password = hashed_password
    user_query.salt = salt.decode()
    user_query.update_at = datetime.now()

    db.commit()
    db.refresh(user_query)

    return {"message": "Password updated successfully"}

# ユーザー削除機能
@router.delete("/delete_user", status_code=status.HTTP_200_OK)
async def delete_user(db: DbDependency, user: UserDependency, user_id: int):
    if not user.admin:
        raise HTTPException(status_code=403, detail="No authority")

    user_query = db.query(User)\
        .filter(
            User.id == user_id,
            )\
        .first()

    if not user_query:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_query.delete_flg = True
    user_query.update_at = datetime.now()

    db.commit()
    db.refresh(user_query)

    return {"message": "User deleted successfully"}
from datetime import timedelta
from typing import Annotated
from fastapi import Response, Request, APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette import status
from schemas.users import UserCreate,UserResponse
from schemas.auth import Token,Csrf
from db import get_db
from models import User
import hashlib
import base64
import os
from datetime import timedelta
from auth import create_access_token,encode_jwt,verify_jwt,verify_update_jwt,verify_csrf_update_jwt
from datetime import datetime
from pydantic import BaseModel
from starlette.status import HTTP_200_OK
from fastapi_csrf_protect import CsrfProtect
import json

class OAuth2PasswordRequestFormCustom(BaseModel):
    personal_id: str
    password: str
# csrfDependency = Annotated[CsrfProtect, Depends()]
DbDependency = Annotated[Session, Depends(get_db)]
FormDependency = Annotated[OAuth2PasswordRequestFormCustom, Depends()]
router = APIRouter(prefix="/auth", tags=["Auth"])

#ユーザー作成機能
#saltとはパスワードをハッシュ化する際に使用するランダムな値
#パスワードと組み合わせてハッシュ化することで同じパスワードでも異なるハッシュ値を生成する仕組みを作る。
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(db: DbDependency,user_create: UserCreate):
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
        email=new_user.email,
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
    
# ユーザー情報取得
@router.get('/authtest',status_code=status.HTTP_200_OK)
async def find_all(db: DbDependency,request: Request):
    user = db.query(User).all()
    token = encode_jwt(
        db, "test1234", timedelta(days=30)      
    )
    test =verify_jwt(request)

    return test

@router.get('/gettoken',status_code=status.HTTP_200_OK)
async def find_all(db: DbDependency,request: Request,response:Response):
    user = db.query(User).all()
    token = encode_jwt(
        db, "test1234", timedelta(days=30)      
    )
    test =verify_jwt(request)
    response.status_code = HTTP_200_OK
    response.set_cookie(
        key="access_token",value=f"Beaere {token}",httponly=True,samesite="none",secure=True
    )
    return token

@router.get('/updatetoken',status_code=status.HTTP_200_OK)
async def find_all(db: DbDependency,request: Request,response:Response):
    token = verify_update_jwt(db,request)
    response.status_code = HTTP_200_OK
    response.set_cookie(
        key="access_token",value=f"Beaere {token}",httponly=True,samesite="none",secure=True
    )
    return token

@router.get('/csrf_login',status_code=status.HTTP_200_OK)
async def find_all(form_data: FormDependency,db: DbDependency,request: Request, response:Response, csrf_protect: CsrfProtect = Depends()):
    # csrf_token = csrf_protect.get_csrf_from_headers(request.headers)
    # csrf_protect.validate_csrf(csrf_token)

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

    token = encode_jwt(
        db,{'personal_id':user.personal_id} 
    )
     
    response.status_code = HTTP_200_OK
    response.set_cookie(
        key="access_token",value=f"Beaere {token}",httponly=True,samesite="none",secure=True
    )
    return token

@router.post("/csrf_logout",status_code=status.HTTP_200_OK)
def logout(request: Request, response: Response, csrf_protect: CsrfProtect = Depends()):
    # csrf_token = csrf_protect.get_csrf_from_headers(request.headers)
    # csrf_protect.validate_csrf(csrf_token)
    response.set_cookie(key="access_token", value="",
                        httponly=True, samesite="none", secure=True)
    return {'message': 'Successfully logged-out'}

# CSRFトークン取得
@router.get("/api/csrftoken", response_model=Csrf)
def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    csrf_token = csrf_protect.generate_csrf()
    return {'csrf_token': csrf_token}


#ログイン機能
@router.post("/logintest",status_code=status.HTTP_200_OK)
async def login(db: DbDependency, response:Response, request:Request):

    # リクエストボディを非同期で取得
    body = await request.body()
    # バイナリデータを文字列に変換
    body_str = body.decode('utf-8')
    # 文字列をJSONオブジェクトに変換
    body_json = json.loads(body_str)
    
    # JSONデータをプリント
    print(body_json)

    user = db.query(User)\
           .filter(User.personal_id == body_json["personal_id"]\
                  ,User.delete_flg == "false"\
                  )\
                  .first()
    
    #ユーザー存在チェック
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect personal_id")

    hashed_password = hashlib.pbkdf2_hmac(
        "sha256", body_json["password"].encode(), user.salt.encode(), 1000
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
    return {"token": {token}, "data": {user}}
  
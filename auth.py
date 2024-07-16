from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, status,Security
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from schemas.auth import DecodedToken
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from db import get_db
from models import User

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login")
security = HTTPBearer()
#アクセストークンの作成
#ハッシュ化の方法
ALGORITHM = "HS256"
#ランダムな値
SECRET_KEY = "aaaaaaiuhlciakycbkaybciluabufchnlhaullbnubn1111u;h;uoho;h3uoh3;ounh"


def create_access_token(db: Session, personal_id: str, expires_delta: timedelta):
    user = db.query(User).filter(User.personal_id == personal_id).first()
    expires = datetime.now() + expires_delta
    payload = {"id": user.id, 
               "company_id": user.company_id, 
               "department_id": user.department_id, 
               "personal_id": user.personal_id,
               "user_name": user.user_name,
               "storage": user.storage,
               "permission": user.permission,
               "admin": user.admin,
               "icon":user.icon,                 
               "exp": expires}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        company_id = payload.get("company_id")
        department_id = payload.get("department_id")
        personal_id = payload.get("personal_id")
        user_name = payload.get("user_name")
        storage = payload.get("storage")
        permission = payload.get("permission")
        admin = payload.get("admin")
        icon = payload.get("icon")
        expires = payload.get("exp")
        if personal_id is None or user_id is None:
            raise HTTPException(status_code=403, detail="Invalid authentication credentials")
        return DecodedToken(user_id=user_id, 
                            company_id=company_id,
                            department_id=department_id,
                            personal_id=personal_id,
                            user_name=user_name,
                            storage=storage,
                            permission=permission,
                            admin=admin,
                            icon=icon,
                            expires=expires
                            )
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token or expired token")


# timedelta(days=30)
def encode_jwt(db: Session, user: dict):
    user = db.query(User).filter(User.personal_id == user["personal_id"]).first()
    expires = datetime.now() + timedelta(days=30)
    payload = {"id": user.id, 
               "company_id": user.company_id, 
               "department_id": user.department_id, 
               "personal_id": user.personal_id,
               "user_name": user.user_name,
               "storage": user.storage,
               "permission": user.permission,
               "admin": user.admin,
               "icon":user.icon,                 
               "exp": expires}
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

def decode_jwt(token):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # return payload['sub']
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401, detail='The JWT has expired')
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail='JWT is not valid')

# アクセストークン確認用 デコードした内容を返す
def verify_jwt(request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=403, detail="No JWT exist: may not set yet or deleted"
        )
    _,_, value = token.partition(" ")
    subject = decode_jwt(value)
    return subject

# アクセストークン更新
def verify_update_jwt(db: Session, request):
    subject = verify_jwt(request)
    new_token = encode_jwt(db,subject)
    return  new_token

# csrfトークン更新
def verify_csrf_update_jwt(db: Session, request, csrf_protect):
    csrf_token = csrf_protect.get_csrf_from_headers(request.headers)
    csrf_protect.validate_csrf(csrf_token)
    subject = verify_jwt(request)
    new_token = encode_jwt(db,subject)
    return new_token

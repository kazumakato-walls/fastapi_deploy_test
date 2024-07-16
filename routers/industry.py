from fastapi import Depends, APIRouter, status,HTTPException
from models import Company,Region,Industry
from typing import Annotated
from db import get_db
from sqlalchemy.orm import Session
from schemas.auth import DecodedToken
from auth import get_current_user
from schemas.companies import CompanyCreate,CompanyResponse,CompanyUpdate
from datetime import datetime

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[DecodedToken, Depends(get_current_user)]

router = APIRouter(prefix="/industry",tags=["industry"])
@router.get('/get_all',status_code=status.HTTP_200_OK)
async def queryParam(db: DbDependency):
    item = db.query(Industry).all()
    return item

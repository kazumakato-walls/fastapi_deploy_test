from fastapi import Depends, APIRouter, HTTPException,status
from models import Directory, Permission,Favorite
from typing import Annotated
from schemas.favorites import FavoriteResponse,FavoriteCreate,FavoriteUpdate,FavoriteDelete
from db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from schemas.auth import DecodedToken
from auth import get_current_user
from datetime import datetime

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[DecodedToken, Depends(get_current_user)]
router = APIRouter(prefix="/favorite",tags=["favorite"])

# お気に入り一覧取得
@router.get('/get_all', response_model=list[FavoriteResponse], status_code=status.HTTP_200_OK)
async def queryParam(db: DbDependency, user: UserDependency):
    # 権限あり
    query1 = db.query(Favorite.id,
                      Directory.id.label('directory_id'),
                      Favorite.favorite_name,
                      func.concat(func.coalesce(Directory.path, ''), Directory.directory_name).label('directory_path'),
                      Directory.directory_class
                      )\
                .select_from(Favorite)\
                .join(Directory, 
                      Favorite.directory_id == Directory.id
                      )\
                .outerjoin(Permission, 
                      Favorite.directory_id == Permission.directory_id
                      )\
                .filter(Favorite.user_id == user.user_id,
                        Directory.company_id == user.company_id,
                        Directory.delete_flg == False,
                        Directory.open_flg == False
                        )
                     
    # 非公開 権限あり
    query2 = db.query(Favorite.id,
                      Directory.id.label('directory_id'),
                      Favorite.favorite_name,
                      func.concat(func.coalesce(Directory.path, ''), Directory.directory_name).label('directory_path'),
                      Directory.directory_class
                      )\
                .select_from(Favorite)\
                .join(Directory, 
                      Favorite.directory_id == Directory.id
                      )\
                .join(Permission, 
                      Favorite.directory_id == Permission.directory_id
                      )\
                .filter(Favorite.user_id == user.user_id,
                        Directory.company_id == user.company_id,
                        Permission.user_id == user.user_id,
                        Directory.delete_flg == False,
                        Directory.open_flg == True
                        )
    
    result = query1.union_all(query2).all()
    
    return result

# お気に入り追加
@router.post('/add_favorite',status_code=status.HTTP_201_CREATED)
async def queryParam(db: DbDependency, user: UserDependency, favorite_create: FavoriteCreate):

    # お気に入り名が重複しているか確認
    favorite_query = db.query(Favorite)\
        .filter(
            Favorite.user_id == user.user_id,
            Favorite.favorite_name == favorite_create.favorite_name
            )\
        .first()
    
    if favorite_query:
        raise HTTPException(status_code=400, detail="Favorite name already exists")

    # ディレクトリ存在確認
    directory_query = db.query(Directory)\
        .filter(Directory.id == favorite_create.directory_id)\
        .first()

    if not directory_query:
        raise HTTPException(status_code=404, detail="Directory not found")
        
    new_favorite = Favorite(
        user_id = user.user_id,
        directory_id = favorite_create.directory_id,
        favorite_name = favorite_create.favorite_name,
        create_at = datetime.now(),
        update_at = datetime.now()
    )

    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)

    return new_favorite

# お気に入り更新
@router.put('/update_favorite',status_code=status.HTTP_200_OK)
async def queryParam(db: DbDependency, user: UserDependency, favorite_update: FavoriteUpdate):

    # お気に入り名が重複しているか確認
    favorite_query = db.query(Favorite)\
        .filter(
            Favorite.user_id == user.user_id,
            Favorite.favorite_name == favorite_update.favorite_name
            )\
        .first()
    
    if favorite_query:
        raise HTTPException(status_code=400, detail="Favorite name already exists")

    # お気に入り存在確認
    favorite = db.query(Favorite)\
        .filter(
            Favorite.id == favorite_update.id,
            Favorite.user_id == user.user_id
        ).first()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    favorite.favorite_name = favorite_update.favorite_name
    favorite.update_at = datetime.now()

    db.commit()
    db.refresh(favorite)
    
    return favorite

# お気に入り削除
@router.delete('/delete_favorite',status_code=status.HTTP_200_OK)
async def queryParam(db: DbDependency, user: UserDependency, favorite_delete: FavoriteDelete):

    # 削除対象お気に入り存在確認
    favorite = db.query(Favorite)\
        .filter(Favorite.id == favorite_delete.id,
                Favorite.user_id == user.user_id
                ).first()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    db.delete(favorite)
    db.commit()

    return favorite

@router.get("/all", status_code=status.HTTP_200_OK)
async def create(db: DbDependency, user: UserDependency):
    item = db.query(Favorite).all()
    return item
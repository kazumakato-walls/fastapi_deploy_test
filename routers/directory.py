from fastapi import Depends, APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated, List
from schemas.directories import DirectoryResponse, DirectoryCreate, DirectoryRename, DirectoryDelete
from schemas.auth import DecodedToken
from auth import get_current_user
from db import get_db
from models import Company, Directory, Permission, File
from sqlalchemy import or_, and_
from datetime import datetime
from azure_access import create_azure_folder, rename_azure_folder, delete_azure_folder_recursive, get_azure_directory_list
import os

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[DecodedToken, Depends(get_current_user)]
router = APIRouter(prefix="/directory", tags=["directory"])

# ユーザーの会社ストレージ名を取得する関数
def get_user_storage_name(db: Session, user_id: int) -> str:
    storage_name_query = db.query(Company)\
        .filter(Company.id == user_id)\
        .first()
    
    if not storage_name_query:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return storage_name_query.storage_name

@router.get('/get_all_directory', response_model=List[DirectoryResponse], status_code=status.HTTP_200_OK)
async def get_all_directories(db: DbDependency, user: UserDependency):
    query_result = (
        db.query(
            Directory.id,
            Directory.directory_name,
            Directory.path,
            Directory.directory_class
        )
        .outerjoin(
            Permission,
            and_(
                Directory.id == Permission.directory_id,
                Permission.user_id == user.user_id
            )
        )
        .filter(
            Directory.company_id == user.company_id,
            Directory.directory_class != 0,
            Directory.delete_flg == False,
            or_(
                Directory.open_flg == 0,  # 公開ディレクトリ
                Permission.id.isnot(None)  # ユーザーがアクセス権を持つディレクトリ
            )
        )
        .order_by(Directory.directory_name)
        .all()
    )

    get_result = [
        DirectoryResponse(
            directory_id=dir.id,
            directory_name=dir.directory_name,
            path=dir.path,
            directory_class=dir.directory_class
        ) for dir in query_result
    ]

    return get_result

@router.post("/add_directory", response_model=DirectoryResponse, status_code=status.HTTP_201_CREATED)
async def create_directory(db: DbDependency, user: UserDependency, directory_create: DirectoryCreate):

    # ユーザーの会社ストレージ名の取得
    storage_name = get_user_storage_name(db, user.company_id)
    
    # 追加対象のdirectory情報を取得
    directory_query = db.query(Directory)\
        .filter(
            Directory.company_id == user.company_id,
            Directory.id == directory_create.directory_id,
            Directory.delete_flg == False
        )\
        .first()
    
    if not directory_query:
        raise HTTPException(status_code=404, detail="Directory not found")

    # ディレクトリのパスを設定
    if directory_query.directory_class == 0:
        directory_path = None  
    else:
        # directory_pathがnullの場合、ディレクトリのパスはtarget_directory_query.directory_name + / に設定
        if directory_query.path is None:
            directory_path = directory_query.directory_name + '/'
        else:
            directory_path = directory_query.path + directory_query.directory_name + '/'

    # Directory.directory_nameとdirectory_create.nameの重複チェック
    directory_name_query = db.query(Directory)\
        .filter(
            Directory.company_id == user.company_id,
            Directory.directory_name == directory_create.directory_name,
            Directory.path == directory_path,
            Directory.delete_flg == False
        )\
        .first()
    
    if directory_name_query:
        raise HTTPException(status_code=400, detail="Directory name already exists")


    # ディレクトリの作成
    create_azure_folder(directory_create.directory_name, directory_path, storage_name)

    # ディレクトリクラスをカウント
    directory_class_count = 1 if directory_path is None else directory_path.count('/') + 1

    # ディレクトリ情報をデータベースに追加
    new_directory = Directory(
        directory_name=directory_create.directory_name,
        path=directory_path,
        directory_class = directory_class_count,
        company_id=user.company_id,
        open_flg=directory_create.open_flg,
        delete_flg=False,
        create_acc=user.user_id,
        create_at=datetime.now(),
        update_acc=user.user_id,
        update_at=datetime.now()
    )
    db.add(new_directory)
    db.commit()
    db.refresh(new_directory)

    add_result = DirectoryResponse(
        directory_id=new_directory.id,
        directory_name=new_directory.directory_name,
        path=new_directory.path,
        directory_class=new_directory.directory_class
    )

    return add_result

@router.post("/rename_directory", response_model=DirectoryResponse, status_code=status.HTTP_200_OK)
async def rename_directory(db: DbDependency, user: UserDependency, directory_rename: DirectoryRename):

    # ユーザーの会社ストレージ名の取得
    storage_name = get_user_storage_name(db, user.company_id)
    
    # リネーム対象のdirectory情報を取得
    target_directory_query = db.query(Directory)\
    .filter(
        Directory.id == directory_rename.directory_id,
        Directory.delete_flg == False,
        Directory.company_id == user.company_id
    )\
    .first()
    if not target_directory_query:
        raise HTTPException(status_code=404, detail="Directory not found")

    # Directory.directory_nameとdirectory_rename.new_directory_nameの重複チェック
    directory_name_query = db.query(Directory)\
        .filter(
            Directory.company_id == user.company_id,
            Directory.directory_name == directory_rename.new_directory_name,
            Directory.directory_class == target_directory_query.directory_class,
            Directory.delete_flg == False
        )\
        .first()
    if directory_name_query:
        raise HTTPException(status_code=400, detail="Directory name already exists")

    # Azure上のディレクトリ名を変更
    if target_directory_query.path == None:
        old_directory_path = target_directory_query.directory_name
        new_directory_path = directory_rename.new_directory_name
    else:
        old_directory_path = os.path.join(target_directory_query.path, target_directory_query.directory_name)
        new_directory_path = os.path.join(target_directory_query.path, directory_rename.new_directory_name)

    rename_azure_folder(old_directory_path, new_directory_path, storage_name)

    # ディレクトリ名を変更
    target_directory_query.directory_name = directory_rename.new_directory_name
    target_directory_query.update_acc = user.user_id
    target_directory_query.update_at = datetime.now()

    # 子ディレクトリのパスを更新
    old_path_prefix = old_directory_path + "/"
    new_path_prefix = new_directory_path + "/"
    child_directories = db.query(Directory).filter(
        Directory.path.like(old_path_prefix + "%"),
        Directory.company_id == user.company_id,
        Directory.delete_flg == False
    ).all()

    for child_directory in child_directories:
        # 正確な階層の部分を置換するために、旧パスプレフィックスを新パスプレフィックスに置換
        relative_path = child_directory.path[len(old_path_prefix):]
        child_directory.path = new_path_prefix + relative_path
        child_directory.update_acc = user.user_id
        child_directory.update_at = datetime.now()

    db.commit()
    db.refresh(target_directory_query)

    rename_result = DirectoryResponse(
        directory_id=target_directory_query.id,
        directory_name=target_directory_query.directory_name,
        path=target_directory_query.path,
        directory_class=target_directory_query.directory_class
    )

    return rename_result

@router.post("/delete_directory", response_model=DirectoryResponse, status_code=status.HTTP_200_OK)
async def delete_directory(db: DbDependency, user: UserDependency, directory_delete: DirectoryDelete):

    # ユーザーの会社ストレージ名の取得
    storage_name = get_user_storage_name(db, user.company_id)

    # 削除対象のdirectory情報を取得
    target_directory_query = db.query(Directory)\
        .filter(
            Directory.company_id == user.company_id,
            Directory.id == directory_delete.directory_id,
            Directory.delete_flg == False
        )\
        .first()

    # 削除対象のdirectory_classが0の場合、directory_pathはnull
    if target_directory_query.directory_class == 0:
        directory_path = None  
    else:
        # directory_pathがnullの場合、ディレクトリのパスはtarget_directory_query.directory_nameに設定
        if target_directory_query.path is None:
            directory_path = target_directory_query.directory_name + '/'
        else:
            directory_path = target_directory_query.path + target_directory_query.directory_name + '/'

    delete_azure_folder_recursive(directory_path, storage_name)

    # 親ディレクトリ情報に削除フラグを立てる
    target_directory_query.delete_flg = True
    target_directory_query.update_acc = user.user_id
    target_directory_query.update_at = datetime.now()

    child_directories = db.query(Directory).filter(
        Directory.path.like(directory_path + "%"),
        Directory.company_id == user.company_id,
        Directory.delete_flg == False
    ).all()

    # 子ディレクトリ情報に削除フラグを立てる
    for child_directory in child_directories:
        child_directory.delete_flg = True
        child_directory.update_acc = user.user_id
        child_directory.update_at = datetime.now()

    # 親ディレクトリと子ディレクトリに含まれるファイルに削除フラグを立てる
    directories_to_update = [target_directory_query.id] + [child_directory.id for child_directory in child_directories]

    files_to_update = db.query(File)\
        .filter(
            File.directory_id.in_(directories_to_update),
            File.delete_flg == False
        )\
        .all()

    for file in files_to_update:
        file.delete_flg = True
        file.update_acc = user.user_id
        file.update_at = datetime.now()

    db.commit()
    db.refresh(target_directory_query)

    delete_result = DirectoryResponse(
        directory_id=target_directory_query.id,
        directory_name=target_directory_query.directory_name,
        path=target_directory_query.path,
        directory_class=target_directory_query.directory_class
    )

    return delete_result

# Azureファイル共有に保存されている全てのディレクトリリストを取得する関数
@router.get('/get_azure_all_directory', status_code=status.HTTP_200_OK)
async def get_azure_all_directories(db: DbDependency, user: UserDependency):

    # ユーザーの会社ストレージ名の取得
    storage_name = get_user_storage_name(db, user.company_id)

    # ディレクトリリストを取得
    directories = get_azure_directory_list(storage_name)

    # ディレクトリ情報を返す
    return JSONResponse(content={"directories": directories})
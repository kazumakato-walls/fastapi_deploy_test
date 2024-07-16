from fastapi import Depends, APIRouter, HTTPException, status, UploadFile, File as FastAPIFile, Form
from fastapi.responses import FileResponse
from typing import List, Annotated, Union
from models import Directory, User, File, FileType, Company, Department
from schemas.files import FileGet, FileGetResponse, FileUploadData, FileUploadResponse, FileRenameResponse, FileRename, FileDelete, FileDownload, FileDeleteResponse
from schemas.directories import DirectoryGetResponse
from db import get_db
from sqlalchemy.orm import Session
from schemas.auth import DecodedToken
from auth import get_current_user
from azure_access import upload_file_to_azure, rename_azure_file, delete_azure_file, download_file_from_azure_to_stream
import mimetypes
from datetime import datetime
from urllib.parse import quote
from fastapi import BackgroundTasks
import shutil
import os

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[DecodedToken, Depends(get_current_user)]
router = APIRouter(prefix="/file", tags=["file"])

# ファイルサイズをKB,MB,GBに変換
def convert_file_size(size_in_kb: int) -> str:
    if size_in_kb < 1:
        return "1KB"  # 1KB以下の場合は切り上げて1KBとする

    units = ["KB", "MB", "GB", "TB"]
    index = 0
    size = size_in_kb
    
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1

    # 小数点第1位と第2位が0の場合は小数点以下を表示しない
    if size.is_integer():
        return f"{int(size)}{units[index]}"
    else:
        return f"{size:.2f}{units[index]}"

    # size_in_mb = size_in_bytes / 1024
    # size_in_gb = size_in_mb / 1024

    # if size_in_gb >= 1:
    #     return f"{size_in_gb:.2f}GB" if size_in_gb % 1 != 0 else f"{int(size_in_gb)}GB"
    # elif size_in_mb >= 1:
    #     return f"{size_in_mb:.2f}MB" if size_in_mb % 1 != 0 else f"{int(size_in_mb)}MB"
    # else:
    #     return f"{size_in_bytes:.2f}KB" if size_in_bytes % 1 != 0 else f"{int(size_in_bytes)}KB"

# ユーザーの会社ストレージ名を取得する関数
def get_user_storage_name(db: Session, user_id: int) -> str:
    storage_name_query = db.query(Company.storage_name)\
        .join(Department, Department.company_id == Company.id)\
        .join(User, User.department_id == Department.id)\
        .filter(User.id == user_id)\
        .first()
    
    if not storage_name_query:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return storage_name_query.storage_name

# ファイル一覧取得
@router.post('/get_all_file', response_model=List[Union[FileGetResponse, DirectoryGetResponse]], status_code=status.HTTP_200_OK)
async def file_get_all(db: DbDependency, user: UserDependency, file_get: FileGet):

    query_file_result = (
        db.query(
            File.id,
            File.directory_id,
            File.file_name,
            File.file_size,
            File.filetype_id,
            File.file_update_at,
            FileType.extension_name,
            FileType.icon,
            Directory.company_id,
        )
        .select_from(File)
        .outerjoin(
            FileType,
            File.filetype_id == FileType.id
            )
        .outerjoin(
            Directory,
            File.directory_id == Directory.id
            )
        .filter(
            Directory.company_id == user.company_id,
            File.directory_id == file_get.directory_id,
            File.delete_flg == False
        )
        .order_by(File.file_name)
        .all()
    )

    # 取得先ディレクトリの情報を取得
    query_first_result = db.query(Directory)\
        .filter(
            Directory.company_id == user.company_id,
            Directory.id == file_get.directory_id,
            Directory.open_flg == False,
            Directory.delete_flg == False
        )\
        .order_by(Directory.directory_name)\
        .first()
    
    if query_first_result is None:
        raise HTTPException(status_code=404, detail="Directory not found")
    
    # query_first_result.directory_classが0の場合、Directory.directory_class == 1のみ取得
    if query_first_result.directory_class == 0:
        query_directory_result = db.query(Directory)\
            .filter(
                Directory.company_id == user.company_id,
                Directory.id != query_first_result.id,
                Directory.path == None,
                Directory.directory_class == 1,
                Directory.open_flg == False,
                Directory.delete_flg == False
            )\
        .order_by(Directory.directory_name)\
        .all()

    else:
        # directory_pathがnullの場合、Directory.path == query_directory_path.directory_name + '/'の場合のみ取得
        if query_first_result.path is None:
            query_directory_result = db.query(Directory)\
                .filter(
                    Directory.id != query_first_result.id,
                    Directory.company_id == user.company_id,
                    Directory.path == query_first_result.directory_name + '/',
                    Directory.open_flg == False,
                    Directory.delete_flg == False
                    )\
                .order_by(Directory.directory_name)\
                .all()
        else:
            query_directory_result = db.query(Directory)\
                .filter(
                    Directory.id != query_first_result.id,
                    Directory.company_id == user.company_id,
                    Directory.path == query_first_result.path + query_first_result.directory_name + '/',
                    Directory.open_flg == False,
                    Directory.delete_flg == False
                    )\
                .order_by(Directory.directory_name)\
                .all()
            
    # 拡張子がない場合はファイル名から拡張子を取得
    get_file_result = []
    for file in query_file_result:
        if file.extension_name is None:
            file_extension = os.path.splitext(file.file_name)[1].lstrip('.')
            filetype_name = f"{file_extension}ファイル"
        else:
            filetype_name = file.extension_name

        get_file_result.append(
            FileGetResponse(
            id=file.id,
            file_name=file.file_name,
            file_size=convert_file_size(file.file_size),
            file_update_at=file.file_update_at.strftime('%Y-%m-%d %H:%M:%S'),
            filetype_name=filetype_name,
            icon_id=file.icon
        ))

    get_directory_result = [
        FileGetResponse(
            id=dir.id,
            file_name=dir.directory_name,
            file_size=None,
            file_update_at=dir.update_at.strftime('%Y-%m-%d %H:%M:%S'),
            filetype_name="ファイルフォルダー",
            icon_id=99,
        ) for dir in query_directory_result
    ]

    combined_result = get_directory_result + get_file_result

    return combined_result

# ファイルダウンロード
@router.post("/download_file", status_code=status.HTTP_200_OK)
async def download_file(db: DbDependency, user: UserDependency, file_download: FileDownload, background_tasks: BackgroundTasks):
    # ファイル情報の取得
    file_query = (
        db.query(
            File.id,
            File.file_name,
            File.file_size,
            File.filetype_id,
            File.file_update_at,
            Directory.directory_name,
            Directory.directory_class,
            Directory.path
        )
        .select_from(File)
        .outerjoin(Directory, File.directory_id == Directory.id)
        .filter(
            Directory.company_id == user.company_id,
            File.id == file_download.file_id,
            File.delete_flg == False
        )
        .first()
    )

    if file_query is None:
        raise HTTPException(status_code=404, detail="File not found")

    # ユーザーの会社ストレージ名の取得
    storage_name = get_user_storage_name(db, user.company_id)

    # ファイルのパスを取得
    if file_query.directory_class == 0:
        directory_path = ''
    else:
        if file_query.path is None:
            directory_path = file_query.directory_name + '/'
        else:
            directory_path = file_query.path + file_query.directory_name + '/'

    file_chunks = download_file_from_azure_to_stream(storage_name, directory_path, file_query.file_name)

    # ファイル名をRFC 5987形式でエンコード
    encoded_file_name = quote(file_query.file_name)
    print(encoded_file_name)

    # encoded_file_nameからMINEタイプを取得
    mime_type = mimetypes.guess_type(encoded_file_name)[0]
    if mime_type is None:
        mime_type = 'application/octet-stream'

    # バックグラウンドタスクとして一時ファイルを削除する
    background_tasks.add_task(remove_file, file_chunks)

    # フロントへファイルを渡す
    response = FileResponse(file_chunks, media_type='application/octet-stream', headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_file_name}"})
    # response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_file_name}"


    # print('receponse_body:',response.file_chunks)
    print('receponse_body:',response.media_type)
    print('receponse_body:',response.headers)
    return response

def remove_file(file_path: str):
    os.remove(file_path)

# ファイルアップロード
@router.post("/upload_file", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(db: DbDependency,user: UserDependency, directory_id: int = Form(...), file: UploadFile = FastAPIFile(...)):
    upload_file = FileUploadData(directory_id=directory_id)

    # ファイルサイズの特定（バイトからKBへ変換。）
    file_size_bytes = len(await file.read())
    print(file_size_bytes)
    file_size_kb = file_size_bytes / 1024
    if file_size_kb < 1:
        file_size_kb = 1
    await file.seek(0)

    # ファイル名の長さチェック
    if len(file.filename) > 255:
        raise HTTPException(status_code=400, detail="ファイル名は255文字以内で指定してください")

    # アップロード対象のストレージ容量をチェック
    storage_query = db.query(
        Company.storage.label('company_storage'),
        Department.storage.label('department_storage'))\
    .select_from(Department)\
    .join(
        Company, Company.id == Department.company_id)\
    .filter(
        Department.id == user.department_id)\
    .first()

    if storage_query is None:
        raise HTTPException(status_code=404, detail="ストレージ情報が見つかりません")

    # ユーザーが保存した全ファイルのサイズを取得
    user_files_query = db.query(File)\
    .filter(
        File.user_id == user.user_id
    )\
    .all()

    total_user_file_size_kb = sum(file.file_size for file in user_files_query)
    total_user_file_size_kb += file_size_kb

    if total_user_file_size_kb > user.storage:
        raise HTTPException(status_code=400, detail="ファイルサイズがユーザーのストレージ容量を超えています")

    # 部署の全てのファイルサイズを取得
    department_files_query = db.query(File).join(
        User, User.id == File.user_id
    ).filter(
        user.department_id == Department.id
    ).all()

    total_department_file_size_kb = sum(file.file_size for file in department_files_query)
    total_department_file_size_kb += file_size_kb

    if total_department_file_size_kb > storage_query.department_storage:
        raise HTTPException(status_code=400, detail="ファイルサイズが所属のストレージ容量を超えています")

    # 会社の全てのファイルサイズを取得
    company_files_query = db.query(File).join(
        User, User.id == File.user_id
    ).filter(
        user.company_id == Company.id
    ).all()

    total_company_file_size_kb = sum(file.file_size for file in company_files_query)
    total_company_file_size_kb += file_size_kb

    if total_company_file_size_kb > storage_query.company_storage:
        raise HTTPException(status_code=400, detail="ファイルサイズが会社のストレージ容量を超えています")

    # ユーザーの会社ストレージ名の取得
    storage_name = get_user_storage_name(db, user.user_id)

    # アップロード対象のディレクトリパス取得
    directory_query = db.query(Directory)\
        .filter(
            Directory.id == upload_file.directory_id,
            Directory.open_flg == False,
            Directory.delete_flg == False
        )\
        .first()

    if not directory_query:
        raise HTTPException(status_code=404, detail="Directory not found")

    if directory_query.directory_class == 0:
        azure_directory_path = ''
    else:
        if directory_query.path is None:
            azure_directory_path = directory_query.directory_name + '/'
        else:
            azure_directory_path = directory_query.path + directory_query.directory_name + '/'

    # 拡張子の特定
    file_extension = os.path.splitext(file.filename)[1]

    filetype_query = (
        db.query(FileType)
        .filter(
            FileType.extension == file_extension,
        ).first()
    )

    # ファイルタイプが見つからない場合はNoneを設定
    filetype_id = filetype_query.id if filetype_query else None

    # ファイル情報の更新または追加
    existing_file = db.query(File)\
    .filter(
        File.directory_id == upload_file.directory_id,
        File.file_name == file.filename,
        File.delete_flg == False
    ).first()

    if existing_file:
        # 既存ファイルの場合
        # 一時ファイルに保存
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Azureにファイルをアップロード
        upload_file_to_azure(temp_file_path, azure_directory_path, storage_name)

        # ファイルの更新日時を取得
        file_update_time = datetime.fromtimestamp(os.path.getmtime(temp_file_path))

        # ファイル情報をデータベースに反映
        existing_file.filetype_id = filetype_id,
        existing_file.file_size = file_size_kb,        
        existing_file.file_update_at = file_update_time
        existing_file.update_acc = user.user_id,
        existing_file.update_at = datetime.now()

        db.commit()
        db.refresh(existing_file)

        # ファイル情報を返す
        return FileUploadResponse(
            directory_id=existing_file.directory_id,
            file_name=existing_file.file_name,
            file_size=existing_file.file_size,
        )

    else:
        # 新規ファイルの場合
        # 一時ファイルに保存
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Azureにファイルをアップロード
        upload_file_to_azure(temp_file_path, azure_directory_path, storage_name)

        # ファイルの更新日時を取得
        file_update_time = datetime.fromtimestamp(os.path.getmtime(temp_file_path))

        # ファイル情報をデータベースに追加
        new_file = File(
            user_id=user.user_id,
            directory_id=upload_file.directory_id,
            filetype_id=filetype_id,
            file_name=file.filename,
            file_size=file_size_kb,
            delete_flg=False,
            file_update_at=file_update_time,
            create_acc=user.user_id,
            create_at=datetime.now(),
            update_acc=user.user_id,
            update_at=datetime.now()
        )
        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        return FileUploadResponse(
            directory_id=new_file.directory_id,
            file_id=new_file.id,
            file_name=new_file.file_name,
            file_size=new_file.file_size,
        )

@router.post("/rename_file", response_model=FileRenameResponse, status_code=status.HTTP_200_OK)
async def rename_file(db: DbDependency, user: UserDependency, file_rename: FileRename):

    # ユーザーの会社ストレージ名の取得
    storage_name = get_user_storage_name(db, user.company_id)

    # 現在のファイル名を取得
    old_name_query = db.query(
        File.file_name,
        File.directory_id,
        Directory.directory_name,
        Directory.path,
        Directory.directory_class
        )\
        .select_from(File)\
        .outerjoin(
            Directory, 
            File.directory_id == Directory.id
            )\
        .filter(
            File.id == file_rename.file_id,
            Directory.company_id == user.company_id,
            )\
        .first()

    if old_name_query is None:
        raise HTTPException(status_code=404, detail="File not found")

    if old_name_query.directory_class == 0:
        path = None
    else:
        if old_name_query.path is None:
            path = old_name_query.directory_name + '/'
        else:
            path = old_name_query.path + old_name_query.directory_name + '/'

    # Azureでのファイル名変更処理
    try:
        rename_azure_file(storage_name, path, old_name_query.file_name, file_rename.new_file_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    # データベース内のファイル名変更処理
    file = db.query(File)\
        .filter(File.id == file_rename.file_id)\
        .first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    file.file_name = file_rename.new_file_name
    file.update_acc = user.user_id
    file.update_at = datetime.now()

    db.commit()
    db.refresh(file)
    
    file_rename_result = FileRenameResponse(
        directory_id=file.directory_id,
        file_id=file_rename.file_id,
        old_directory_name=old_name_query.file_name,
        new_directory_name=file_rename.new_file_name
    )

    return file_rename_result

@router.post("/delete_file", response_model=FileDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_file(db: DbDependency, user: UserDependency, file_delete: FileDelete):

    # ユーザーの会社ストレージ名の取得
    storage_name = get_user_storage_name(db, user.company_id)

    # 現在のファイル名を取得
    file_name_query = db.query(
        File.file_name,
        File.directory_id,
        Directory.directory_name,
        Directory.path,
        Directory.directory_class
        )\
        .select_from(File)\
        .outerjoin(
            Directory, 
            File.directory_id == Directory.id
            )\
        .filter(
            File.id == file_delete.file_id,
            Directory.company_id == user.company_id,
            )\
        .first()

    if file_name_query is None:
        raise HTTPException(status_code=404, detail="File not found")

    if file_name_query.directory_class == 0:
        directory_path = None
    else:
        if file_name_query.path is None:
            directory_path = file_name_query.directory_name + '/'
        else:
            directory_path = file_name_query.path + file_name_query.directory_name + '/'

    delete_azure_file(storage_name, directory_path, file_name_query.file_name)

    # ファイル情報を取得
    target_file = db.query(File)\
        .filter(
            File.id == file_delete.file_id,
            File.delete_flg == False
        )\
        .first()

    if not target_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # ファイル情報を削除フラグを立てる
    target_file.delete_flg = True
    target_file.update_acc = user.user_id
    target_file.update_at = datetime.now()

    # データベースにコミット
    db.commit()
    db.refresh(target_file)

    delete_result = FileDeleteResponse(
        directory_id=target_file.directory_id,
        file_id=target_file.id,
        file_name=target_file.file_name
    )

    return delete_result

# 会社ファイル容量の合計値を各社ごとに取得(管理者用)
@router.post("/get_storage", response_model=List[FileGetResponse], status_code=status.HTTP_200_OK)
async def get_storage(db: DbDependency, user: UserDependency):
    
        # ユーザーが管理者でない場合はエラーを返す
        if not user.admin:
            raise HTTPException(status_code=403, detail="Forbidden")
    
        # 会社のファイル容量を取得
        company_storage_query = db.query(
            Company.id,
            Company.company_name,
            Company.storage_name,
            Company.storage
        ).all()
    
        # 各会社のファイル容量を取得
        company_storage_result = []
        for company in company_storage_query:
            # 会社のファイル容量を取得
            company_files_query = db.query(File)\
            .join(User, User.id == File.user_id)\
            .join(Department, Department.id == User.department_id)\
            .filter(
                Department.company_id == company.id
            )\
            .all()

            total_company_file_size_kb = sum(file.file_size for file in company_files_query)

            company_storage_result.append(
                FileGetResponse(
                    id=company.id,
                    file_name=company.company_name,
                    file_size=convert_file_size(total_company_file_size_kb),
                    file_update_at=None,
                    filetype_name=None,
                    icon_id=None
                )
            )
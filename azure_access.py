from azure.storage.fileshare import ShareServiceClient
from fastapi import HTTPException, status
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
import os
import time

# .envファイルを読み込む
load_dotenv()

# Azureポータルから取得した接続文字列
AZURE_STORAGE_CONNECTION_STRING = os.getenv('connection_string')
AZURE_SHARE_CLIENT_NAME = os.getenv('share_client_name')

if AZURE_STORAGE_CONNECTION_STRING is None:
    raise ValueError("AZURE_STORAGE_CONNECTION_STRING is not set. Please check your .env file.")

# Azure Storageのshare_clientを作成
def add_azure_share_client(azure_share_client_name: str):
    try:
        service_client = ShareServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        share_client = service_client.get_share_client(azure_share_client_name)
        share_client.create_share()
        print(f"Share client URL: {share_client.url}")  # デバッグログ
    except ResourceExistsError:
        print("Share client already exists")  # デバッグログ
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create share client: {repr(e)}"
        )
    
# Azure Storageのshare_clientを削除
def delete_azure_share_client(azure_share_client_name: str):
    try:
        service_client = ShareServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        share_client = service_client.get_share_client(azure_share_client_name)
        share_client.delete_share()
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Share client '{azure_share_client_name}' not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete share client: {repr(e)}"
        )

# Azure Storageのディレクトリクライアントを取得
def get_azure_directory_client(directory_path: str, azure_share_client_name: str):
    try:
        service_client = ShareServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        share_client = service_client.get_share_client(azure_share_client_name)
        directory_client = share_client.get_directory_client(directory_path)
        print(f"Directory client URL: {directory_client.url}")  # デバッグログ
        return directory_client
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get directory client: {repr(e)}"
        )

# Azure Storageからファイルをダウンロード
def download_file_from_azure_to_stream(storage_name: str, directory_path: str, file_name: str):
    # ファイルクライアントを取得
    file_client = get_azure_directory_client(directory_path, storage_name).get_file_client(file_name)

    # ファイルの存在確認    
    if not file_client.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_name}' not found"
        )
    
    # 一時ファイルを作成
    temp_file = NamedTemporaryFile(delete=False)
    temp_file.close()  # ファイルを閉じてからファイルクライアントに渡す

    # ファイルをダウンロードして一時ファイルに書き込む
    with open(temp_file.name, 'wb') as file_handle:
        downloader = file_client.download_file()
        downloader.readinto(file_handle)
    
    return temp_file.name
    
    # stream = file_client.download_file()
    # return stream.chunks()

# Azure Storageのフォルダを作成
def create_azure_folder(directory_name: str, parent_path: str, storage_name: str) -> str:    
    full_path = os.path.join(parent_path, directory_name) if parent_path else directory_name
    directory_client = get_azure_directory_client(full_path, storage_name)

    try:
        directory_client.create_directory()
    except ResourceExistsError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="同名のフォルダが存在しています")

def delete_azure_folder(directory_path: str, storage_name: str):
    directory_client = get_azure_directory_client(directory_path, storage_name)
    
    # ディレクトリ内のすべてのファイルとサブディレクトリを再帰的に削除
    for item in directory_client.list_directories_and_files():
        item_path = os.path.join(directory_path, item['name'])
        if item['is_directory']:
            delete_azure_folder(item_path, storage_name)
        else:
            file_client = directory_client.get_file_client(item['name'])
            file_client.delete_file()

    # 最後にディレクトリ自体を削除
    try:
        directory_client.delete_directory()
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="変更対象のディレクトリが存在しません")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"フォルダの削除に失敗しました: {str(e)}")

# Azure Storageのフォルダを再帰的に削除
def delete_azure_folder_recursive(directory_path: str, storage_name: str):
    directory_client = get_azure_directory_client(directory_path, storage_name)
    
    try:
        # ディレクトリ内のアイテムを取得
        items = directory_client.list_directories_and_files()
        
        # ディレクトリ内のすべてのファイルとサブディレクトリを削除
        for item in items:
            item_path = os.path.join(directory_path, item['name'])
            if item['is_directory']:
                delete_azure_folder_recursive(item_path, storage_name)  # 再帰的にサブディレクトリを削除
            else:
                file_client = directory_client.get_file_client(item['name'])
                file_client.delete_file()  # ファイルを削除

        # 最後にディレクトリ自体を削除
        directory_client.delete_directory()
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Directory not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Azure Storageのフォルダが存在するか確認
def check_azure_folder_exists(directory_path: str) -> bool:
    directory_client = get_azure_directory_client(directory_path)
    try:
        directory_client.get_directory_properties()
        return True
    except ResourceNotFoundError:
        return False

# Azure Storageのファイルをリネーム
def rename_azure_folder(old_directory_path: str, new_directory_path: str, storage_name: str):
    if not old_directory_path or not new_directory_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both old and new directory paths are required")
    
    old_directory_client = get_azure_directory_client(old_directory_path, storage_name)
    new_directory_client = get_azure_directory_client(new_directory_path, storage_name)

    # デバッグ用ログ
    print(f"Old directory URL: {old_directory_client.url}")
    print(f"New directory URL: {new_directory_client.url}")
    
    try:
        # 新しいディレクトリが存在しない場合のみ作成
        try:
            new_directory_client.create_directory()
        except ResourceExistsError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新しいディレクトリが既に存在しています")

        for item in old_directory_client.list_directories_and_files():
            if item['is_directory']:
                rename_azure_folder(os.path.join(old_directory_path, item['name']), os.path.join(new_directory_path, item['name']), storage_name)
            else:
                old_file_client = old_directory_client.get_file_client(item['name'])
                new_file_client = new_directory_client.get_file_client(item['name'])
                new_file_client.start_copy_from_url(old_file_client.url)
        
        delete_azure_folder(old_directory_path, storage_name)
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Directory not found")


# Azure Storageにファイルをアップロード
def upload_file_to_azure(file_path: str, directory_path: str, storage_name: str) -> str:

    file_name = os.path.basename(file_path)
    directory_client = get_azure_directory_client(directory_path, storage_name)
    file_client = directory_client.get_file_client(file_name)

    try:
        with open(file_path, "rb") as source_file:
            file_client.upload_file(source_file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ファイルのアップロードに失敗しました: {repr(e)}"
        )

    return file_client.url

# Azure Storageのファイルをリネーム
def rename_azure_file(storage_name: str, directory_path: str, old_file_name: str, new_file_name: str):
    try:
        directory_client = get_azure_directory_client(directory_path, storage_name)
        old_file_client = directory_client.get_file_client(old_file_name)
        new_file_client = directory_client.get_file_client(new_file_name)

        # デバッグ用ログ
        print(f"Old file URL: {old_file_client.url}")
        print(f"New file URL: {new_file_client.url}")

        # ファイルの存在確認
        if not old_file_client.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Old file '{old_file_name}' does not exist"
            )

        # ファイルをコピー
        new_file_client.start_copy_from_url(old_file_client.url)

        # コピーが完了するまで待つ
        max_retries = 10
        retries = 0
        while retries < max_retries:
            properties = new_file_client.get_file_properties()
            copy_status = properties.copy.status
            if copy_status == "success":
                break
            elif copy_status == "pending":
                time.sleep(1)  # 1秒待機
                retries += 1
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"ファイルのコピーに失敗しました: {copy_status}"
                )

        if copy_status != "success":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ファイルのコピーに失敗しました"
            )

        # 元のファイルを削除
        old_file_client.delete_file()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ファイルのリネームに失敗しました: {repr(e)}"
        )
    
# Azure Storageのファイルを削除
def delete_azure_file(storage_name: str, directory_path: str, file_name: str):
    try:
        directory_client = get_azure_directory_client(directory_path, storage_name)
        file_client = directory_client.get_file_client(file_name)
        
        if not file_client.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{file_name}' not found"
            )
        
        file_client.delete_file()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {repr(e)}"
        )
    
# Azure ファイル共有に保存されている全てのディレクトリリストを取得
def get_azure_directory_list(storage_name: str):
    try:
        service_client = ShareServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        share_client = service_client.get_share_client(storage_name)
        return [item['name'] for item in share_client.list_directories_and_files()]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get directory list: {repr(e)}"
        )
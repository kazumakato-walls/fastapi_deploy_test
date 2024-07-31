# -*- coding: utf-8 -*-
# DBへの接続設定
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# .envから環境変数を読み込む
load_dotenv()

# 接続したいDBの基本情報を設定
USER_NAME = os.getenv('user_name')
PASSWORD = os.getenv('password')
HOST = os.getenv('host')
DATABASE_NAME = os.getenv('database_name')

# 接続URLの作成
DATABASE_URL = f'mysql+pymysql://{USER_NAME}:{PASSWORD}@{HOST}/{DATABASE_NAME}?charset=utf8'

# SSLオプションの追加
ssl_args = {
    "ssl": {
        "ca": "/etc/ssl/certs/ca-certificates.crt"
    }
}

# DBとの接続
ENGINE = create_engine(
    DATABASE_URL,
    connect_args=ssl_args,
    encoding="utf-8",
    echo=True
)

# modelで使用する
Base = declarative_base()

#SQL接続
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=ENGINE)
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    

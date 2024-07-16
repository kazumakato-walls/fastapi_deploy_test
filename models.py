from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.types import Date, DateTime
from db import Base
from db import ENGINE

class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True)
    industry_id = Column(Integer)
    region_id = Column(Integer)
    company_name = Column(String(100), nullable=False)
    storage_name = Column(String(100), nullable=False)
    tell = Column(String(100), nullable=False)
    storage = Column(Integer, nullable=False)
    create_at = Column(DateTime, nullable=False)
    create_acc = Column(Integer)
    update_at = Column(DateTime)
    update_acc = Column(Integer)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    personal_id = Column(String(50), nullable=False)
    user_name = Column(String(50), nullable=False)
    name_kana = Column(String(100))
    email = Column(String(100))
    password = Column(String(100))
    salt = Column(String(100), nullable=False)
    age = Column(Date)
    sex = Column(String(10))
    storage = Column(Integer, nullable=False)
    permission = Column(Boolean, nullable=False)
    admin = Column(Boolean, nullable=False)
    icon = Column(String(500))
    delete_flg = Column(Boolean, nullable=False)
    create_at = Column(DateTime)
    update_at = Column(DateTime)
    memo = Column(String(800))

class Directory(Base):
    __tablename__ = 'cd_directories'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    path = Column(String(1000), nullable=False)
    directory_name = Column(String(100), nullable=False)
    directory_class = Column(Integer, nullable=False)
    open_flg = Column(Boolean, nullable=False)
    delete_flg = Column(Boolean, nullable=False)
    create_at = Column(DateTime)
    create_acc = Column(Integer, ForeignKey('users.id'), nullable=False)
    update_at = Column(DateTime)
    update_acc = Column(Integer)

class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    department_name = Column(String(100), nullable=False)
    storage = Column(Integer, nullable=False)
    memo = Column(String(500))
    create_at = Column(DateTime)
    create_acc = Column(Integer, ForeignKey('users.id'), nullable=False)
    update_at = Column(DateTime)
    update_acc = Column(Integer)

class Assignment(Base):
    __tablename__ = 'assignments'
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    delete_flg = Column(Boolean, nullable=False)
    create_at = Column(DateTime)
    create_acc = Column(Integer, ForeignKey('users.id'), nullable=False)
    update_at = Column(DateTime)
    update_acc = Column(Integer)

class Permission(Base):
    __tablename__ = 'cd_permissions'
    id = Column(Integer, primary_key=True)
    directory_id = Column(Integer, ForeignKey('cd_directories.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    create_at = Column(DateTime)
    create_acc = Column(Integer, ForeignKey('users.id'), nullable=False)
    update_at = Column(DateTime)
    update_acc = Column(Integer)

class File(Base):
    __tablename__ = 'cd_files'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    directory_id = Column(Integer, ForeignKey('cd_directories.id'), nullable=False)
    filetype_id = Column(Integer, ForeignKey('filetypes.id'))
    file_name = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    delete_flg = Column(Boolean, nullable=False)
    file_update_at = Column(DateTime)
    create_at = Column(DateTime)
    create_acc = Column(Integer, ForeignKey('users.id'), nullable=False)
    update_at = Column(DateTime)
    update_acc = Column(Integer)

class Favorite(Base):
    __tablename__ = 'cd_favorites'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    directory_id = Column(Integer, ForeignKey('cd_directories.id'), nullable=False)
    favorite_name = Column(String(400), nullable=False)
    create_at = Column(DateTime)
    update_at = Column(DateTime)

class FileType(Base):
    __tablename__ = 'filetypes'
    id = Column(Integer, primary_key=True)
    extension = Column(String(5), nullable=False)
    extension_name = Column(String(50), nullable=False)
    icon = Column(Integer)

class Region(Base):
    __tablename__ = 'regions'
    id = Column(Integer, primary_key=True)
    country = Column(String(50), nullable=False)
    country_code = Column(String(6), nullable=False)
    region = Column(String(100), nullable=False)
    region_code = Column(String(6), nullable=False)

class Industry(Base):
    __tablename__ = 'industries'
    id = Column(Integer, primary_key=True)
    industry_code = Column(String(2), nullable=False)
    industry_name = Column(String(30), nullable=False)

def main():
    # テーブルが存在しなければ、テーブルを作成
    Base.metadata.create_all(bind=ENGINE)
    
if __name__ == "__main__":
    main() 

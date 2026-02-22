from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import logging


# DB Base Settings
DB_URL = "sqlite:///./attendance.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    user_pass = Column(String)

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    attend_time = Column(DateTime, default=datetime.now)

def init_db():
    """テーブル作成と初期ユーザー登録を行う関数"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.user_id == "aaa").first():
            db.add(User(user_id="aaa", user_pass="111"))
            db.commit()
    finally:
        db.close()

# --- データベース操作関数 (CRUD) ---
def get_db():
    """セッションを生成・提供するジェネレータ関数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def authenticate_user(db: Session, user_id: str, user_pass: str):
    """ユーザー認証を行う関数"""
    return db.query(User).filter(User.user_id == user_id, User.user_pass == user_pass).first()

def create_attendance_record(db: Session, user_id: str):
    """打刻データを保存する関数"""
    now = datetime.now()
    new_record = Attendance(user_id=user_id, attend_time=now)
    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record
    except Exception as e:
        db.rollback()
        logger.error(f'Registration Error: {e}')
        raise e

# --- FastAPIメイン設定 ---
app = FastAPI()
init_db() # アプリ起動時に実行

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AttendanceRequest(BaseModel):
    user_id: str
    user_pass: str

# --- APIエンドポイント ---
@app.get('/')
async def read_index():
    return FileResponse('./static/index.html')

@app.post('/api/CheckIn')
async def checkin(req: AttendanceRequest, db: Session = Depends(get_db)):
    
    try:
        user = authenticate_user(db, req.user_id, req.user_pass)
        
        if not user:
            raise HTTPException(status_code=401, detail="認証に失敗しました \n ユーザーIDとパスワードを確認してください")

        # loggin success
        record = create_attendance_record(db, req.user_id)

        return {
            "status": 'CheckIn',
            "time": record.attend_time.strftime('%Y-%m-%d %H:%M:%S'),
            "username": record.user_id
            }

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(status_code=500, detail="サーバー内でエラーが発生しました")
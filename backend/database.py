"""
Revixa — SQLAlchemy ORM Database Architecture
==============================================
Kullanıcı hesapları, kaydedilen uygulamalar ve özel API anahtarları için veritabanı altyapısı.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "revixa_v2.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    saved_apps = relationship("SavedAppDB", back_populates="owner", cascade="all, delete-orphan")
    api_keys = relationship("UserAPIKeyDB", back_populates="owner", cascade="all, delete-orphan")


class SavedAppDB(Base):
    __tablename__ = "saved_apps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    play_url = Column(Text, nullable=True)
    appstore_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("UserDB", back_populates="saved_apps")


class UserAPIKeyDB(Base):
    __tablename__ = "user_api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # openai, claude, deepseek, gemini
    api_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("UserDB", back_populates="api_keys")


def init_db():
    """Tüm veritabanı tablolarını oluşturur."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI için veritabanı oturum bağımlılığı (dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

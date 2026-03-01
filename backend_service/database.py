"""
穹盾智矿 - 核心业务数据库引擎 (MySQL + SQLAlchemy)
包含：设备台账、用户权限(RBAC)、告警记录
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# MySQL 连接字符串 (与 docker-compose.yml 保持一致)
DATABASE_URL = (
    "mysql+pymysql://msm_user:msm_pass@127.0.0.1:3306/mining_system?charset=utf8mb4"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
穹盾智矿 - 核心业务管理 API
提供: 用户认证、设备CRUD、告警规则引擎、告警记录查询
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import timedelta, datetime

from database import engine, get_db, Base
from models import User, Device, DeviceType, AlertRule, AlertRecord, RoleEnum
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    require_role,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# ---- 创建所有表 ----
Base.metadata.create_all(bind=engine)

# ---- FastAPI 应用 ----
app = FastAPI(title="穹盾智矿 - 核心业务管理平台", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================
#   Pydantic 请求/响应模型
# ==============================


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str = ""
    role: RoleEnum = RoleEnum.viewer


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: RoleEnum
    is_active: bool

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DeviceCreate(BaseModel):
    device_id: str
    device_name: str = ""
    device_type: DeviceType
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    altitude: Optional[float] = None
    install_location: str = ""


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    altitude: Optional[float] = None
    install_location: Optional[str] = None
    status: Optional[str] = None


class DeviceOut(BaseModel):
    id: int
    device_id: str
    device_name: str
    device_type: DeviceType
    longitude: Optional[float]
    latitude: Optional[float]
    altitude: Optional[float]
    install_location: str
    status: str

    class Config:
        from_attributes = True


class AlertRuleCreate(BaseModel):
    device_id: str
    metric_field: str
    operator: str = ">"
    threshold: float
    alert_level: str = "warning"
    description: str = ""


class AlertRuleOut(BaseModel):
    id: int
    device_id: str
    metric_field: str
    operator: str
    threshold: float
    alert_level: str
    description: str
    is_enabled: bool

    class Config:
        from_attributes = True


class AlertRecordOut(BaseModel):
    id: int
    device_id: str
    metric_field: str
    metric_value: float
    threshold: float
    alert_level: str
    message: str
    is_acknowledged: bool
    triggered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==============================
#   初始化：自动创建默认管理员
# ==============================


@app.on_event("startup")
def seed_admin():
    """启动时自动创建默认管理员账户"""
    db = next(get_db())
    existing = db.query(User).filter(User.username == "admin").first()
    if not existing:
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="系统管理员",
            role=RoleEnum.admin,
        )
        db.add(admin)
        db.commit()
        print("✅ 默认管理员账户已创建: admin / admin123")
    db.close()


# ==============================
#   1. 认证接口
# ==============================


@app.post("/api/v1/auth/login", response_model=TokenOut, tags=["认证"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """用户登录，返回 JWT Token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@app.get("/api/v1/auth/me", response_model=UserOut, tags=["认证"])
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user


@app.post("/api/v1/auth/register", response_model=UserOut, tags=["认证"])
def register_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(RoleEnum.admin)),
):
    """注册新用户 (仅管理员)"""
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=data.username,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ==============================
#   2. 设备资产 CRUD
# ==============================


@app.get("/api/v1/devices", response_model=List[DeviceOut], tags=["设备资产"])
def list_devices(
    device_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """查询设备列表（支持按类型、状态过滤）"""
    q = db.query(Device)
    if device_type:
        q = q.filter(Device.device_type == device_type)
    if status:
        q = q.filter(Device.status == status)
    return q.order_by(Device.id.desc()).all()


@app.get("/api/v1/devices/{device_id}", response_model=DeviceOut, tags=["设备资产"])
def get_device(device_id: str, db: Session = Depends(get_db)):
    """查询单个设备详情"""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@app.post("/api/v1/devices", response_model=DeviceOut, tags=["设备资产"])
def create_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(RoleEnum.admin, RoleEnum.engineer)),
):
    """新增设备 (管理员/工程师)"""
    if db.query(Device).filter(Device.device_id == data.device_id).first():
        raise HTTPException(status_code=400, detail="设备ID已存在")
    device = Device(**data.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@app.put("/api/v1/devices/{device_id}", response_model=DeviceOut, tags=["设备资产"])
def update_device(
    device_id: str,
    data: DeviceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(RoleEnum.admin, RoleEnum.engineer)),
):
    """修改设备信息 (管理员/工程师)"""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    db.commit()
    db.refresh(device)
    return device


@app.delete("/api/v1/devices/{device_id}", tags=["设备资产"])
def delete_device(
    device_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(RoleEnum.admin)),
):
    """删除设备 (仅管理员)"""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    db.delete(device)
    db.commit()
    return {"status": "success", "message": f"设备 {device_id} 已删除"}


# ==============================
#   3. 告警规则引擎
# ==============================


@app.get("/api/v1/alert-rules", response_model=List[AlertRuleOut], tags=["告警规则"])
def list_alert_rules(device_id: Optional[str] = None, db: Session = Depends(get_db)):
    """查询告警规则列表"""
    q = db.query(AlertRule)
    if device_id:
        q = q.filter(AlertRule.device_id == device_id)
    return q.all()


@app.post("/api/v1/alert-rules", response_model=AlertRuleOut, tags=["告警规则"])
def create_alert_rule(
    data: AlertRuleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(RoleEnum.admin, RoleEnum.engineer)),
):
    """创建告警规则 (管理员/工程师)"""
    device = db.query(Device).filter(Device.device_id == data.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="关联设备不存在")
    rule = AlertRule(**data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@app.delete("/api/v1/alert-rules/{rule_id}", tags=["告警规则"])
def delete_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(RoleEnum.admin)),
):
    """删除告警规则 (仅管理员)"""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    db.delete(rule)
    db.commit()
    return {"status": "success", "message": f"规则 #{rule_id} 已删除"}


# ==============================
#   4. 告警记录查询
# ==============================


@app.get(
    "/api/v1/alert-records", response_model=List[AlertRecordOut], tags=["告警记录"]
)
def list_alert_records(
    device_id: Optional[str] = None,
    alert_level: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """查询告警记录 (支持过滤)"""
    q = db.query(AlertRecord)
    if device_id:
        q = q.filter(AlertRecord.device_id == device_id)
    if alert_level:
        q = q.filter(AlertRecord.alert_level == alert_level)
    if acknowledged is not None:
        q = q.filter(AlertRecord.is_acknowledged == acknowledged)
    return q.order_by(AlertRecord.triggered_at.desc()).limit(limit).all()


@app.put("/api/v1/alert-records/{record_id}/ack", tags=["告警记录"])
def acknowledge_alert(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """确认/处理一条告警"""
    record = db.query(AlertRecord).filter(AlertRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="告警记录不存在")
    record.is_acknowledged = True
    db.commit()
    return {"status": "success", "message": f"告警 #{record_id} 已确认处理"}


# ==============================
#   5. 健康检查
# ==============================


@app.get("/", tags=["系统"])
def health_check():
    return {"status": "ok", "service": "穹盾智矿 - 核心业务管理平台", "version": "2.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)

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
import math
import random

from database import engine, get_db, Base
from models import (
    User,
    Device,
    DeviceType,
    AlertRule,
    AlertRecord,
    RoleEnum,
    UAVMission,
    ProductionRecord,
    ProductionTask,
)
from settings import CORS_ALLOW_ORIGINS, DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD
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
    allow_origins=CORS_ALLOW_ORIGINS,
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
    created_at: Optional[datetime] = None

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
def seed_data():
    """启动时自动填充初始数据"""
    db = next(get_db())
    # 1. 创建默认管理员
    existing_admin = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
    if not existing_admin:
        admin = User(
            username=DEFAULT_ADMIN_USERNAME,
            hashed_password=get_password_hash(DEFAULT_ADMIN_PASSWORD),
            full_name="系统管理员",
            role="admin",
        )
        db.add(admin)
        print("✅ 默认管理员账户已创建")

    # 2. 填充初始生产运营数据 (如果为空)
    if db.query(ProductionRecord).count() == 0:
        now = datetime.now()
        records = [
            ProductionRecord(
                tonnage=450.5,
                efficiency=85.2,
                fuel_consumption=1200.0,
                active_vehicles=12,
                shift_name="昼班",
            ),
            ProductionRecord(
                tonnage=380.2,
                efficiency=78.5,
                fuel_consumption=1050.0,
                active_vehicles=10,
                shift_name="夜班",
            ),
        ]
        db.add_all(records)
        print("✅ 初始生产运营数据已填充")

    db.commit()
    db.close()


# ==============================
#   Pydantic 生产运营相关模型
# ==============================


class ProductionOut(BaseModel):
    id: int
    timestamp: datetime
    shift_name: str
    material_type: str
    tonnage: float
    efficiency: float
    fuel_consumption: float
    active_vehicles: int
    location_zone: str

    class Config:
        from_attributes = True


class ProductionKPI(BaseModel):
    total_tonnage: float
    avg_efficiency: float
    total_fuel: float
    active_vehicle_count: int
    daily_trend: List[ProductionOut]


class AssetStat(BaseModel):
    online: int
    total: int


class MiningSummaryOut(BaseModel):
    safety_status: str
    asset_stats: dict
    production_today: dict
    recent_alerts: List[AlertRecordOut]
    environment: dict
    operation_logs: List[dict]
    cost_metrics: List[dict]
    key_equipment: List[dict]
    material_quality: List[dict]
    logistic_chokepoints: List[dict]
    stripping_progress: dict
    equipment_oee: dict


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


@app.get("/api/v1/users", response_model=List[UserOut], tags=["认证"])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(RoleEnum.admin)),
):
    """获取所有用户信息"""
    return db.query(User).order_by(User.id.desc()).all()


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
#   5. UAV 空天指控集群
# ==============================


class UAVMissionCreate(BaseModel):
    device_id: str
    mission_name: str
    waypoints: str


class UAVMissionOut(BaseModel):
    id: int
    device_id: str
    mission_name: str
    waypoints: str
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@app.get("/api/v1/uav/missions", response_model=List[UAVMissionOut], tags=["UAV指控"])
def get_missions(device_id: Optional[str] = None, db: Session = Depends(get_db)):
    """获取无人机任务列表"""
    q = db.query(UAVMission)
    if device_id:
        q = q.filter(UAVMission.device_id == device_id)
    return q.order_by(UAVMission.id.desc()).all()


@app.post("/api/v1/uav/missions", response_model=UAVMissionOut, tags=["UAV指控"])
def create_mission(
    data: UAVMissionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(RoleEnum.admin, RoleEnum.engineer)),
):
    """下发新的无人机巡飞任务"""
    device = (
        db.query(Device)
        .filter(Device.device_id == data.device_id, Device.device_type == "uav")
        .first()
    )
    if not device:
        raise HTTPException(
            status_code=404,
            detail="未找到对应的 UAV 设备，可能该设备不存在或不是无人机",
        )

    mission = UAVMission(**data.model_dump())
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission


@app.post("/api/v1/uav/{device_id}/command", tags=["UAV指控"])
def send_uav_command(
    device_id: str,
    command: str = Query(
        ...,
        description="控制指令: takeoff (起飞), rth (返航), hover (悬停), land (降落)",
    ),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(RoleEnum.admin, RoleEnum.engineer)),
):
    """直接下发 UAV 控制指令并执行"""
    valid_commands = ["takeoff", "rth", "hover", "land"]
    if command not in valid_commands:
        raise HTTPException(
            status_code=400, detail=f"无效的控制指令, 可选值: {valid_commands}"
        )

    # 模拟向边缘侧发送 MQTT 消息等...
    return {
        "status": "success",
        "device_id": device_id,
        "command": command,
        "message": f"指令 [{command}] 成功发送到设备集群",
    }


# ==============================
#   Pydantic 生产运营相关模型
# ==============================


class ProductionOut(BaseModel):
    id: int
    timestamp: datetime
    shift_name: str
    material_type: str
    tonnage: float
    efficiency: float
    fuel_consumption: float
    active_vehicles: int
    location_zone: str

    class Config:
        from_attributes = True


class ProductionKPI(BaseModel):
    total_tonnage: float
    avg_efficiency: float
    total_fuel: float
    active_vehicle_count: int
    daily_trend: List[ProductionOut]


class TaskCreate(BaseModel):
    vehicle_id: str
    excavator_id: Optional[str] = None
    load_zone: str
    unload_zone: str
    material: str = "矿石"
    weight_tons: float


class TaskOut(BaseModel):
    id: int
    task_id: str
    vehicle_id: str
    load_zone: str
    unload_zone: str
    status: str
    weight_tons: float
    start_time: datetime

    class Config:
        from_attributes = True


# ==============================
#   6. 生产运营 (Ops) - 指挥中心深度接口
# ==============================


def get_demo_scene(now: Optional[datetime] = None):
    now = now or datetime.now()
    cycle = 360
    sec = int(now.timestamp()) % cycle
    if sec < 150:
        phase = 'stable'; progress = sec / 150
    elif sec < 220:
        phase = 'precursor'; progress = (sec - 150) / 70
    elif sec < 280:
        phase = 'warning'; progress = (sec - 220) / 60
    elif sec < 330:
        phase = 'dispatch'; progress = (sec - 280) / 50
    else:
        phase = 'recovery'; progress = (sec - 330) / 30
    return phase, max(0.0, min(1.0, progress)), sec


@app.get(
    "/api/v1/ops/mining-summary", response_model=MiningSummaryOut, tags=["生产运营"]
)
def get_mining_summary(db: Session = Depends(get_db)):
    """矿山总览：按真实演示场景构造统一联动数据"""
    now = datetime.now()
    phase, progress, sec = get_demo_scene(now)

    asset_map = {
        'excavator': {'online': 12, 'total': 15},
        'truck': {'online': 41, 'total': 45},
        'uav': {'online': 4 if phase in ['stable', 'precursor'] else 5, 'total': 5},
        'crusher': {'online': 2, 'total': 2},
    }
    if phase == 'warning':
        asset_map['truck']['online'] = 38
    elif phase == 'dispatch':
        asset_map['truck']['online'] = 35
        asset_map['excavator']['online'] = 10
    elif phase == 'recovery':
        asset_map['truck']['online'] = 39
        asset_map['excavator']['online'] = 11

    today_zero = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed_hours = max(0.0, (now - today_zero).total_seconds() / 3600)
    base_output = 180 * min(elapsed_hours, 2) + 240 * max(elapsed_hours - 2, 0)
    scene_bonus = {'stable': 0, 'precursor': 18, 'warning': 35, 'dispatch': 12, 'recovery': 20}[phase]
    current = round(base_output + scene_bonus + now.minute * 2.6 + now.second * 0.045, 1)
    efficiency = {'stable': 87.5, 'precursor': 84.2, 'warning': 76.8, 'dispatch': 71.5, 'recovery': 82.6}[phase]
    prod_stats = {
        'current': current,
        'target': 5000.0,
        'efficiency': efficiency,
        'material_stock': round(146.0 - elapsed_hours * 0.55, 1),
        'fuel_stock': round(139.5 - elapsed_hours * 1.1, 1),
    }

    if phase == 'stable':
        safety = 'green'
        recent = [
            {'id': 1, 'device_id': 'CM-001', 'metric_field': 'crack_width_mm', 'metric_value': 2.1, 'threshold': 4.0, 'alert_level': 'info', 'message': '边坡监测稳定，处于正常巡检区间', 'is_acknowledged': True, 'triggered_at': now},
        ]
    elif phase == 'precursor':
        safety = 'yellow'
        recent = [
            {'id': 1, 'device_id': 'MS-001', 'metric_field': 'energy_level', 'metric_value': 24.6, 'threshold': 20.0, 'alert_level': 'warning', 'message': '微震能级连续抬升，建议加密巡检频次', 'is_acknowledged': False, 'triggered_at': now},
        ]
    elif phase == 'warning':
        safety = 'yellow'
        recent = [
            {'id': 1, 'device_id': 'CM-001', 'metric_field': 'crack_width_mm', 'metric_value': 4.3, 'threshold': 4.0, 'alert_level': 'warning', 'message': '裂缝宽度接近预警阈值，已进入重点监控', 'is_acknowledged': False, 'triggered_at': now},
            {'id': 2, 'device_id': 'IN-001', 'metric_field': 'angle_x', 'metric_value': 0.22, 'threshold': 0.2, 'alert_level': 'warning', 'message': '边坡倾角出现持续偏移', 'is_acknowledged': False, 'triggered_at': now},
        ]
    elif phase == 'dispatch':
        safety = 'red'
        recent = [
            {'id': 1, 'device_id': 'SLOPE-ZONE-A', 'metric_field': 'risk_score', 'metric_value': 86.0, 'threshold': 70.0, 'alert_level': 'danger', 'message': '边坡风险升至二级预警，无人机已起飞核查', 'is_acknowledged': False, 'triggered_at': now},
            {'id': 2, 'device_id': 'CM-001', 'metric_field': 'crack_width_mm', 'metric_value': 5.2, 'threshold': 4.0, 'alert_level': 'danger', 'message': '裂缝扩展速率升高，建议限制临近作业', 'is_acknowledged': False, 'triggered_at': now},
        ]
    else:
        safety = 'yellow'
        recent = [
            {'id': 1, 'device_id': 'SLOPE-ZONE-A', 'metric_field': 'risk_score', 'metric_value': 48.0, 'threshold': 70.0, 'alert_level': 'warning', 'message': '现场复核完成，风险回落至持续观察', 'is_acknowledged': False, 'triggered_at': now},
        ]

    logs_map = {
        'stable': ['1#铲完成第18车装载，运输链路正常', 'UAV-EAGLE-01 按计划巡检边坡北侧', '破碎站皮带负载稳定，当前连续运行', '调度中心完成一轮常规生产核验'],
        'precursor': ['微震监测能级抬升，系统自动提高采样频率', '调度中心将边坡北侧列入重点观察区域', '1#铲作业正常，临近边坡车辆限速提醒已下发', 'AI 风险模型进入增强分析模式'],
        'warning': ['裂缝计与倾角计出现协同异常，值班长已确认', '系统下发边坡北侧作业减速指令', '无人机巡检任务进入待命队列', '调度中心保留运输主线，压缩临边作业窗口'],
        'dispatch': ['UAV-EAGLE-01 已起飞，前往 SLOPE-ZONE-A 核查', '边坡北侧临近车辆已执行绕行', 'AI 风险模型维持二级预警输出', '现场管理人员正在等待无人机图传回传'],
        'recovery': ['无人机核查结束，边坡区域已转入持续观察', '临边车辆恢复限流通行，作业强度仍受控', 'AI 模型风险评分持续回落', '值班长记录本轮预警处置闭环'],
    }
    operation_logs = [
        {'time': (now - timedelta(seconds=i * 45)).strftime('%H:%M:%S'), 'event': text, 'level': 'warning' if phase in ['warning', 'dispatch'] and i < 2 else ('info' if 'AI' in text or '无人机' in text or 'UAV' in text else 'normal')}
        for i, text in enumerate(logs_map[phase])
    ]

    chokepoints = {
        'stable': [
            {'location': '装车区 A (1#铲)', 'waiting_trucks': 2, 'avg_wait_min': 3.4, 'status': 'normal'},
            {'location': '装车区 B (3#铲)', 'waiting_trucks': 3, 'avg_wait_min': 5.2, 'status': 'normal'},
            {'location': '粗破碎站卸料口', 'waiting_trucks': 1, 'avg_wait_min': 1.8, 'status': 'free'},
        ],
        'precursor': [
            {'location': '装车区 A (1#铲)', 'waiting_trucks': 3, 'avg_wait_min': 4.6, 'status': 'normal'},
            {'location': '装车区 B (3#铲)', 'waiting_trucks': 4, 'avg_wait_min': 6.8, 'status': 'normal'},
            {'location': '粗破碎站卸料口', 'waiting_trucks': 1, 'avg_wait_min': 2.0, 'status': 'free'},
        ],
        'warning': [
            {'location': '装车区 A (1#铲)', 'waiting_trucks': 4, 'avg_wait_min': 6.2, 'status': 'normal'},
            {'location': '装车区 B (3#铲)', 'waiting_trucks': 6, 'avg_wait_min': 9.5, 'status': 'congested'},
            {'location': '粗破碎站卸料口', 'waiting_trucks': 2, 'avg_wait_min': 2.6, 'status': 'normal'},
        ],
        'dispatch': [
            {'location': '装车区 A (1#铲)', 'waiting_trucks': 5, 'avg_wait_min': 8.6, 'status': 'congested'},
            {'location': '装车区 B (3#铲)', 'waiting_trucks': 7, 'avg_wait_min': 12.8, 'status': 'congested'},
            {'location': '粗破碎站卸料口', 'waiting_trucks': 2, 'avg_wait_min': 3.1, 'status': 'normal'},
        ],
        'recovery': [
            {'location': '装车区 A (1#铲)', 'waiting_trucks': 3, 'avg_wait_min': 5.1, 'status': 'normal'},
            {'location': '装车区 B (3#铲)', 'waiting_trucks': 4, 'avg_wait_min': 7.0, 'status': 'normal'},
            {'location': '粗破碎站卸料口', 'waiting_trucks': 1, 'avg_wait_min': 2.1, 'status': 'free'},
        ],
    }[phase]

    total_devs = sum(v['total'] for v in asset_map.values())
    online_devs = sum(v['online'] for v in asset_map.values())
    availability = round((online_devs / total_devs * 100), 1)
    performance = {'stable': 88.0, 'precursor': 85.0, 'warning': 79.0, 'dispatch': 73.0, 'recovery': 83.0}[phase]
    quality = 98.4

    return {
        'safety_status': safety,
        'asset_stats': asset_map,
        'production_today': prod_stats,
        'recent_alerts': recent,
        'environment': {'wind_speed': 4.8 if phase != 'dispatch' else 6.1, 'visibility': 3800 if phase != 'dispatch' else 3200, 'pm25': 42 if phase in ['stable', 'precursor'] else 51, 'rainfall': 0.0, 'flight_condition': 'allowed'},
        'operation_logs': operation_logs,
        'cost_metrics': [{'name': '炸药', 'value': 38, 'color': '#00f0ff', 'cost': '0.12'}, {'name': '中保', 'value': 36, 'color': '#3a86ff', 'cost': '0.20'}, {'name': '工资', 'value': 34, 'color': '#ff9900', 'cost': '0.12'}, {'name': '柴油', 'value': 31, 'color': '#ccd6f6', 'cost': '0.12'}],
        'key_equipment': [{'name': '1#PSZ', 'status': '正常', 'status_class': 'text-green', 'current': '22.8A'}, {'name': '2#PSZ', 'status': '检修待命' if phase == 'dispatch' else '正常', 'status_class': 'warning-text' if phase == 'dispatch' else 'text-green', 'current': '-' if phase == 'dispatch' else '21.9A'}, {'name': '3#PSZ', 'status': '正常', 'status_class': 'text-green', 'current': '20.6A'}],
        'material_quality': [{'name': 'CaO', 'value': '52.1', 'trend': '-', 'range': '45.50-53.50', 'status': 'normal'}, {'name': 'MgO', 'value': '0.28', 'trend': '↑' if phase in ['warning', 'dispatch'] else '-', 'range': '0.20-0.50', 'status': 'warning' if phase in ['warning', 'dispatch'] else 'normal'}, {'name': 'SO3', 'value': '0.23', 'trend': '-', 'range': '0.20-0.26', 'status': 'normal'}],
        'logistic_chokepoints': chokepoints,
        'stripping_progress': {'current_m3': round(current * 2.35, 1), 'target_m3': 15000.0, 'ratio': '2.35:1'},
        'equipment_oee': {'availability': availability, 'performance': performance, 'quality': quality, 'oee_score': round(availability * performance * quality / 10000, 1)},
    }


@app.get(
    "/api/v1/ops/production-records",
    response_model=List[ProductionOut],
    tags=["生产运营"],
)
def list_production_records(db: Session = Depends(get_db)):
    """查询生产记录流水 (汇总表)"""
    return (
        db.query(ProductionRecord)
        .order_by(ProductionRecord.timestamp.desc())
        .limit(20)
        .all()
    )


@app.get("/api/v1/ops/production-kpi", response_model=ProductionKPI, tags=["生产运营"])
def get_production_kpi(db: Session = Depends(get_db)):
    """获取生产关键指标 (KPI)"""
    records = (
        db.query(ProductionRecord)
        .order_by(ProductionRecord.timestamp.desc())
        .limit(7)
        .all()
    )

    total_tonnage = sum(r.tonnage for r in records)
    avg_efficiency = sum(r.efficiency for r in records) / len(records) if records else 0
    total_fuel = sum(r.fuel_consumption for r in records)
    current_active = records[0].active_vehicles if records else 0

    return {
        "total_tonnage": round(total_tonnage, 2),
        "avg_efficiency": round(avg_efficiency, 2),
        "total_fuel": round(total_fuel, 2),
        "active_vehicle_count": current_active,
        "daily_trend": records[::-1],
    }


@app.get("/api/v1/ops/energy-optimization", tags=["能源优化"])
def get_energy_optimization(db: Session = Depends(get_db)):
    """获取节能优化面板数据"""
    records = (
        db.query(ProductionRecord)
        .order_by(ProductionRecord.timestamp.desc())
        .limit(7)
        .all()
    )

    total_tonnage = sum(r.tonnage for r in records)
    total_fuel = sum(r.fuel_consumption for r in records)
    avg_efficiency = sum(r.efficiency for r in records) / len(records) if records else 0
    active_vehicle_count = records[0].active_vehicles if records else 0

    kwh_per_ton = round(total_fuel / total_tonnage, 2) if total_tonnage else 2.71
    projected_savings = 12.5 if avg_efficiency < 85 else 8.4
    energy_score = max(62, round(100 - (kwh_per_ton - 2.4) * 20 - max(1, round(active_vehicle_count * 0.2)) * 3))

    zones = [
        {
            "id": "ZONE-01",
            "name": "主运输线",
            "type": "运输优化",
            "priority": "high",
            "priorityText": "重要",
            "saving": "预计节能 8.6%",
            "status": "空转偏高",
            "desc": "通过重排矿卡进出场顺序，降低主运输线待机和空载回程耗能。",
        },
        {
            "id": "ZONE-02",
            "name": "破碎站 CRS-02",
            "type": "负荷平衡",
            "priority": "medium",
            "priorityText": "一般",
            "saving": "预计节能 5.2%",
            "status": "峰值波动",
            "desc": "将高负载破碎任务移入低谷时段，平滑瞬时功率峰值。",
        },
        {
            "id": "ZONE-03",
            "name": "边坡巡检区",
            "type": "设备节电",
            "priority": "low",
            "priorityText": "低",
            "saving": "预计节能 3.4%",
            "status": "可下调频率",
            "desc": "非告警窗口切换节能采样频率，降低边缘计算与传感器待机耗电。",
        },
    ]

    strategies = [
        {
            "id": "ENG-001",
            "title": "主运输线空转压降",
            "zone": "主运输线",
            "type": "运输优化",
            "priority": "high",
            "saving": "8.6%",
            "desc": "调整矿卡侧线装载与排队顺序，缩短主线等待时间，减少怠速损耗。",
            "plan": ["减少主线待机车辆 2 台", "将 AUT-003 / AUT-005 改派至侧线", "10 分钟后复查平均等待时长"],
        },
        {
            "id": "ENG-002",
            "title": "破碎站峰谷错峰",
            "zone": "CRS-02",
            "type": "负荷平衡",
            "priority": "medium",
            "saving": "5.2%",
            "desc": "把高功率破碎任务切换到低谷运行窗口，避免瞬时负载过高。",
            "plan": ["延后高功率破碎任务 15 分钟", "优先清理已缓存矿石", "观察峰值负荷回落情况"],
        },
        {
            "id": "ENG-003",
            "title": "巡检链路低功耗",
            "zone": "边坡巡检区",
            "type": "采集节电",
            "priority": "low",
            "saving": "3.4%",
            "desc": "对稳定区域降低巡检频率，同时保留高风险点位实时上报。",
            "plan": ["巡检间隔从 30 秒调整至 90 秒", "保留高风险传感器实时上报", "告警恢复后自动切回高频模式"],
        },
    ]

    timeline = [
        {"id": 1, "time": "01:04", "action": "识别能耗异常", "target": "主运输线空转率升高"},
        {"id": 2, "time": "01:09", "action": "生成节能建议", "target": "建议切换两台矿卡至侧线"},
        {"id": 3, "time": "01:12", "action": "策略待下发", "target": "等待值班长确认节能策略"},
    ]

    electricity = round(total_tonnage * 1.18 + active_vehicle_count * 9.6, 2) if total_tonnage else 1080.0
    fuel = round(total_fuel, 2)
    peak_load = min(100, round(58 + (active_vehicle_count * 1.9) + (100 - avg_efficiency) * 0.6))
    idle_loss = min(100, round(max(12, active_vehicle_count * 2.4)))

    return {
        "energyMetrics": {
            "shiftEnergy": round(total_fuel * 3.6 or 2860),
            "energyDelta": round(max(1.0, 100 - energy_score) / 2, 1),
            "kwhPerTon": kwh_per_ton,
            "targetKwhPerTon": 2.4,
            "idleVehicles": max(1, round(active_vehicle_count * 0.2)),
            "projectedSavings": projected_savings,
            "energyScore": energy_score,
        },
        "energyBreakdown": {
            "electricity": electricity,
            "fuel": fuel,
            "peakLoad": peak_load,
            "idleLoss": idle_loss,
            "unitCost": round((electricity * 0.82 + fuel * 1.35) / 1000, 2),
        },
        "deviceGroups": [
            {"name": "运输车队", "load": min(100, 45 + active_vehicle_count * 3), "status": "运行中", "saving": "2.8%"},
            {"name": "破碎站", "load": peak_load, "status": "高负荷", "saving": "5.2%"},
            {"name": "巡检链路", "load": max(18, 36 - int(avg_efficiency // 10)), "status": "节能模式", "saving": "3.4%"},
            {"name": "供配电节点", "load": min(100, 52 + int(total_tonnage // 100)), "status": "平稳", "saving": "1.6%"},
        ],
        "rules": [
            {"id": "RULE-01", "when": "运输空载率 > 35%", "then": "下调车队巡航速度并重排装载顺序", "level": "high"},
            {"id": "RULE-02", "when": "破碎站峰值负荷 > 70%", "then": "切换到低谷排程窗口", "level": "medium"},
            {"id": "RULE-03", "when": "智能识别告警升高", "then": "自动提升巡检频率并保留高风险点位实时上报", "level": "critical"},
        ],
        "zones": zones,
        "strategies": strategies,
        "timeline": timeline,
        "trendSeries": [
            {"label": "00:00", "value": max(22, peak_load - 12)},
            {"label": "00:10", "value": max(24, peak_load - 8)},
            {"label": "00:20", "value": max(28, peak_load - 4)},
            {"label": "00:30", "value": peak_load},
            {"label": "00:40", "value": min(100, peak_load + 5)},
            {"label": "00:50", "value": max(30, peak_load - 3)},
        ],
        "summary": {
            "total_tonnage": round(total_tonnage, 2),
            "total_fuel": round(total_fuel, 2),
            "avg_efficiency": round(avg_efficiency, 2),
            "active_vehicle_count": active_vehicle_count,
        },
    }


@app.get("/api/v1/ops/fleet/status", tags=["生产运营"])
def get_fleet_status(db: Session = Depends(get_db)):
    """获取车队实时状态 (位置、电量、作业环节)"""
    # 模拟从实时传感器/GPS系统获取的活跃车队数据
    # 实际项目中这里可能从 Redis 或实时位置库获取
    vehicles = db.query(Device).filter(Device.device_type.in_(["truck", "uav"])).all()

    fleet_data = []
    for v in vehicles:
        fleet_data.append(
            {
                "device_id": v.device_id,
                "device_name": v.device_name,
                "location": {"lng": v.longitude, "lat": v.latitude},
                "status": v.status,
                "current_load": (
                    45.5 if v.device_type == "truck" else 0
                ),  # 重载/空载模拟
                "telemetry": {"fuel_level": 82.5, "speed": 18.5},
            }
        )
    return fleet_data


@app.get("/api/v1/ops/tasks/active", response_model=List[TaskOut], tags=["生产运营"])
def get_active_tasks(db: Session = Depends(get_db)):
    """获取当前所有活跃的运输任务"""
    return db.query(ProductionTask).filter(ProductionTask.status != "completed").all()


@app.post("/api/v1/ops/tasks/dispatch", response_model=TaskOut, tags=["生产运营"])
def dispatch_vehicle(
    data: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(RoleEnum.admin, RoleEnum.engineer)),
):
    """人工/系统下发车辆调度任务"""
    # 简单的任务ID生成逻辑
    task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    new_task = ProductionTask(
        task_id=task_id,
        vehicle_id=data.vehicle_id,
        excavator_id=data.excavator_id,
        load_zone=data.load_zone,
        unload_zone=data.unload_zone,
        material=data.material,
        weight_tons=data.weight_tons,
        status="hauling",
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@app.get("/api/v1/ops/stats/efficiency-leaderboard", tags=["生产运营"])
def get_leaderboard(db: Session = Depends(get_db)):
    """获取车辆作业效率排行榜"""
    # 这里是一个演示逻辑，按累计吨位进行排序
    from sqlalchemy import func

    stats = (
        db.query(
            ProductionTask.vehicle_id,
            func.sum(ProductionTask.weight_tons).label("total_weight"),
        )
        .group_by(ProductionTask.vehicle_id)
        .order_by(func.sum(ProductionTask.weight_tons).desc())
        .all()
    )

    return [
        {
            "vehicle_id": row.vehicle_id,
            "total_tonnage": round(row.total_weight, 2),
            "rank": i + 1,
        }
        for i, row in enumerate(stats)
    ]


# ==============================
#   7. 健康检查
# ==============================


@app.get("/", tags=["系统"])
def health_check():
    return {"status": "ok", "service": "穹盾智矿 - 核心业务管理平台", "version": "2.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)

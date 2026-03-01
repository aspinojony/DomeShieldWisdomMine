"""
穹盾智矿 - ORM 数据模型定义
设备资产、用户权限(RBAC)、告警规则与记录
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base


# ============== 用户与权限 (RBAC) ==============


class RoleEnum(str, enum.Enum):
    admin = "admin"  # 系统管理员
    engineer = "engineer"  # 工程师（可操作设备）
    viewer = "viewer"  # 只读观察员


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100), default="")
    role = Column(Enum(RoleEnum), default=RoleEnum.viewer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


# ============== 设备资产台账 ==============


class DeviceType(str, enum.Enum):
    crack_meter = "crack_meter"  # 裂缝计
    micro_seismic = "micro_seismic"  # 微震仪
    inclinometer = "inclinometer"  # 倾角计
    settlement = "settlement"  # 沉降计
    water_pressure = "water_pressure"  # 孔隙水压计
    gnss = "gnss"  # GNSS 基站
    uav = "uav"  # 无人机


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(
        String(50), unique=True, nullable=False, index=True
    )  # 如 SENSOR-DE-001
    device_name = Column(String(100), default="")
    device_type = Column(Enum(DeviceType), nullable=False)
    longitude = Column(Float, nullable=True)  # 经度
    latitude = Column(Float, nullable=True)  # 纬度
    altitude = Column(Float, nullable=True)  # 海拔(m)
    install_location = Column(String(200), default="")  # 安装位置描述
    status = Column(String(20), default="online")  # online / offline / maintenance
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联的告警规则
    alert_rules = relationship(
        "AlertRule", back_populates="device", cascade="all, delete-orphan"
    )
    alert_records = relationship(
        "AlertRecord", back_populates="device", cascade="all, delete-orphan"
    )


# ============== 告警规则引擎 ==============


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(50), ForeignKey("devices.device_id"), nullable=False)
    metric_field = Column(String(50), nullable=False)  # 监控的字段名，如 crack_width_mm
    operator = Column(String(10), default=">")  # 比较运算符: >, <, >=, <=, ==
    threshold = Column(Float, nullable=False)  # 阈值, 如 10.0
    alert_level = Column(String(20), default="warning")  # info / warning / critical
    description = Column(String(200), default="")
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    device = relationship("Device", back_populates="alert_rules")


class AlertRecord(Base):
    __tablename__ = "alert_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(50), ForeignKey("devices.device_id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=True)
    metric_field = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    alert_level = Column(String(20), default="warning")
    message = Column(Text, default="")
    is_acknowledged = Column(Boolean, default=False)  # 是否已确认/处理
    triggered_at = Column(DateTime, server_default=func.now())

    device = relationship("Device", back_populates="alert_records")

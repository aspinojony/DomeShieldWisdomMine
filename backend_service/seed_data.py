"""
穹盾智矿 - 数据库种子数据初始化
运行: python seed_data.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal, Base
from models import User, Device, AlertRule, AlertRecord, UAVMission
from auth import get_password_hash
from datetime import datetime, timedelta
import random
import json

# 创建所有表
Base.metadata.create_all(bind=engine)

db = SessionLocal()

print("🔧 开始初始化种子数据...\n")

# ============== 1. 用户 ==============
users_data = [
    {
        "username": "admin",
        "password": "admin123",
        "full_name": "系统管理员",
        "role": "admin",
    },
    {
        "username": "engineer01",
        "password": "eng123",
        "full_name": "张工程师",
        "role": "engineer",
    },
    {
        "username": "viewer01",
        "password": "view123",
        "full_name": "李观察员",
        "role": "viewer",
    },
]

for u in users_data:
    existing = db.query(User).filter(User.username == u["username"]).first()
    if not existing:
        user = User(
            username=u["username"],
            hashed_password=get_password_hash(u["password"]),
            full_name=u["full_name"],
            role=u["role"],
        )
        db.add(user)
        print(f"  ✅ 创建用户: {u['username']} ({u['role']})")
    else:
        print(f"  ⏩ 用户已存在: {u['username']}")

db.commit()

# ============== 2. 设备台账 ==============
devices_data = [
    # 微震仪
    {
        "device_id": "SENSOR-MS-001",
        "device_name": "1号微震仪",
        "device_type": "micro_seismic",
        "longitude": 110.4521,
        "latitude": 35.6312,
        "altitude": 850.0,
        "install_location": "北坡采掘区A段",
        "status": "online",
    },
    {
        "device_id": "SENSOR-MS-002",
        "device_name": "2号微震仪",
        "device_type": "micro_seismic",
        "longitude": 110.4535,
        "latitude": 35.6298,
        "altitude": 865.0,
        "install_location": "北坡采掘区B段",
        "status": "online",
    },
    {
        "device_id": "SENSOR-MS-003",
        "device_name": "3号微震仪",
        "device_type": "micro_seismic",
        "longitude": 110.4548,
        "latitude": 35.6280,
        "altitude": 840.0,
        "install_location": "南坡监测区",
        "status": "offline",
    },
    # 裂缝计
    {
        "device_id": "SENSOR-CK-001",
        "device_name": "1号裂缝计",
        "device_type": "crack_meter",
        "longitude": 110.4510,
        "latitude": 35.6320,
        "altitude": 830.0,
        "install_location": "主采区西侧边坡",
        "status": "online",
    },
    {
        "device_id": "SENSOR-CK-002",
        "device_name": "2号裂缝计",
        "device_type": "crack_meter",
        "longitude": 110.4525,
        "latitude": 35.6305,
        "altitude": 845.0,
        "install_location": "排土场北缘",
        "status": "online",
    },
    {
        "device_id": "SENSOR-CK-003",
        "device_name": "3号裂缝计",
        "device_type": "crack_meter",
        "longitude": 110.4540,
        "latitude": 35.6290,
        "altitude": 860.0,
        "install_location": "高危边坡C段",
        "status": "maintenance",
    },
    # 倾角计
    {
        "device_id": "SENSOR-IC-001",
        "device_name": "1号倾角计",
        "device_type": "inclinometer",
        "longitude": 110.4515,
        "latitude": 35.6318,
        "altitude": 835.0,
        "install_location": "主采区东侧",
        "status": "online",
    },
    {
        "device_id": "SENSOR-IC-002",
        "device_name": "2号倾角计",
        "device_type": "inclinometer",
        "longitude": 110.4530,
        "latitude": 35.6302,
        "altitude": 850.0,
        "install_location": "排土场南缘",
        "status": "online",
    },
    # GNSS
    {
        "device_id": "SENSOR-GN-001",
        "device_name": "GNSS基站-A",
        "device_type": "gnss",
        "longitude": 110.4500,
        "latitude": 35.6330,
        "altitude": 820.0,
        "install_location": "矿区中心基准站",
        "status": "online",
    },
    {
        "device_id": "SENSOR-GN-002",
        "device_name": "GNSS基站-B",
        "device_type": "gnss",
        "longitude": 110.4560,
        "latitude": 35.6270,
        "altitude": 870.0,
        "install_location": "矿区南部参考站",
        "status": "online",
    },
    # 沉降计
    {
        "device_id": "SENSOR-ST-001",
        "device_name": "1号沉降计",
        "device_type": "settlement",
        "longitude": 110.4518,
        "latitude": 35.6315,
        "altitude": 838.0,
        "install_location": "排土场中心",
        "status": "online",
    },
    # 孔隙水压计
    {
        "device_id": "SENSOR-WP-001",
        "device_name": "1号水压计",
        "device_type": "water_pressure",
        "longitude": 110.4522,
        "latitude": 35.6308,
        "altitude": 825.0,
        "install_location": "地下水监测井A",
        "status": "online",
    },
    # 无人机
    {
        "device_id": "UAV-DJI-001",
        "device_name": "巡检1号机",
        "device_type": "uav",
        "longitude": 110.4505,
        "latitude": 35.6325,
        "altitude": 815.0,
        "install_location": "无人机停机坪",
        "status": "online",
    },
    {
        "device_id": "UAV-DJI-002",
        "device_name": "巡检2号机",
        "device_type": "uav",
        "longitude": 110.4505,
        "latitude": 35.6325,
        "altitude": 815.0,
        "install_location": "无人机停机坪",
        "status": "online",
    },
]

for d in devices_data:
    existing = db.query(Device).filter(Device.device_id == d["device_id"]).first()
    if not existing:
        device = Device(**d)
        db.add(device)
        print(f"  ✅ 注册设备: {d['device_id']} - {d['device_name']}")
    else:
        print(f"  ⏩ 设备已存在: {d['device_id']}")

db.commit()

# ============== 3. 告警规则 ==============
rules_data = [
    {
        "device_id": "SENSOR-CK-001",
        "metric_field": "crack_width_mm",
        "operator": ">",
        "threshold": 5.0,
        "alert_level": "warning",
        "description": "裂缝宽度超过5mm触发黄色预警",
    },
    {
        "device_id": "SENSOR-CK-001",
        "metric_field": "crack_width_mm",
        "operator": ">",
        "threshold": 10.0,
        "alert_level": "critical",
        "description": "裂缝宽度超过10mm触发红色预警",
    },
    {
        "device_id": "SENSOR-MS-001",
        "metric_field": "magnitude",
        "operator": ">",
        "threshold": 2.5,
        "alert_level": "warning",
        "description": "微震震级超过2.5级触发预警",
    },
    {
        "device_id": "SENSOR-MS-001",
        "metric_field": "magnitude",
        "operator": ">",
        "threshold": 4.0,
        "alert_level": "critical",
        "description": "微震震级超过4.0级紧急预警",
    },
    {
        "device_id": "SENSOR-IC-001",
        "metric_field": "tilt_degree",
        "operator": ">",
        "threshold": 3.0,
        "alert_level": "warning",
        "description": "倾角超过3度触发预警",
    },
    {
        "device_id": "SENSOR-ST-001",
        "metric_field": "settlement_mm",
        "operator": ">",
        "threshold": 15.0,
        "alert_level": "warning",
        "description": "沉降量超过15mm触发预警",
    },
    {
        "device_id": "SENSOR-WP-001",
        "metric_field": "pressure_kpa",
        "operator": ">",
        "threshold": 200.0,
        "alert_level": "critical",
        "description": "孔隙水压超过200kPa紧急预警",
    },
    {
        "device_id": "SENSOR-GN-001",
        "metric_field": "displacement_mm",
        "operator": ">",
        "threshold": 8.0,
        "alert_level": "warning",
        "description": "GNSS水平位移超过8mm预警",
    },
]

existing_rules = db.query(AlertRule).count()
if existing_rules == 0:
    for r in rules_data:
        rule = AlertRule(**r)
        db.add(rule)
        print(f"  ✅ 创建规则: {r['device_id']} - {r['description'][:30]}...")
    db.commit()
else:
    print(f"  ⏩ 已有 {existing_rules} 条告警规则")

# ============== 4. 模拟告警记录 ==============
existing_records = db.query(AlertRecord).count()
if existing_records == 0:
    now = datetime.now()
    records = [
        {
            "device_id": "SENSOR-CK-001",
            "metric_field": "crack_width_mm",
            "metric_value": 6.8,
            "threshold": 5.0,
            "alert_level": "warning",
            "message": "裂缝计1号检测到裂缝宽度6.8mm，超过5mm预警阈值",
            "triggered_at": now - timedelta(hours=2),
        },
        {
            "device_id": "SENSOR-CK-003",
            "metric_field": "crack_width_mm",
            "metric_value": 12.3,
            "threshold": 10.0,
            "alert_level": "critical",
            "message": "高危边坡C段裂缝宽度12.3mm，已达紧急预警阈值！",
            "triggered_at": now - timedelta(hours=1),
        },
        {
            "device_id": "SENSOR-MS-001",
            "metric_field": "magnitude",
            "metric_value": 3.1,
            "threshold": 2.5,
            "alert_level": "warning",
            "message": "北坡采掘区A段检测到3.1级微震事件",
            "triggered_at": now - timedelta(hours=5),
        },
        {
            "device_id": "SENSOR-MS-002",
            "metric_field": "magnitude",
            "metric_value": 4.2,
            "threshold": 4.0,
            "alert_level": "critical",
            "message": "北坡B段检测到4.2级微震事件，建议立即撤离！",
            "triggered_at": now - timedelta(minutes=30),
        },
        {
            "device_id": "SENSOR-IC-001",
            "metric_field": "tilt_degree",
            "metric_value": 3.8,
            "threshold": 3.0,
            "alert_level": "warning",
            "message": "主采区东侧倾角异常3.8度",
            "triggered_at": now - timedelta(hours=8),
        },
        {
            "device_id": "SENSOR-GN-001",
            "metric_field": "displacement_mm",
            "metric_value": 9.68,
            "threshold": 8.0,
            "alert_level": "critical",
            "message": "GNSS基站A检测到水平位移9.68mm，超过阈值",
            "triggered_at": now - timedelta(days=1),
        },
        {
            "device_id": "SENSOR-WP-001",
            "metric_field": "pressure_kpa",
            "metric_value": 215.0,
            "threshold": 200.0,
            "alert_level": "critical",
            "message": "地下水监测井A孔隙水压215kPa",
            "triggered_at": now - timedelta(hours=12),
        },
        {
            "device_id": "SENSOR-ST-001",
            "metric_field": "settlement_mm",
            "metric_value": 18.5,
            "threshold": 15.0,
            "alert_level": "warning",
            "message": "排土场中心沉降量18.5mm",
            "triggered_at": now - timedelta(hours=3),
            "is_acknowledged": True,
        },
    ]
    for r in records:
        record = AlertRecord(**r)
        db.add(record)
        print(f"  ✅ 生成告警: {r['device_id']} - {r['alert_level']}")
    db.commit()
else:
    print(f"  ⏩ 已有 {existing_records} 条告警记录")

# ============== 5. UAV任务 ==============
existing_missions = db.query(UAVMission).count()
if existing_missions == 0:
    missions = [
        {
            "device_id": "UAV-DJI-001",
            "mission_name": "北坡边坡日常巡检",
            "waypoints": json.dumps(
                [
                    {"lng": 110.4521, "lat": 35.6312, "alt": 100},
                    {"lng": 110.4535, "lat": 35.6298, "alt": 120},
                    {"lng": 110.4548, "lat": 35.6280, "alt": 110},
                ]
            ),
            "status": "completed",
        },
        {
            "device_id": "UAV-DJI-002",
            "mission_name": "排土场巡飞监测",
            "waypoints": json.dumps(
                [
                    {"lng": 110.4510, "lat": 35.6320, "alt": 80},
                    {"lng": 110.4525, "lat": 35.6305, "alt": 90},
                ]
            ),
            "status": "pending",
        },
    ]
    for m in missions:
        mission = UAVMission(**m)
        db.add(mission)
        print(f"  ✅ 创建任务: {m['mission_name']}")
    db.commit()
else:
    print(f"  ⏩ 已有 {existing_missions} 条UAV任务")

db.close()
print("\n🎉 种子数据初始化完成！")
print("用户账号: admin/admin123, engineer01/eng123, viewer01/view123")

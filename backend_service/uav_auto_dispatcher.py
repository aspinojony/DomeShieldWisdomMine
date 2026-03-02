import asyncio
import json
import logging
import random
import time
from sqlalchemy import create_engine
from database import SessionLocal
from models import UAVMission, Device, AlertRecord, DeviceType

# 独立运行的自动派单巡检机器人 (模拟 DJI Cloud API 闭环)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - UAVDispatcher - %(levelname)s - %(message)s",
)

DATABASE_URL = "sqlite:///./mining_db.sqlite3"


def check_and_dispatch():
    db = SessionLocal()
    try:
        # 1. 查找未处理的最高级别预警 (此处查找 critical)
        unacked_critical_alerts = (
            db.query(AlertRecord)
            .filter(
                AlertRecord.alert_level == "critical",
                AlertRecord.is_acknowledged == False,
            )
            .all()
        )

        if not unacked_critical_alerts:
            # logging.info("目前无三级紧急预警，无人机编队待命中...")
            return

        # 2. 查找全矿目前处于挂载状态且空闲的无人机
        idle_uavs = (
            db.query(Device)
            .filter(Device.device_type == DeviceType.uav, Device.status == "online")
            .all()
        )

        if not idle_uavs:
            logging.warning("出现高危警报！但当前无空闲的 UAV 机组可供调遣！")
            return

        for alert in unacked_critical_alerts:
            # 判断是否已经为这个告警设备地址派发过任务，防止重复派发
            recent_mission = (
                db.query(UAVMission)
                .filter(
                    UAVMission.mission_name.like(f"Auto-Inspect: {alert.device_id}%"),
                    UAVMission.status.in_(["pending", "executing"]),
                )
                .first()
            )

            if recent_mission:
                continue

            # 3. 生成空地协同任务，随机派出一架无人机
            uav = random.choice(idle_uavs)

            # 使用简单的虚拟偏移算法，为待飞设备中心生成四个抵近巡查航点
            # 真实项目中需要接入 大疆司空2 (DJI FlightHub 2) API 或 MSDK
            mock_waypoints = [
                {
                    "lat": 39.635 + random.uniform(-0.005, 0.005),
                    "lng": 109.840 + random.uniform(-0.005, 0.005),
                    "alt": 150,
                },
                {
                    "lat": 39.636 + random.uniform(-0.005, 0.005),
                    "lng": 109.841 + random.uniform(-0.005, 0.005),
                    "alt": 120,
                },
            ]

            new_mission = UAVMission(
                device_id=uav.device_id,
                mission_name=f"Auto-Inspect: {alert.device_id} 区块异常",
                waypoints=json.dumps(mock_waypoints),
                status="pending",
            )
            db.add(new_mission)
            db.commit()

            logging.info(
                f"🚨 [闭环响应] 监测到 {alert.device_id} ({alert.metric_field}: {alert.metric_value}) 高危预警！"
            )
            logging.info(
                f"🚁 已自动为您生成无人机查证工单，指派机组: {uav.device_id}。航线端点已下发至 MSDK / 云台。"
            )

    except Exception as e:
        logging.error(f"UAV Dispatcher Error: {e}")
    finally:
        db.close()


async def main():
    logging.info("=================================")
    logging.info(" 🛰️ 无人机空地协同调度中枢启动")
    logging.info("=================================")
    while True:
        check_and_dispatch()
        await asyncio.sleep(10)  # 每 10 秒扫描一次红框告警


if __name__ == "__main__":
    asyncio.run(main())

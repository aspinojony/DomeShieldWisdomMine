import asyncio
import json
import logging
import random
import time
from sqlalchemy.orm import Session
from database import SessionLocal
from models import UAVMission, Device, AlertRecord, DeviceType

# 工业级空地协同管控引擎核心逻辑 (UAV Swarm Orchestrator)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [UAV-Orchestrator] - %(levelname)s - %(message)s",
)


class UAVDispatcherEngine:
    """
    负责管理无人机工单生命周期：
    1. 警报捕获 -> 2. 可用设备寻呼 -> 3. 避障航线生成 -> 4. 任务下发 -> 5. 状态机流转监测 -> 6. 任务闭环确认
    """

    def __init__(self):
        self.active_tasks = {}  # 用于保存当前正在执飞中的协程任务锁

    def fetch_critical_alerts(self, db: Session):
        return (
            db.query(AlertRecord)
            .filter(
                AlertRecord.alert_level == "critical",
                AlertRecord.is_acknowledged == False,
            )
            .all()
        )

    def find_available_drone(self, db: Session):
        # 查询状态为 "online" 的空闲无人机
        drones = (
            db.query(Device)
            .filter(Device.device_type == DeviceType.uav, Device.status == "online")
            .all()
        )
        return random.choice(drones) if drones else None

    def generate_safe_waypoints(self, target_lat, target_lng):
        """
        三维避障航线生成模拟 (真实场景接入 DEM/DSM 标高数据与 A* / RRT 算法)
        """
        # 以报警点为圆心，生成 4 个环绕查证航点
        radius = 0.002  # 大约 200 米半径
        base_alt = 120  # 安全起降限高 120m

        return [
            {"lat": target_lat + radius, "lng": target_lng, "alt": base_alt},
            {"lat": target_lat, "lng": target_lng + radius, "alt": base_alt - 10},
            {"lat": target_lat - radius, "lng": target_lng, "alt": base_alt},
            {"lat": target_lat, "lng": target_lng - radius, "alt": base_alt + 20},
        ]

    async def execute_flight_mission(
        self, mission_id: int, target_alert_id: int = None
    ):
        """
        后台监视无人机从起飞、巡检到返航归巢 (模拟 MSDK 或互联回调机制)
        """
        db = SessionLocal()
        try:
            mission = db.query(UAVMission).filter(UAVMission.id == mission_id).first()
            if not mission:
                return

            uav = db.query(Device).filter(Device.device_id == mission.device_id).first()
            if uav:
                uav.status = "executing"  # 锁定占用无人机
                db.commit()

            logging.info(
                f"🚁 [{uav.device_id}] 引擎点火！已开始执行工单 (#{mission_id}) -> {mission.mission_name}"
            )

            # 模拟飞完了各个航点并拍照取证 (延时代表了真实的飞行周期)
            waypoints = json.loads(mission.waypoints)
            for idx, wp in enumerate(waypoints):
                await asyncio.sleep(8)  # 模拟飞向该锚点所需时间...
                logging.info(
                    f"📷 [{uav.device_id}] 已抵达 {idx+1}/{len(waypoints)} 号查证锚点 (Lat: {wp['lat']:.4f}), 执行拍摄与建模..."
                )

            # 返航降落
            await asyncio.sleep(5)

            # 任务闭环更新状态
            mission.status = "completed"
            if uav:
                uav.status = "online"  # 释放无人机，可接受下一次调度

            # 空地协同最终闭环：系统消警
            if target_alert_id:
                alert = (
                    db.query(AlertRecord)
                    .filter(AlertRecord.id == target_alert_id)
                    .first()
                )
                if alert:
                    alert.is_acknowledged = True
                    alert.message = f"✅ 已通过空地协同核实消除。执飞架次: {uav.device_id}, 任务单号: #{mission_id}"
                    logging.info(
                        f"✔️ 警报 #{target_alert_id} 自动消警完成，并留下不可篡改的飞行确认痕迹。"
                    )

            db.commit()
            logging.info(
                f"✅ [{uav.device_id}] 任务 (#{mission_id}) 执行完毕，无人机已安全返航入巢，状态解除锁定！"
            )

        except Exception as e:
            logging.error(f"Flight Mission Error on MT-Task {mission_id}: {e}")
        finally:
            db.close()
            # 释放活跃任务锁
            self.active_tasks.pop(mission_id, None)

    def trigger_dispatch_flow(self):
        db = SessionLocal()
        try:
            alerts = self.fetch_critical_alerts(db)
            if not alerts:
                return

            for alert in alerts:
                # 去重：如果这个隐患区域已经在派过或者刚刚派过无人机去看了，就跳过
                recent_mission = (
                    db.query(UAVMission)
                    .filter(
                        UAVMission.mission_name.like(f"%{alert.device_id}%"),
                        UAVMission.status.in_(["pending", "executing"]),
                    )
                    .first()
                )

                if recent_mission:
                    continue

                uav = self.find_available_drone(db)
                if not uav:
                    logging.warning(
                        "⚠️ 高危警报待处理队列拥堵，目前已无可用/满电的无人机编队！"
                    )
                    break

                # 获取报警设备位置 (Mock 位置系)
                target_lat, target_lng = 39.635, 109.840
                mock_waypoints = self.generate_safe_waypoints(target_lat, target_lng)

                # 创建调度工单
                new_mission = UAVMission(
                    device_id=uav.device_id,
                    mission_name=f"自动紧急查证: {alert.device_id} 区块异常",
                    waypoints=json.dumps(mock_waypoints),
                    status="executing",
                )
                db.add(new_mission)
                db.commit()
                db.refresh(new_mission)

                logging.critical(
                    f"🚨 [警报拦截成功] 捕获 {alert.device_id} ({alert.metric_field}: {alert.metric_value}) 高危熔断！"
                )
                logging.warning(
                    f"🗺️ 智能航线规划成功，共 {len(mock_waypoints)} 个锚点，已下发指控命令。"
                )

                # 扔到异步循环里非阻塞执行监视
                task = asyncio.create_task(
                    self.execute_flight_mission(new_mission.id, alert.id)
                )
                self.active_tasks[new_mission.id] = task

        except Exception as e:
            logging.error(f"调度引擎捕获到异常: {e}")
        finally:
            db.close()


async def main():
    engine = UAVDispatcherEngine()
    logging.info("⚡ IOT-UAV 神经中枢网络启动 (常驻巡查)")

    while True:
        engine.trigger_dispatch_flow()
        await asyncio.sleep(5)  # 5秒一次的心跳扫描


if __name__ == "__main__":
    asyncio.run(main())

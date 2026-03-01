import json
import time
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# --- 配置参数 ---
# 1. EMQX (MQTT Broker) 配置
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
TOPIC_SUBSCRIBE = "mining/device/sensor/#"

# 2. InfluxDB (时序数据库) 配置
INFLUX_URL = "http://127.0.0.1:8086"
INFLUX_TOKEN = "my-super-secret-auth-token"  # 与 docker-compose.yml 保持一致
INFLUX_ORG = "mining"
INFLUX_BUCKET = "sensor_data"

# 全局的 InfluxDB 客户端连接
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# 阈值配置（用于第一阶段触发报警打印）
THRESHOLDS = {
    "crack_meter": 10.0,  # 裂缝 > 10mm
    "micro_seismic": 100.0,  # 微震能量 > 100
    "inclinometer": 2.0,  # 倾角 > 2 度
    "settlement": 10.0,  # 沉降 > 10mm
    "water_pressure": 200.0,  # 水压 > 200kpa
}


def check_and_alert(data):
    """边缘验证与轻量预警检查逻辑"""
    dev_type = data.get("device_type")
    dev_id = data.get("device_id")

    if dev_type == "crack_meter":
        val = data.get("crack_width_mm")
        if val > THRESHOLDS["crack_meter"]:
            print(f"🚨 [一级警报] {dev_id} 裂缝宽度达到 {val} mm! 超越红线！")

    elif dev_type == "micro_seismic":
        val = data.get("energy_level")
        if val > THRESHOLDS["micro_seismic"]:
            print(f"🚨 [爆震警报] {dev_id} 检测到异常高能微震：{val}，警惕断层破裂！")

    elif dev_type == "inclinometer":
        val = data.get("angle_x")
        if val > THRESHOLDS["inclinometer"]:
            print(f"🚨 [滑坡风险] {dev_id} X轴倾角倾斜加速：{val}°!")

    # 后续复杂的逻辑（多源数据关联、AI模型对接）将在 Sprint 3 补入


def process_and_save(msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        device_id = data.get("device_id", "unknown")
        device_type = data.get("device_type", "unknown")

        # 1. 数据安全性告警校验
        check_and_alert(data)

        # 2. 将数据组装为 InfluxDB 的 'Point' (打标签和值)
        point = Point(device_type).tag("device_id", device_id)

        # 筛选所有的浮点数或整数，视为存储的值 (Field)
        for key, value in data.items():
            if isinstance(value, (int, float)) and key != "timestamp":
                point = point.field(key, float(value))

        # 设置时间戳（如果不设置，InfluxDB 自动取入库的时间戳）
        if "timestamp" in data:
            # Python time() 是秒，乘以 10^9 变成纳秒
            point = point.time(int(data["timestamp"] * 1000000), WritePrecision.NS)

        # 3. 写入数据库
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        # print(f"✅ 入库成功 -> {device_type} : {device_id}")

    except Exception as e:
        print(f"⚠️ 解析/入库失败: {e}")


# --- MQTT 回调函数 ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"🔌 后端接收网关已成功连接到 EMQX ")
        client.subscribe(TOPIC_SUBSCRIBE)
        print(f"🎧 开始监听主题: {TOPIC_SUBSCRIBE}")
    else:
        print(f"❌ 连接 EMQX 失败，错误码 {rc}")


def on_message(client, userdata, msg):
    # 当接收到设备报文，立刻放入处理流水线
    process_and_save(msg)


def start_backend_service():
    print("🚀 启动[穹盾智矿]后端数据入库服务...")
    client = mqtt.Client("Backend_Data_Ingestion_Node")
    client.on_connect = on_connect
    client.on_message = on_message

    # 不断重试连接直到 EMQX 启动（Docker可能还需要几秒）
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except ConnectionRefusedError:
            print("⏳ 等待 EMQX 服务启动，3秒后重连...")
            time.sleep(3)

    client.loop_forever()


if __name__ == "__main__":
    start_backend_service()

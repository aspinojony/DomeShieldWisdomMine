import time
import json
import random
import datetime
import paho.mqtt.client as mqtt

# --- 配置参数 ---
MQTT_BROKER = "127.0.0.1"  # EMQX 服务地址，如果是Docker跑在本地，直接用127.0.0.1
MQTT_PORT = 1883
TOPIC_PREFIX = "mining/device/sensor/"  # 发送消息的 MQTT 主题前缀
PUBLISH_INTERVAL = 2  # 每 2 秒发送一次数据

# 模拟的 10 个传感器设备 ID，涵盖地表沉降计、微震仪、倾角计等
SENSORS = [
    {"id": "SENSOR-DE-001", "type": "crack_meter", "desc": "边坡裂缝计"},
    {"id": "SENSOR-DE-002", "type": "crack_meter", "desc": "边坡裂缝计"},
    {"id": "SENSOR-MV-101", "type": "micro_seismic", "desc": "深部微震仪"},
    {"id": "SENSOR-MV-102", "type": "micro_seismic", "desc": "深部微震仪"},
    {"id": "SENSOR-IN-201", "type": "inclinometer", "desc": "岩体倾角计"},
    {"id": "SENSOR-IN-202", "type": "inclinometer", "desc": "岩体倾角计"},
    {"id": "SENSOR-SE-301", "type": "settlement", "desc": "地表沉降计"},
    {"id": "SENSOR-SE-302", "type": "settlement", "desc": "地表沉降计"},
    {"id": "SENSOR-WP-401", "type": "water_pressure", "desc": "孔隙水压计"},
    {"id": "SENSOR-WP-402", "type": "water_pressure", "desc": "孔隙水压计"},
]


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ 成功连接到 MQTT (EMQX) 服务器！")
    else:
        print(f"❌ 连接失败，返回码: {rc}")


def generate_mock_data(sensor):
    """根据传感器类型，生成带有轻微随机波动、偶尔爆发的模拟数据"""
    base_data = {
        "device_id": sensor["id"],
        "device_type": sensor["type"],
        "timestamp": int(datetime.datetime.now().timestamp() * 1000),
    }

    # 为了模拟异常数据突发（例如边坡滑坡预兆或微震），增加 5% 产生超限大数据的概率
    is_anomaly = random.random() < 0.05

    if sensor["type"] == "crack_meter":
        # 单位：mm
        # 正常缓慢变形在 1.0~2.5mm，异常突变为 10.0~30.0mm
        value = (
            random.uniform(1.0, 2.5) if not is_anomaly else random.uniform(10.0, 30.0)
        )
        base_data["crack_width_mm"] = round(value, 3)

    elif sensor["type"] == "micro_seismic":
        # 微震能量。普通波动极小，如果有大石头断裂，能量突然极速飙升
        value = (
            random.uniform(0.1, 5.0) if not is_anomaly else random.uniform(100.0, 500.0)
        )
        base_data["energy_level"] = round(value, 2)
        base_data["frequency_hz"] = round(random.uniform(10, 50), 1)

    elif sensor["type"] == "inclinometer":
        # 倾角，单位°
        value = (
            random.uniform(0.01, 0.5) if not is_anomaly else random.uniform(2.0, 8.0)
        )
        base_data["angle_x"] = round(value, 4)
        base_data["angle_y"] = round(random.uniform(0.01, 0.5), 4)

    elif sensor["type"] == "settlement":
        # 沉降量：mm
        value = (
            random.uniform(0.5, 3.0) if not is_anomaly else random.uniform(15.0, 50.0)
        )
        base_data["settlement_mm"] = round(value, 2)

    elif sensor["type"] == "water_pressure":
        # 渗透水压，单位：KPa
        value = (
            random.uniform(100.0, 120.0)
            if not is_anomaly
            else random.uniform(200.0, 400.0)
        )
        base_data["pressure_kpa"] = round(value, 2)

    return base_data


def run_mock_devices():
    client = mqtt.Client(f"Mock_Device_Runner_{random.randint(1000, 9999)}")
    client.on_connect = on_connect

    try:
        # 注意：如果在等待 EMQX 启动，可能会连接失败，最好做重试机制
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()  # 在后台开启接收循环

        print(f"🚀 开始模拟 {len(SENSORS)} 台矿山传感器并向 MQTT 推送实时数据...")

        while True:
            for s in SENSORS:
                payload = generate_mock_data(s)
                topic = f"{TOPIC_PREFIX}{s['type']}/{s['id']}"

                # 发布消息到对应的主题
                client.publish(topic, json.dumps(payload), qos=1)

                # 提示在控制台打印
                print(f"[发往 {topic}] => {payload}")

            print(f"--- 睡眠 {PUBLISH_INTERVAL} 秒后进行下一轮发送 ---")
            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print("\n⛔ 停止模拟数据发送。")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"❌ 发生错误要求: {e}，请检查 MQTT 服务 (EMQX) 是否已经完全启动")


if __name__ == "__main__":
    run_mock_devices()

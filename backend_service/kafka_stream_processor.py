import json
import time
from kafka import KafkaConsumer
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# --- Kafka 配置 ---
KAFKA_BROKER = "127.0.0.1:9092"
KAFKA_TOPIC = "mining_sensor_stream"
CONSUMER_GROUP = "backend_anomaly_detectors"

# --- InfluxDB 配置 ---
INFLUX_URL = "http://127.0.0.1:8086"
INFLUX_TOKEN = "my-super-secret-auth-token"
INFLUX_ORG = "mining"
INFLUX_BUCKET = "sensor_data"
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

THRESHOLDS = {
    "crack_meter": 10.0,
    "micro_seismic": 100.0,
    "inclinometer": 2.0,
    "settlement": 10.0,
    "water_pressure": 200.0,
}


def analyze_and_sink(record):
    """
    Kafka 消费者处理单元
    流计算中心：在这里能进行滑窗运算、接驳上面的 AI 推理等。
    """
    data = record.value
    device_id = data.get("device_id", "unknown")
    device_type = data.get("device_type", "unknown")

    # 1. 简单的异常检测 (模拟工业 Flink 中的复杂滑动窗口规则)
    if (
        device_type == "crack_meter"
        and data.get("crack_width_mm", 0) > THRESHOLDS["crack_meter"]
    ):
        print(
            f"🔥 [流计算引擎拦截] {device_id} 裂缝超限: {data.get('crack_width_mm')} mm!"
        )

    # 2. 从 Kafka 取出数据下沉到 InfluxDB
    try:
        point = Point(device_type).tag("device_id", device_id)

        # 提取字段写入
        for key, value in data.items():
            if isinstance(value, (int, float)) and key != "timestamp":
                point = point.field(key, float(value))

        if "timestamp" in data:
            point = point.time(int(data["timestamp"] * 1000000), WritePrecision.NS)

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        # print(f"🌊 [入库] 成功序列化 {device_id} 的波形至 InfluxDB。")

    except Exception as e:
        print(f"⚠️ 入库致命错误: {e}")


def start_stream_processing():
    print("===================================================")
    print(" 🌊 穹盾智矿 - 工业级流计算吞吐中心 (Kafka Consumer)")
    print("===================================================")

    # 初始化 Kafka 消费集群 (支持随意伸缩节点)
    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset="latest",  # 启动时只接收最新数据
                enable_auto_commit=True,  # 自动提交 Offset 分布式游标
                group_id=CONSUMER_GROUP,  # 消费组模式
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            )
        except Exception as e:
            print(f"⏳ 等待连接 Kafka 集群... {e}")
            time.sleep(3)

    print("✅ 消费者已挂载至 Kafka 拓扑网络，正在监听高频信道...")

    # 永久监听与拉取
    for message in consumer:
        analyze_and_sink(message)


if __name__ == "__main__":
    start_stream_processing()

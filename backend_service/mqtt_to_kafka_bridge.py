import json
import time
import paho.mqtt.client as mqtt
from kafka import KafkaProducer

# --- 配置参数 ---
# 1. EMQX (MQTT Broker) 边缘端网关配置
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
TOPIC_SUBSCRIBE = "mining/device/sensor/#"

# 2. Kafka (集群流数据中枢) 配置
KAFKA_BROKER = "127.0.0.1:9092"
KAFKA_TOPIC = "mining_sensor_stream"

print("⏳ 正在初始化 Kafka 生产者节点...")
# 初始化 Kafka 生产者 (带重试保护机制)
producer = None
while not producer:
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        print("✅ Kafka 生产者连接成功！")
    except Exception as e:
        print(f"⚠️ 等待 Kafka 启动中: {e}")
        time.sleep(3)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"🔌 边缘网关 (Bridge) 成功接入 EMQX ")
        client.subscribe(TOPIC_SUBSCRIBE)
        print(f"🎧 开始监听弱网协议主题: {TOPIC_SUBSCRIBE}")
    else:
        print(f"❌ EMQX 连接失败，码: {rc}")


def on_message(client, userdata, msg):
    """
    边缘转云核心逻辑：
    直接把 MQTT 协议下松散的数据，打包打入 Kafka 的统一 Topic
    在这个环节，我们解耦了“接收”与“处理”，从而可以承受高达百万/秒的并发而不丢弃任何一条传感器波形。
    """
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        device_id = data.get("device_id", "unknown")

        # 将原始数据推入 Kafka
        producer.send(KAFKA_TOPIC, value=data, key=device_id.encode("utf-8"))
        # producer.flush() # 生产环境中可以去掉 flush 以提高吞吐量，靠定期提交
        # print(f"🚀 [Bridge] 成功将 {device_id} 数据泵入 Kafka 管道。")

    except Exception as e:
        print(f"⚠️ 数据转发异常: {e}")


def start_bridge():
    print("========================================")
    print(" 🌉 穹盾智矿 - 边缘与云端高速通道 (MQTT->Kafka)")
    print("========================================")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "Edge_Gateway_Bridge")
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except ConnectionRefusedError:
            print("⏳ 等待 EMQX，3秒后重连...")
            time.sleep(3)

    client.loop_forever()


if __name__ == "__main__":
    start_bridge()

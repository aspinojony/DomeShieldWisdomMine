import paho.mqtt.client as mqtt
import time
import json
import random
import threading

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
TOPIC_PREFIX = "mine/sensors"
TOTAL_SENSORS = 10000
THREADS = 20
MESSAGES_PER_THREAD = TOTAL_SENSORS // THREADS


def worker(thread_id, start_idx, num_messages):
    client = mqtt.Client(f"LoadTester-{thread_id}")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        start_time = time.time()
        for i in range(num_messages):
            sensor_id = f"SENSOR-STRESS-{(start_idx + i):05d}"

            # 随机生成一种传感器数据
            device_type = random.choice(
                [
                    "crack_meter",
                    "micro_seismic",
                    "inclinometer",
                    "settlement",
                    "water_pressure",
                ]
            )

            payload = {
                "device_id": sensor_id,
                "device_type": device_type,
                "timestamp": int(time.time() * 1000),
            }

            # 添加各类专属数据
            if device_type == "crack_meter":
                payload["crack_width_mm"] = random.uniform(0.1, 15.0)
            elif device_type == "micro_seismic":
                payload["energy_level"] = random.uniform(10, 200)
                payload["frequency_hz"] = random.uniform(1, 50)
            elif device_type == "inclinometer":
                payload["angle_x"] = random.uniform(0, 5)
            elif device_type == "settlement":
                payload["settlement_mm"] = random.uniform(0, 15)
            elif device_type == "water_pressure":
                payload["pressure_kpa"] = random.uniform(50, 250)

            client.publish(f"{TOPIC_PREFIX}/{sensor_id}", json.dumps(payload), qos=0)

            if i > 0 and i % 500 == 0:
                print(f"[{thread_id}] 已发送 {i} 条压测载荷")
                time.sleep(0.01)  # 短暂限流防止 socket 爆掉

        client.loop_stop()
        client.disconnect()
        elapsed = time.time() - start_time
        print(
            f"[{thread_id}] 完成 {num_messages} 条发送. 耗时: {elapsed:.2f}秒 (TPS: {num_messages/elapsed:.0f})"
        )

    except Exception as e:
        print(f"Thread {thread_id} error: {e}")


if __name__ == "__main__":
    print(f"🚀 初始化穹盾智矿大数据压测引擎")
    print(f"   目标集群: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"   模拟传感器吞吐量: {TOTAL_SENSORS} 节点接入")
    print("--------------------------------------------------")

    start_time = time.time()
    threads = []

    for t in range(THREADS):
        start_idx = t * MESSAGES_PER_THREAD
        thread = threading.Thread(
            target=worker, args=(t, start_idx, MESSAGES_PER_THREAD)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    total_time = time.time() - start_time
    print("--------------------------------------------------")
    print(f"✅ 高并发压测攻击完成: {TOTAL_SENSORS} Payload.")
    print(f"⏱️ 全局耗时: {total_time:.2f} 秒")
    print(
        f"⚡ 集群处理均速 TPS (Transactions Per Second): {TOTAL_SENSORS / total_time:.2f} 笔/秒"
    )

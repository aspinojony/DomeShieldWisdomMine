from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import datetime
from influxdb_client import InfluxDBClient

# --- 配置参数 ---
INFLUX_URL = "http://127.0.0.1:8086"
INFLUX_TOKEN = "my-super-secret-auth-token"
INFLUX_ORG = "mining"
INFLUX_BUCKET = "sensor_data"

# 初始化 InfluxDB 客户端和查询 API
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

# 初始化 FastAPI 框架
app = FastAPI(title="穹盾智矿 - 核心监控系统 API", version="1.0")

# 解决跨域问题，允许任何前端域名访问接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 接口定义 ---


@app.get("/")
def read_root():
    return {"status": "ok", "message": "API 服务运行正常！"}


@app.get("/api/v1/sensors/latest")
def get_latest_sensor_data(device_type: Optional[str] = None):
    """
    获取各种传感器设备的最新上报数据 (从 InfluxDB 中抽血最近 10 分钟的数据末梢)
    如果传入 device_type 比如 crack_meter，则只查询裂缝计数据
    """

    # 构建 Flux 查询语句：去 sensor_data 桶中取最近 10 分钟数据，按 device_id 分组，并取最后一条（latest）
    base_query = f"""
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -10m)
    """

    if device_type:
        base_query += f'|> filter(fn: (r) => r._measurement == "{device_type}")'

    base_query += """
        |> filter(fn: (r) => r._field != "")
        |> last()
    """

    try:
        tables = query_api.query(base_query, org=INFLUX_ORG)

        results = []
        for table in tables:
            for record in table.records:
                results.append(
                    {
                        "device_type": record.get_measurement(),
                        "device_id": record.values.get("device_id"),
                        "field": record.get_field(),
                        "value": record.get_value(),
                        "time": record.get_time().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

        # 因为 InfluxDB 查询出的数据结构是平铺长条的，我们将其针对 device_id 进行一下对象合并，便于前端拿数据
        grouped_results = {}
        for r in results:
            d_id = r["device_id"]
            if d_id not in grouped_results:
                grouped_results[d_id] = {
                    "device_id": d_id,
                    "device_type": r["device_type"],
                    "last_update": r["time"],
                }
            # 将具体的值附加到这个设备对象身上 (例如: crack_width_mm: 2.1)
            grouped_results[d_id][r["field"]] = r["value"]

        return {"status": "success", "data": list(grouped_results.values())}

    except Exception as e:
        return {"status": "error", "message": f"查询 InfluxDB 失败: {str(e)}"}


@app.get("/api/v1/sensors/history/{device_id}")
def get_sensor_history(device_id: str, minutes: int = 60):
    """
    获取指定设备的历史曲线数据
    默认为获取近 60 分钟的时序数据
    """
    query = f"""
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -{minutes}m)
        |> filter(fn: (r) => r.device_id == "{device_id}")
    """

    try:
        tables = query_api.query(query, org=INFLUX_ORG)
        history = []

        for table in tables:
            for record in table.records:
                history.append(
                    {
                        "field": record.get_field(),
                        "value": record.get_value(),
                        "time": record.get_time().strftime("%H:%M:%S"),
                    }
                )

        # 按时间排序展示曲线
        return {"status": "success", "device_id": device_id, "data": history}

    except Exception as e:
        return {"status": "error", "message": f"查询历史数据失败: {str(e)}"}


if __name__ == "__main__":
    import uvicorn

    # 以 8000 端口启动 API 后端服务
    uvicorn.run(app, host="0.0.0.0", port=8000)

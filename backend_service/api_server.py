from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from influxdb_client import InfluxDBClient
from settings import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET, DEMO_MODE, CORS_ALLOW_ORIGINS
from datetime import datetime, timedelta
import math

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

app = FastAPI(title='穹盾智矿 - 核心监控系统 API', version='1.2')
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def get_demo_scene(now: datetime | None = None):
    now = now or datetime.now()
    cycle = 360
    sec = int(now.timestamp()) % cycle
    if sec < 150:
        phase = 'stable'
        progress = sec / 150
    elif sec < 220:
        phase = 'precursor'
        progress = (sec - 150) / 70
    elif sec < 280:
        phase = 'warning'
        progress = (sec - 220) / 60
    elif sec < 330:
        phase = 'dispatch'
        progress = (sec - 280) / 50
    else:
        phase = 'recovery'
        progress = (sec - 330) / 30
    return phase, max(0.0, min(1.0, progress)), sec


def build_sensor_snapshot(now: datetime | None = None):
    now = now or datetime.now()
    phase, progress, sec = get_demo_scene(now)
    jitter = math.sin(sec / 9) * 0.03

    crack = 2.1 + math.sin(sec / 17) * 0.12
    seismic = 16.0 + math.sin(sec / 13) * 1.4
    angle = 0.12 + math.sin(sec / 16) * 0.01
    settlement = 1.5 + math.sin(sec / 18) * 0.08

    if phase == 'precursor':
        crack += 0.4 + progress * 1.2
        seismic += 3 + progress * 8
        angle += 0.03 + progress * 0.05
        settlement += 0.3 + progress * 0.9
    elif phase == 'warning':
        crack += 1.8 + progress * 1.6
        seismic += 12 + progress * 15
        angle += 0.09 + progress * 0.08
        settlement += 1.1 + progress * 1.5
    elif phase == 'dispatch':
        crack += 3.2 - progress * 0.3
        seismic += 24 - progress * 3
        angle += 0.16 - progress * 0.02
        settlement += 2.3 - progress * 0.4
    elif phase == 'recovery':
        crack += 1.6 - progress * 1.0
        seismic += 9 - progress * 6
        angle += 0.07 - progress * 0.04
        settlement += 0.8 - progress * 0.5

    return {
        'phase': phase,
        'progress': round(progress, 3),
        'crack': round(crack + jitter, 2),
        'seismic': round(seismic + jitter * 8, 1),
        'angle': round(angle + jitter / 2, 3),
        'settlement': round(settlement + jitter, 2),
        'time': now.strftime('%Y-%m-%d %H:%M:%S'),
    }


def build_demo_latest(device_type: Optional[str] = None):
    snap = build_sensor_snapshot()
    samples = [
        {'device_id': 'CM-001', 'device_type': 'crack_meter', 'crack_width_mm': snap['crack'], 'last_update': snap['time']},
        {'device_id': 'MS-001', 'device_type': 'micro_seismic', 'energy_level': snap['seismic'], 'last_update': snap['time']},
        {'device_id': 'IN-001', 'device_type': 'inclinometer', 'angle_x': snap['angle'], 'last_update': snap['time']},
        {'device_id': 'ST-001', 'device_type': 'settlement', 'settlement_mm': snap['settlement'], 'last_update': snap['time']},
    ]
    if device_type:
        samples = [s for s in samples if s['device_type'] == device_type]
    return {'status': 'success', 'message': f'场景演示数据 · {snap["phase"]}', 'demo_mode': True, 'scene_phase': snap['phase'], 'data': samples}


def build_demo_history(device_id: str, minutes: int = 60):
    now = datetime.now()
    data = []
    field_map = {
        'CM-001': 'crack_width_mm',
        'MS-001': 'energy_level',
        'IN-001': 'angle_x',
        'ST-001': 'settlement_mm',
    }
    field = field_map.get(device_id, 'value')
    for i in range(24):
        ts = now - timedelta(minutes=(23 - i) * max(1, minutes // 24))
        snap = build_sensor_snapshot(ts)
        value = {
            'crack_width_mm': snap['crack'],
            'energy_level': snap['seismic'],
            'angle_x': snap['angle'],
            'settlement_mm': snap['settlement'],
            'value': snap['crack'],
        }[field]
        data.append({'field': field, 'value': value, 'time': ts.strftime('%H:%M:%S')})
    return {'status': 'success', 'device_id': device_id, 'demo_mode': True, 'data': data}


@app.get('/')
def read_root():
    return {'status': 'ok', 'message': 'API 服务运行正常！', 'demo_mode': DEMO_MODE}


@app.get('/health')
def health():
    return {'status': 'ok', 'demo_mode': DEMO_MODE}


@app.get('/sensors/latest')
def get_latest_sensor_data_alias(device_type: Optional[str] = None):
    return get_latest_sensor_data(device_type)


@app.get('/api/v1/sensors/latest')
def get_latest_sensor_data(device_type: Optional[str] = None):
    if DEMO_MODE:
        return build_demo_latest(device_type)

    base_query = f'''
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -10m)
    '''
    if device_type:
        base_query += f'|> filter(fn: (r) => r._measurement == "{device_type}")'
    base_query += '''
        |> filter(fn: (r) => r._field != "")
        |> last()
    '''
    try:
        tables = query_api.query(base_query, org=INFLUX_ORG)
        results = []
        for table in tables:
            for record in table.records:
                results.append({
                    'device_type': record.get_measurement(),
                    'device_id': record.values.get('device_id'),
                    'field': record.get_field(),
                    'value': record.get_value(),
                    'time': record.get_time().strftime('%Y-%m-%d %H:%M:%S'),
                })
        grouped_results = {}
        for r in results:
            d_id = r['device_id']
            if d_id not in grouped_results:
                grouped_results[d_id] = {
                    'device_id': d_id,
                    'device_type': r['device_type'],
                    'last_update': r['time'],
                }
            grouped_results[d_id][r['field']] = r['value']
        return {'status': 'success', 'demo_mode': False, 'data': list(grouped_results.values())}
    except Exception as e:
        return {**build_demo_latest(device_type), 'message': f'InfluxDB 未就绪，已切换演示模式: {str(e)}'}


@app.get('/api/v1/sensors/history/{device_id}')
def get_sensor_history(device_id: str, minutes: int = 60):
    if DEMO_MODE:
        return build_demo_history(device_id, minutes)

    query = f'''
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -{minutes}m)
        |> filter(fn: (r) => r.device_id == "{device_id}")
    '''
    try:
        tables = query_api.query(query, org=INFLUX_ORG)
        history = []
        for table in tables:
            for record in table.records:
                history.append({
                    'field': record.get_field(),
                    'value': record.get_value(),
                    'time': record.get_time().strftime('%H:%M:%S'),
                })
        return {'status': 'success', 'device_id': device_id, 'demo_mode': False, 'data': history}
    except Exception as e:
        return {**build_demo_history(device_id, minutes), 'message': f'查询历史数据失败，已切换演示模式: {str(e)}'}


# ==============================
# 现实感模拟接口（用于演示/联调）
# ==============================


def _risk_level_by_score(score: float) -> str:
    if score >= 85:
        return 'critical'
    if score >= 65:
        return 'warning'
    if score >= 40:
        return 'monitor'
    return 'safe'


@app.get('/api/v1/mock/site/weather')
def get_mock_weather():
    snap = build_sensor_snapshot()
    phase = snap['phase']
    wind = 3.8 + (snap['seismic'] / 40)
    visibility = 4800 - (1200 if phase in ['warning', 'dispatch'] else 300)
    rainfall = 0.0 if phase in ['stable', 'precursor'] else (1.2 if phase == 'warning' else 0.4)
    return {
        'status': 'success',
        'demo_mode': True,
        'timestamp': snap['time'],
        'data': {
            'wind_speed_mps': round(wind, 1),
            'wind_direction_deg': int((snap['progress'] * 260 + 70) % 360),
            'visibility_m': int(max(1200, visibility)),
            'temperature_c': round(17.5 + math.sin(datetime.now().timestamp() / 1800) * 6, 1),
            'humidity_pct': int(56 + math.sin(datetime.now().timestamp() / 1500) * 10),
            'rainfall_mm_h': round(rainfall, 1),
            'flight_condition': 'restricted' if phase in ['warning', 'dispatch'] else 'allowed'
        }
    }


@app.get('/api/v1/mock/slope/risk-index')
def get_mock_slope_risk(zone_id: str = 'SLOPE-ZONE-A'):
    snap = build_sensor_snapshot()
    score = (
        snap['crack'] * 8.5
        + snap['seismic'] * 1.3
        + snap['angle'] * 180
        + snap['settlement'] * 5.2
    )
    score = max(0.0, min(100.0, round(score, 2)))
    level = _risk_level_by_score(score)
    return {
        'status': 'success',
        'demo_mode': True,
        'zone_id': zone_id,
        'timestamp': snap['time'],
        'data': {
            'risk_score': score,
            'risk_level': level,
            'drivers': {
                'crack_width_mm': snap['crack'],
                'seismic_energy_j': snap['seismic'],
                'tilt_deg': snap['angle'],
                'settlement_mm': snap['settlement']
            },
            'suggestion': {
                'critical': '立即停采并启动无人机与人工复核',
                'warning': '提高巡检频次并触发预警广播',
                'monitor': '维持监测并观察趋势',
                'safe': '保持常规巡检'
            }[level]
        }
    }


@app.get('/api/v1/mock/fleet/realtime')
def get_mock_fleet_realtime():
    snap = build_sensor_snapshot()
    phase = snap['phase']
    base_trucks = [
        {'device_id': 'TR-101', 'type': 'truck', 'zone': '装车区A'},
        {'device_id': 'TR-118', 'type': 'truck', 'zone': '运输主线'},
        {'device_id': 'TR-123', 'type': 'truck', 'zone': '卸料口'},
    ]
    uavs = [
        {'device_id': 'UAV-EAGLE-01', 'type': 'uav', 'zone': '边坡巡检区'},
        {'device_id': 'UAV-MAPPER-02', 'type': 'uav', 'zone': '高风险区外环'},
    ]
    records = []
    for i, d in enumerate(base_trucks + uavs):
        moving = phase in ['warning', 'dispatch'] or i % 2 == 0
        records.append({
            'device_id': d['device_id'],
            'device_type': d['type'],
            'zone': d['zone'],
            'speed_kmh': round((18 + i * 3 + snap['progress'] * 8) if moving else 0, 1),
            'fuel_pct': max(8, 86 - i * 9 - int(snap['progress'] * 12)),
            'online': True,
            'status': 'executing' if moving else 'idle',
            'eta_min': max(2, 14 - i * 2 - int(snap['progress'] * 3))
        })
    return {
        'status': 'success',
        'demo_mode': True,
        'timestamp': snap['time'],
        'data': records
    }


@app.get('/api/v1/mock/dispatch/events')
def get_mock_dispatch_events(limit: int = 10):
    snap = build_sensor_snapshot()
    now = datetime.now()
    phase = snap['phase']
    events = [
        {'level': 'info', 'event': '班前点检完成，设备上线率 96%'},
        {'level': 'info', 'event': '矿卡 TR-118 进入主运输线'},
        {'level': 'warning', 'event': '边坡微震能量持续抬升，建议关注'},
        {'level': 'warning', 'event': 'SLOPE-ZONE-A 裂缝宽度接近阈值'},
        {'level': 'critical', 'event': '触发三级告警，建议启动无人机复核'},
        {'level': 'info', 'event': '应急工单已下发，等待执行反馈'}
    ]
    idx_map = {'stable': 2, 'precursor': 3, 'warning': 4, 'dispatch': 5, 'recovery': 6}
    take = idx_map.get(phase, 3)
    sel = events[:take][-max(1, min(limit, 30)):]
    out = []
    for i, e in enumerate(reversed(sel)):
        out.append({
            'id': f'EVT-{int(now.timestamp())}-{i}',
            'time': (now - timedelta(minutes=i * 3)).strftime('%Y-%m-%d %H:%M:%S'),
            'level': e['level'],
            'event': e['event']
        })
    return {'status': 'success', 'demo_mode': True, 'data': out}


@app.get('/api/v1/mock/dashboard/overview')
def get_mock_dashboard_overview():
    snap = build_sensor_snapshot()
    risk = get_mock_slope_risk()['data']
    weather = get_mock_weather()['data']
    fleet = get_mock_fleet_realtime()['data']
    return {
        'status': 'success',
        'demo_mode': True,
        'timestamp': snap['time'],
        'data': {
            'scene_phase': snap['phase'],
            'risk': risk,
            'weather': weather,
            'fleet_online': sum(1 for x in fleet if x['online']),
            'fleet_active': sum(1 for x in fleet if x['status'] == 'executing'),
            'kpi': {
                'today_output_tons': round(5200 + snap['progress'] * 320, 1),
                'avg_efficiency_tph': round(182 + snap['progress'] * 11, 1),
                'alarm_count_24h': 7 if risk['risk_level'] in ['critical', 'warning'] else 3
            }
        }
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)

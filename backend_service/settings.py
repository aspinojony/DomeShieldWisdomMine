import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'mining_system.db'}")
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'qiandun-smart-mine-2026-secret-key-do-not-leak')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '480'))
CORS_ALLOW_ORIGINS = os.getenv('CORS_ALLOW_ORIGINS', '*').split(',')
DEFAULT_ADMIN_USERNAME = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
DEFAULT_ADMIN_PASSWORD = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
INFLUX_URL = os.getenv('INFLUX_URL', 'http://127.0.0.1:8086')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN', 'my-super-secret-auth-token')
INFLUX_ORG = os.getenv('INFLUX_ORG', 'mining')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET', 'sensor_data')
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'

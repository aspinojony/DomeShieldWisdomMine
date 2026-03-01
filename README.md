# 穹盾智矿 (DomeShield Wisdom Mine)

> 露井联采空天地一体化智能预警中枢
>
> Sky-Earth Integrated Intelligent Warning Center for Open-Pit and Underground Mining

本项目是一个全面、智能、基于现代 Web 体系构建的矿山安全监控与预警数字孪生中枢系统。它通过整合多源传感器数据（GNSS、微震仪、表面裂缝计、深井应力计、无人机巡检等），配合 AI 预测与识别模型，为露井联合开采提供一体化的数字大屏监控及后台业务管理能力。

## 🎯 系统核心特性 (Features)

- 💻 **WebGL 3D 数字孪生引擎**：利用 Three.js 实现露天矿坑程序化生成、动态渲染设备点位（基站、微震监测站、沉降监测站等），全视角漫游与交互。
- 📊 **数据大屏与实时可视化**：搭载 ECharts，包含双 Y 轴波形图、动态散点图、雷达图、环形仪表盘等。大屏支持暗黑工业科幻风 (Glassmorphism)。
- 🤖 **AI 预警中枢**：内置 YOLOv8 视觉识别（用于无人机裂缝检测）与 Transformer 时序预测模型引擎（通过 `ai_core` 服务支持）。
- 📡 **多源异构数据接入**：利用 Kafka 与 MQTT 接入各类边缘端物联网设备，支持 WebSocket 实时推送到大屏层。
- 🔒 **完善的 RBAC 后台管理**：
  - **权限架构**：管理员 (Admin)、工程师 (Engineer) 及访问者 (Viewer) 的角色分离体系。
  - **业务后台 (Admin Panel)**：可对设备台账进行增删改查、配置基于指标 (`metric_field`) 阈值的智能化告警规则、并提供了告警记录的一键闭环（ACK）处理模块。

---

## 🏗 开源架构设计 (Architecture)

项目遵循微服务及模块化理念布局，各目录主要职责如下：

```text
├── frontend_dashboard/     # 前端数据大屏与后台管理中心 (Vue 3 + Vite + ECharts + Three.js)
├── backend_service/        # 后端核心 API 与业务逻辑 (FastAPI + SQLAlchemy + WebSocket)
├── ai_core/                # 核心 AI 模型与推理模块 (PyTorch + YOLOv8 + Timeseries Transformer)
├── mock_devices/           # 硬件端数据模拟与压力测试 (MQTT IoT Mocks)
├── ops/                    # 部署运维与容器编排 (Docker Compose / Nginx)
└── README.md               # 项目介绍
```

---

## 🚀 快速启动 (Quick Start)

### 1. 运行后端服务 (Backend Service)

后端主要基于 Python 3.10+ 环境。

```bash
cd backend_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动 FastAPI 服务
uvicorn main:app --host 127.0.0.1 --port 8002 --reload
```

后端 API 文档将在 `http://127.0.0.1:8002/docs` 生成。

### 2. 运行前端大屏 (Frontend Dashboard)

前端依赖于 Node.js (推荐 v18+)。

```bash
cd frontend_dashboard
npm install

# 启动本地开发服务器
npm run dev
```

浏览器打开 `http://localhost:5173` 即可查看**穹盾智矿大屏**。
_默认预置的系统管理员账号: `admin`，密码: `123123`_

### 3. 数据接入 (Data Ingestion) / AI 核心 (Optional)

需要完整的流处理（Kafka / MQTT），可以通过 ops 提供的 Docker Compose 快速唤起消息中间件网络：

```bash
cd ops
docker-compose up -d
```

模拟矿山设备发送数据：

```bash
python mock_devices/iot_sensor_simulator.py
```

---

## 🛠 关键技术栈 (Tech Stack)

- **Frontend**: Vue 3.x, Vue Router 4, Axios, Vite
- **Visualization**: Three.js, ECharts, HTML5 Canvas
- **Backend**: Python, FastAPI, SQLAlchemy, SQLite (可平滑迁移为 PostgreSQL), Passlib
- **IoT Data Link**: MQTT (Paho), Apache Kafka, WebSockets
- **AI Engine**: PyTorch, HuggingFace Transformers, YOLO Ecosystem

---

## 📜 许可证 (License)

本项目受开源协议保护，仅供学习、2026 年度挑战杯等学术及演示交流使用。商业用途或核心机密修改请遵守团队所属规范。

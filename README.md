# 穹盾智矿 · DomeShield Wisdom Mine

> 露天矿 / 地下矿空天地一体化智能预警与生产调度演示系统

穹盾智矿是一个面向矿山安全监测、风险预警、无人机视觉复核与生产运营指挥的综合演示系统。项目把 **传感器监测、AI 时序预警、YOLO 裂缝识别、业务后台、三维大屏** 串成一条完整链路，用于课程项目、竞赛答辩、方案演示和后续工程化扩展。

---

## 1. 这套系统现在能做什么

### 安全监测
- 接入裂缝计、微震、倾角、沉降等监测数据
- 支持实时态势展示与历史趋势查看
- 支持告警规则配置、告警记录查询、人工 ACK 闭环

### AI 预警
- 通过时序模型模拟矿山风险演化过程
- 在演示模式下自动生成“稳定 → 先兆 → 预警 → 调度 → 恢复”的场景周期
- 高风险时可触发无人机复核链路

### 无人机视觉识别
- 提供 YOLOv8 裂缝识别服务
- 支持上传图片进行裂缝检测
- 输出识别框、异常数量、最大裂缝宽度、告警等级、结果图
- 保存历史识别记录，供前端查看

### 业务与调度
- 用户登录与 RBAC 权限控制
- 设备台账管理
- 告警规则管理
- 任务/工单/无人机任务等业务能力
- 生产运营页面与首页联动展示

### 前端展示
- 首页矿山大屏：地图、态势、告警、无人机视觉联测、KPI 总览
- 智能识别页：视觉结果查看、历史识别记录、人工上传分析
- 生产运营页：面向调度与处置的业务化工作台

---

## 2. 当前技术架构

```text
frontend_dashboard/   Vue3 + Vite + Axios + ECharts + Cesium
backend_service/      FastAPI + SQLAlchemy + JWT + SQLite
ai_core/              YOLOv8 裂缝识别 / 时序模型相关代码
mock_devices/         设备数据模拟
ops/                  Docker Compose 部署编排
scripts/              本地启停/检查脚本
```

### 服务划分

| 服务 | 端口 | 说明 |
|---|---:|---|
| frontend | 80 / 5173 | 前端页面 |
| api-server | 8000 | 监测数据 / 演示传感器接口 |
| ai-engine | 8001 | AI 风险推演 / 无人机联动模拟 |
| business-api | 8002 | 登录、权限、设备、规则、业务数据 |
| vision-engine | 8003 | YOLO 裂缝视觉识别 |

---

## 3. 关键能力说明

### 3.1 首页演示链路
首页已经从“纯动效页面”改成了**动态演示链路**：
- 传感器数据会随时间变化
- 矿山总览数据会随场景变化联动
- 无人机状态会随风险阶段切换
- 最新视觉结果会从视觉服务实时读取

### 3.2 YOLO 裂缝模型接入
当前视觉服务支持通过配置或环境变量加载训练权重：
- 默认配置文件：`ai_core/configs/cv_yolo.yaml`
- 当前接入权重：`ai_core/checkpoints/crack_yolo_best.pt`
- 环境变量覆盖：`YOLO_WEIGHTS_PATH`

### 3.3 演示模式
项目包含大量演示兜底逻辑，适合答辩和离线展示：
- 后端接口在依赖不完整时仍可返回演示数据
- 首页、AI、视觉、生产运营可在本地独立联调
- 不依赖真实矿山数据也能跑完整流程

---

## 4. 快速启动

## 方式 A：本地开发启动

### 4.1 前端
```bash
cd frontend_dashboard
npm install
npm run dev
```

### 4.2 后端与 AI
请分别准备 Python 环境后启动：

```bash
# 业务 API
uvicorn backend_service.business_api:app --host 0.0.0.0 --port 8002

# 监测 API
python backend_service/api_server.py

# AI 风险引擎
python backend_service/ai_prediction_engine.py

# 视觉引擎
python ai_core/vision_inference_service.py
```

### 4.3 本地检查
```bash
bash scripts/check.sh
```

---

## 方式 B：Docker Compose 部署

```bash
cd ops
DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 docker compose -f docker-compose.deploy.yml up -d --build
```

适用于：
- 本机演示环境
- 服务器演示部署
- 答辩前一次性拉起全部服务

---

## 5. 默认账号

如果业务库为空，系统会自动创建默认管理员：

- 用户名：`admin`
- 密码：`admin123`

> 实际部署时请务必修改默认口令。

---

## 6. 推荐阅读顺序

如果你第一次接手这个项目，建议按下面顺序看：

1. `README.md` —— 先理解整体结构
2. `项目文档.md` —— 看详细模块与部署说明
3. `ops/docker-compose.deploy.yml` —— 看演示部署方式
4. `frontend_dashboard/src/components/MiningDashboard.vue` —— 看首页主逻辑
5. `backend_service/business_api.py` —— 看业务主接口
6. `ai_core/vision_inference_service.py` —— 看视觉识别链路

---

## 7. 当前仓库内的重要文件

| 文件 | 作用 |
|---|---|
| `README.md` | 项目总览说明 |
| `项目文档.md` | 详细技术与部署文档 |
| `PRODUCTION-OPS-REDESIGN.md` | 生产运营页重构设计说明 |
| `PRODUCTION-OPS-IMPLEMENTATION.md` | 生产运营页实现设计 |
| `ops/docker-compose.deploy.yml` | 演示环境编排 |
| `scripts/start.sh` | 本地启动脚本 |
| `scripts/check.sh` | 服务健康检查脚本 |
| `scripts/stop.sh` | 本地停止脚本 |

---

## 8. 注意事项

- `模型/` 目录中的训练原始素材很大，不建议直接纳入仓库管理
- 当前仓库已保留实际使用的推理权重 `crack_yolo_best.pt`
- Docker 在 macOS 上首次构建会比较慢，尤其是 PyTorch / OpenCV 相关依赖
- 如果遇到 BuildKit 异常，可切到 legacy builder：

```bash
DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 docker compose -f ops/docker-compose.deploy.yml up -d --build
```

---

## 9. 项目定位

这不是一个完全工业落地的生产系统，而是一套 **“可演示、可联调、可继续扩展的矿山数字孪生与预警平台原型”**。

它最适合：
- 课程设计 / 毕设 / 比赛答辩
- 展示矿山空天地一体化方案
- 后续继续迭代成更完整的工程项目


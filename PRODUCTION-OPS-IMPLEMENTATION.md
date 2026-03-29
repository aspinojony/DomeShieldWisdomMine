# 生产运营页实现文档

基于 `PRODUCTION-OPS-REDESIGN.md`，本文件继续定义：
- 组件清单
- 接口映射
- 状态联动机制
- 开发顺序

---

## 一、组件清单

## 1. 页面骨架层

### `OperationsWorkbench.vue`
生产运营页主容器。

职责：
- 组织五大区域布局（顶部 / 左栏 / 中间地图 / 右栏 / 底部）
- 提供全局上下文 `currentContext`
- 管理全局刷新与状态同步

---

## 2. 顶部区域

### `OpsGlobalKpiBar.vue`
顶部态势栏。

显示：
- 今日产量
- 班次完成率
- 在线设备数
- 执行中任务数
- 未闭环告警数
- 高风险区域数

操作：
- 新建调度任务
- 发起无人机复核
- 进入应急处置

---

## 3. 左栏区域

### `OpsWorkbenchTabs.vue`
左栏容器，3 个 Tab：
- 实时告警
- 执行中任务
- 待确认事件

### `AlertQueuePanel.vue`
显示实时告警列表。

每项支持：
- 地图定位
- 指派处理
- 生成工单

### `TaskQueuePanel.vue`
显示执行中任务。

每项支持：
- 查看详情
- 改状态
- 改派
- 终止

### `PendingReviewPanel.vue`
显示待确认事件。

来源：
- AI识别结果待确认
- 无人机巡检待复核
- 人工待确认异常

---

## 4. 中间区域

### `OpsDispatchMap.vue`
调度地图容器。

显示：
- 设备点位
- 风险区域
- 当前任务路径
- 拥堵节点

交互：
- 选中设备
- 选中区域
- 选中任务
- 定位与高亮

### `MapQuickActions.vue`
地图上的最小操作层。

仅保留：
- 回到全局
- 高亮风险区
- 显示任务路径
- 进入区域处置

---

## 5. 右栏区域

### `ContextDetailPanel.vue`
右侧详情容器，根据 `currentContext.type` 切换子面板。

### `AlertDetailCard.vue`
告警详情。

显示：
- 告警摘要
- AI/传感器证据
- 推荐动作

操作：
- 派单
- 复核
- 标记处理中

### `TaskDetailCard.vue`
任务详情。

显示：
- 任务编号
- 执行设备
- 线路
- 进度
- 异常记录

操作：
- 改派
- 暂停
- 完成
- 关闭

### `DeviceDetailCard.vue`
设备详情。

显示：
- 设备状态
- 当前任务
- 最近异常
- 所属区域

操作：
- 指派任务
- 调整路线
- 请求复核

---

## 6. 底部区域

### `OpsExecutionTimeline.vue`
底部处置流水。

显示：
- 告警触发
- 人工接管
- 工单生成
- 指令下发
- 执行反馈
- 关闭事件

操作：
- 查看详情
- 增加备注
- 关闭事件

---

## 二、接口映射表

## 1. 顶部 KPI

### 今日产量 / 班次完成率 / 在线设备数
接口：
- `GET /api/v1/ops/mining-summary`

字段：
- `production_today.current`
- `production_today.target`
- `asset_stats.*.online`
- `asset_stats.*.total`

### 执行中任务数
接口：
- `GET /api/v1/ops/tasks/active`

字段：
- 返回数组长度

### 未闭环告警数
接口：
- `GET /api/v1/ops/mining-summary`

字段：
- `recent_alerts.length`

### 高风险区域数
V1 可前端计算：
- 根据 `recent_alerts` 去重 `zone_id / device_id`
- 或根据视觉/风险结果聚合

---

## 2. 左栏 - 实时告警
接口：
- `GET /api/v1/ops/mining-summary`
- `GET /api/v1/vision/latest`
- 未来可加：`GET /api/v1/alerts/open`

字段来源：
- `recent_alerts[]`
- `vision/latest.data`

---

## 3. 左栏 - 执行中任务
接口：
- `GET /api/v1/ops/tasks/active`
- `GET /api/v1/uav/missions`

V1 可先前端聚合：
- 运输任务 + 无人机任务 合并为统一任务流

---

## 4. 左栏 - 待确认事件
V1 可由前端生成：
来源：
- `vision/latest`
- AI 识别结果
- 未闭环告警

未来建议接口：
- `GET /api/v1/events/pending-review`

---

## 5. 地图区域
接口：
- `GET /api/v1/sensors/latest`
- `GET /api/v1/devices`
- `GET /api/v1/ops/fleet/status`

字段：
- 点位坐标
- 设备状态
- 当前任务关联

---

## 6. 右栏详情

### 告警详情
接口：
- `GET /api/v1/ops/mining-summary`
- `GET /api/v1/vision/latest`
- `GET /api/v1/sensors/history/{device_id}`

### 任务详情
接口：
- `GET /api/v1/ops/tasks/active`
- `GET /api/v1/uav/missions`

### 设备详情
接口：
- `GET /api/v1/devices`
- `GET /api/v1/sensors/latest`
- `GET /api/v1/sensors/history/{device_id}`

---

## 7. 底部处置流水
V1 方案：
前端聚合以下事件：
- 告警进入
- 人工点击“处理中”
- 任务创建
- 状态更新
- 关闭事件

未来建议接口：
- `GET /api/v1/ops/execution-timeline`
- `POST /api/v1/ops/timeline/event`

---

## 三、联动状态设计

建议建立统一状态：

```ts
currentContext = {
  type: 'alert' | 'task' | 'device' | 'zone' | null,
  id: string | null,
  source: 'map' | 'alert-list' | 'task-list' | 'vision' | null,
  payload: any,
  timestamp: number
}
```

---

## 联动规则

### 点击告警
- 设置 `currentContext = alert`
- 地图定位到告警区域
- 右栏显示告警详情
- 底部显示该告警相关流水

### 点击任务
- 设置 `currentContext = task`
- 地图显示任务路径
- 右栏显示任务详情
- 左栏高亮对应设备/区域

### 点击设备
- 设置 `currentContext = device`
- 右栏显示设备详情
- 左栏过滤该设备相关告警/任务

### 点击 AI 识别结果
- 生成待确认事件
- 设置 `currentContext = alert`
- 跳到处置流

---

## 四、开发顺序（建议严格按顺序）

## 阶段 1：打骨架（先别搞样式）
1. 新建 `OperationsWorkbench.vue`
2. 建立顶部 / 左栏 / 地图 / 右栏 / 底部五区结构
3. 建立 `currentContext`
4. 跑通基本数据加载

目标：页面结构稳定、模块职责明确。

---

## 阶段 2：左栏与地图联动
1. 实现实时告警列表
2. 实现任务列表
3. 实现待确认事件列表
4. 地图点选联动 `currentContext`

目标：点哪里，右边和地图都能跟着变。

---

## 阶段 3：右栏详情与动作
1. 告警详情卡
2. 任务详情卡
3. 设备详情卡
4. 接入动作按钮（派单 / 改状态 / 关闭）

目标：这个页开始“能操作”。

---

## 阶段 4：底部流水
1. 建立执行流水数据结构
2. 所有动作写入流水
3. 支持备注与关闭状态

目标：形成闭环感。

---

## 阶段 5：AI 联动接入
1. AI结果进入待确认事件
2. 视觉结果可一键转任务
3. 无人机任务与生产运营任务统一视图

目标：整个系统真正串起来。

---

## 五、V1 最终可交付成果

V1 完成后，这个页面应满足：

- 可看：看到态势、任务、告警、风险
- 可点：任意对象可定位与联动
- 可操作：能派单、改状态、发起复核
- 可跟踪：能看到执行过程
- 可闭环：能标记完成与归档

这时它才算真正成为：

> **生产调度与安全处置台**

而不是展示页。


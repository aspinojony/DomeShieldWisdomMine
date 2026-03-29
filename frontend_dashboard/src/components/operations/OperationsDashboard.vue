<template>
  <div class="ops-page">
    <Map3DViewer />

    <div class="ops-shell">
      <!-- 顶部总览 -->
      <header class="top-bar panel">
        <div>
          <h1>生产运营与调度处置台</h1>
          <div class="sub-line">面向人工调度、风险处置与执行闭环</div>
        </div>
        <div class="top-kpis">
          <div class="kpi-card" v-for="item in topKpis" :key="item.label">
            <span class="kpi-label">{{ item.label }}</span>
            <strong class="kpi-value" :class="item.emphasis">{{ item.value }}</strong>
            <small class="kpi-unit">{{ item.unit }}</small>
          </div>
        </div>
        <div class="quick-actions">
          <button class="action-btn primary" @click="createDispatchTask">新建调度任务</button>
          <button class="action-btn" @click="startUavReview">发起无人机复核</button>
          <button class="action-btn danger" @click="enterEmergency">进入应急处置</button>
        </div>
      </header>

      <div class="content-grid">
        <!-- 左栏 -->
        <aside class="left-panel panel">
          <div class="tab-header">
            <button :class="['tab-btn', { active: activeTab === 'alerts' }]" @click="activeTab = 'alerts'">实时告警</button>
            <button :class="['tab-btn', { active: activeTab === 'tasks' }]" @click="activeTab = 'tasks'">执行中任务</button>
            <button :class="['tab-btn', { active: activeTab === 'reviews' }]" @click="activeTab = 'reviews'">待确认事件</button>
          </div>

          <div class="tab-body">
            <template v-if="activeTab === 'alerts'">
              <div
                v-for="alert in alertQueue"
                :key="alert.id"
                class="list-item"
                :class="['level-' + alert.level, { selected: isSelected('alert', alert.id) }]"
                @click="selectContext('alert', alert.id, alert, 'alert-list')"
              >
                <div class="item-head">
                  <strong>{{ alert.title }}</strong>
                  <span class="item-tag">{{ alert.status }}</span>
                </div>
                <div class="item-sub">{{ alert.zone }} · {{ alert.time }}</div>
                <div class="item-desc">{{ alert.message }}</div>
                <div class="item-actions">
                  <button @click.stop="selectContext('alert', alert.id, alert, 'alert-list')">定位</button>
                  <button @click.stop="markProcessing(alert)">处理中</button>
                  <button @click.stop="createTaskFromAlert(alert)">派单</button>
                </div>
              </div>
            </template>

            <template v-else-if="activeTab === 'tasks'">
              <div
                v-for="task in taskQueue"
                :key="task.id"
                class="list-item"
                :class="[{ selected: isSelected('task', task.id) }]"
                @click="selectContext('task', task.id, task, 'task-list')"
              >
                <div class="item-head">
                  <strong>#{{ task.task_id }}</strong>
                  <span class="item-tag">{{ formatStatus(task.status) }}</span>
                </div>
                <div class="item-sub">{{ task.vehicle_id }} · {{ task.load_zone }} → {{ task.unload_zone }}</div>
                <div class="item-desc">预估载重 {{ task.weight_tons }} 吨</div>
                <div class="item-actions">
                  <button @click.stop="selectContext('task', task.id, task, 'task-list')">详情</button>
                  <button @click.stop="updateTaskStatus(task, 'hauling')">推进</button>
                  <button @click.stop="closeTask(task)">关闭</button>
                </div>
              </div>
            </template>

            <template v-else>
              <div
                v-for="review in pendingReviews"
                :key="review.id"
                class="list-item pending"
                :class="[{ selected: isSelected('review', review.id) }]"
                @click="selectContext('review', review.id, review, 'review-list')"
              >
                <div class="item-head">
                  <strong>{{ review.title }}</strong>
                  <span class="item-tag">待人工确认</span>
                </div>
                <div class="item-sub">{{ review.source }} · {{ review.time }}</div>
                <div class="item-desc">{{ review.message }}</div>
                <div class="item-actions">
                  <button @click.stop="confirmReview(review)">确认事件</button>
                  <button @click.stop="startUavReview(review)">无人机复核</button>
                </div>
              </div>
            </template>
          </div>
        </aside>

        <!-- 中间地图主视图 -->
        <main class="center-panel">
          <div class="map-toolbar panel">
            <button class="mini-btn">全局视图</button>
            <button class="mini-btn">风险区域</button>
            <button class="mini-btn">任务路径</button>
          </div>
        </main>

        <!-- 右栏详情 -->
        <aside class="right-panel panel">
          <div class="detail-header">
            <h2>上下文详情</h2>
            <span class="context-badge">{{ currentContext.type || '未选中' }}</span>
          </div>

          <div v-if="!currentContext.type" class="empty-state">
            请从左侧告警、任务或待确认事件中选择一个对象开始处置。
          </div>

          <template v-else>
            <div class="detail-section">
              <div class="detail-title">对象摘要</div>
              <div class="detail-grid">
                <div class="kv"><span>编号</span><strong>{{ currentContext.payload?.id || currentContext.payload?.task_id || '-' }}</strong></div>
                <div class="kv"><span>来源</span><strong>{{ currentContext.source }}</strong></div>
                <div class="kv"><span>区域</span><strong>{{ currentContext.payload?.zone || currentContext.payload?.load_zone || 'SLOPE-ZONE-A' }}</strong></div>
                <div class="kv"><span>状态</span><strong>{{ currentContext.payload?.status || currentContext.payload?.level || '待处理' }}</strong></div>
              </div>
            </div>

            <div class="detail-section">
              <div class="detail-title">关联证据</div>
              <div class="detail-text">{{ evidenceText }}</div>
            </div>

            <div class="detail-section">
              <div class="detail-title">人工操作</div>
              <div class="detail-actions">
                <button class="action-btn primary" @click="appendTimeline('人工接管', currentContext.payload?.title || currentContext.payload?.task_id || currentContext.type)">人工接管</button>
                <button class="action-btn" @click="createDispatchTask">生成调度任务</button>
                <button class="action-btn" @click="startUavReview">发起无人机复核</button>
                <button class="action-btn danger" @click="appendTimeline('关闭事件', currentContext.payload?.title || currentContext.payload?.task_id || currentContext.type)">关闭事件</button>
              </div>
            </div>
          </template>
        </aside>
      </div>

      <!-- 底部流水 -->
      <footer class="timeline-panel panel">
        <div class="timeline-head">
          <h2>处置闭环流水</h2>
          <span>{{ timeline.length }} 条记录</span>
        </div>
        <div class="timeline-list">
          <div class="timeline-item" v-for="event in timeline" :key="event.id">
            <div class="timeline-time">{{ event.time }}</div>
            <div class="timeline-body">
              <strong>{{ event.action }}</strong>
              <div>{{ event.target }}</div>
            </div>
            <div class="timeline-meta">{{ event.operator }}</div>
          </div>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, computed } from 'vue'
import axios from 'axios'
import { useOperationsStore } from '../../store/operations'
import Map3DViewer from './Map3DViewer.vue'

const store = useOperationsStore()
const activeTab = ref('alerts')
const latestVision = ref(null)
let timer = null
let seq = 1000

const currentContext = ref({
  type: null,
  id: null,
  source: null,
  payload: null,
  timestamp: null,
})

const alertQueue = ref([
  { id: 'ALT-001', title: '边坡裂缝异常', zone: 'SLOPE-ZONE-A', level: 'danger', status: '待处理', time: '01:08', message: '裂缝宽度持续上升，建议发起复核' },
  { id: 'ALT-002', title: '运输卡口拥堵', zone: '主运输线', level: 'warning', status: '处理中', time: '01:05', message: '矿卡等待时长超过阈值' },
  { id: 'ALT-003', title: '风速波动升高', zone: '西侧作业区', level: 'warning', status: '待处理', time: '01:02', message: '飞行条件接近受限阈值' },
])

const pendingReviews = ref([
  { id: 'REV-001', title: 'AI识别待确认', source: '裂缝识别模型', time: '01:09', message: '识别到 3 处裂缝，等待人工确认是否转派单' },
  { id: 'REV-002', title: '无人机巡检待复核', source: '空天指控集群', time: '01:06', message: '边坡区域回传图像已生成，需要人工查看' },
])

const timeline = ref([
  { id: 1, time: '01:00', action: '系统告警', target: '边坡裂缝异常', operator: '系统' },
  { id: 2, time: '01:03', action: '任务下发', target: '矿卡调度 #1024', operator: '调度员' },
  { id: 3, time: '01:07', action: '执行反馈', target: '主运输线拥堵缓解', operator: '系统' },
])

const taskQueue = computed(() => store.displayTasks)

const topKpis = computed(() => {
  const totalAlerts = alertQueue.value.filter(a => a.status !== '已闭环').length
  const riskZones = new Set(alertQueue.value.map(a => a.zone)).size
  return [
    { label: '今日产量', value: store.kpi.total_tonnage || 0, unit: '吨' },
    { label: '班次完成率', value: `${Math.round(((store.kpi.total_tonnage || 0) / 1200) * 100)}%`, unit: '目标 1200 吨' },
    { label: '在线设备', value: store.kpi.active_vehicle_count || 0, unit: '台' },
    { label: '执行中任务', value: taskQueue.value.length, unit: '条' },
    { label: '未闭环告警', value: totalAlerts, unit: '条', emphasis: 'danger-text' },
    { label: '高风险区域', value: riskZones, unit: '个' },
  ]
})

const suggestedAction = computed(() => {
  if (!currentContext.value.type) return '请选择左侧对象开始处置'
  if (currentContext.value.type === 'alert') return '先定位区域，再派发复核或调度任务'
  if (currentContext.value.type === 'task') return '跟踪执行状态，必要时改派或关闭'
  if (currentContext.value.type === 'review') return '先人工确认，再决定是否进入调度流'
  return '查看详情'
})

const evidenceText = computed(() => {
  if (currentContext.value.type === 'alert') return currentContext.value.payload?.message || '暂无告警证据'
  if (currentContext.value.type === 'task') return `当前任务路线：${currentContext.value.payload?.load_zone} → ${currentContext.value.payload?.unload_zone}`
  if (currentContext.value.type === 'review') return currentContext.value.payload?.message || '待人工复核事件'
  return '暂无证据'
})

const selectContext = (type, id, payload, source) => {
  currentContext.value = { type, id, payload, source, timestamp: Date.now() }
}

const isSelected = (type, id) => currentContext.value.type === type && currentContext.value.id === id

const appendTimeline = (action, target, operator = '调度员') => {
  const d = new Date()
  timeline.value.unshift({
    id: ++seq,
    time: d.toTimeString().slice(0, 5),
    action,
    target,
    operator,
  })
}

const createDispatchTask = () => {
  appendTimeline('新建调度任务', currentContext.value.payload?.title || '人工创建任务')
  activeTab.value = 'tasks'
}

const startUavReview = (payload = null) => {
  appendTimeline('发起无人机复核', payload?.title || currentContext.value.payload?.title || '边坡区域复核')
}

const enterEmergency = () => {
  appendTimeline('进入应急处置', currentContext.value.payload?.title || '全局应急模式')
}

const markProcessing = (alert) => {
  alert.status = '处理中'
  appendTimeline('告警转处理中', alert.title)
  selectContext('alert', alert.id, alert, 'alert-list')
}

const createTaskFromAlert = (alert) => {
  appendTimeline('告警转派单', alert.title)
  alert.status = '处理中'
  activeTab.value = 'tasks'
}

const updateTaskStatus = (task, next) => {
  task.status = next
  appendTimeline('任务状态更新', `#${task.task_id} → ${formatStatus(next)}`)
  selectContext('task', task.id, task, 'task-list')
}

const closeTask = (task) => {
  appendTimeline('任务关闭', `#${task.task_id}`)
  task.status = 'returning'
}

const confirmReview = (review) => {
  appendTimeline('确认待复核事件', review.title)
  selectContext('review', review.id, review, 'review-list')
}

const formatStatus = (s) => ({ loading: '装载中', hauling: '运输中', unloading: '卸载中', returning: '返程中' }[s] || s)

const fetchVision = async () => {
  try {
    const res = await axios.get(`http://${window.location.hostname}:8003/api/v1/vision/latest`)
    if (res.data?.status === 'success') latestVision.value = res.data.data
  } catch {}
}

onMounted(() => {
  store.fetchAllData()
  fetchVision()
  timer = setInterval(() => {
    store.fetchAllData()
    fetchVision()
  }, 10000)
})

onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.ops-page {
  position: relative;
  min-height: 100vh;
  background: #08111d;
  color: #dbe4f0;
  overflow: hidden;
}

.ops-shell {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: grid;
  grid-template-rows: 72px 1fr 148px;
  gap: 8px;
  padding: 10px;
}

.panel {
  background: rgba(8, 18, 32, 0.92);
  border: 1px solid rgba(0, 240, 255, 0.16);
  border-radius: 10px;
  backdrop-filter: blur(4px);
}

.top-bar {
  display: grid;
  grid-template-columns: 220px 1fr 280px;
  gap: 10px;
  align-items: stretch;
  padding: 10px 12px;
}
.top-bar h1 { margin: 0; font-size: 18px; }
.sub-line { margin-top: 2px; color: #8ea3be; font-size: 11px; }
.top-kpis { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 6px; }
.kpi-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px; }
.kpi-label { font-size: 11px; color: #91a4be; display:block; }
.kpi-value { display:block; font-size: 16px; line-height:1.2; margin-top: 1px; }
.kpi-unit { color:#8ea3be; font-size:11px; }
.quick-actions { display:grid; grid-template-columns: 1fr; gap:6px; }
.action-btn { height: 28px; border: 1px solid #31445d; background: #132236; color: #dbe4f0; border-radius: 6px; cursor:pointer; font-size: 12px; }
.action-btn.primary { background:#114a62; border-color:#1a6b8d; }
.action-btn.danger { background:#4a1f2b; border-color:#6f2e3f; }

.content-grid {
  min-height: 0;
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr) 340px;
  gap: 8px;
}

.left-panel, .right-panel { padding: 10px; overflow: hidden; }
.center-panel { position: relative; min-height: 0; overflow: hidden; border-radius: 10px; }

.tab-header { display:flex; gap:6px; margin-bottom: 10px; }
.tab-btn { flex:1; height:34px; border:none; border-radius:6px; background:#132132; color:#9ab0c7; cursor:pointer; }
.tab-btn.active { background:#1d3950; color:#fff; }
.tab-body { overflow:auto; height: calc(100% - 44px); display:flex; flex-direction:column; gap:8px; }

.list-item {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-left: 3px solid #3b82f6;
  border-radius: 8px;
  padding: 8px 10px;
}
.list-item.level-danger { border-left-color:#ef4444; }
.list-item.level-warning { border-left-color:#f59e0b; }
.list-item.pending { border-left-color:#22c55e; }
.list-item.selected { outline: 1px solid #00d7ff; }
.item-head { display:flex; justify-content:space-between; gap:8px; }
.item-head strong { font-size: 13px; }
.item-tag { font-size:11px; color:#91a4be; }
.item-sub { margin-top:4px; font-size:11px; color:#8ea3be; }
.item-desc { margin-top:6px; font-size:12px; color:#cbd8e8; line-height:1.4; }
.item-actions { margin-top:8px; display:flex; gap:6px; }
.item-actions button { height:28px; border:none; border-radius:6px; padding:0 10px; background:#1a2a40; color:#dbe4f0; cursor:pointer; }

.map-toolbar {
  position:absolute;
  top: 10px;
  left: 10px;
  display:flex;
  gap: 6px;
  padding: 6px;
  z-index: 12;
}
.mini-btn {
  height: 30px;
  padding: 0 10px;
  border: 1px solid #31445d;
  background: #132236;
  color: #dbe4f0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.detail-header { display:flex; justify-content:space-between; align-items:center; }
.detail-header h2 { margin:0; font-size:16px; }
.context-badge { font-size: 12px; color:#8ea3be; }
.empty-state { margin-top: 12px; font-size: 13px; color:#94a6bd; line-height:1.6; }
.detail-section { margin-top: 12px; padding-top: 12px; border-top: 1px dashed rgba(255,255,255,0.12); }
.detail-title { font-size: 13px; font-weight: 700; margin-bottom: 8px; }
.detail-grid { display:grid; grid-template-columns: 1fr 1fr; gap:8px; }
.kv { background: rgba(255,255,255,0.03); border-radius: 6px; padding: 10px; }
.kv span { display:block; font-size:11px; color:#8ea3be; }
.kv strong { display:block; margin-top:4px; font-size:13px; }
.detail-text { font-size:12px; color:#cbd8e8; line-height:1.6; }
.detail-actions { display:grid; grid-template-columns: 1fr 1fr; gap:8px; }

.timeline-panel { padding: 8px 10px; overflow: hidden; }
.timeline-head { display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px; }
.timeline-head h2 { margin:0; font-size: 15px; }
.timeline-head span { font-size:12px; color:#8ea3be; }
.timeline-list { display:flex; flex-direction:column; gap:8px; overflow:auto; height: calc(100% - 28px); }
.timeline-item {
  min-height: 40px;
  display:grid;
  grid-template-columns: 70px 1fr 80px;
  gap:10px;
  align-items:center;
  background: rgba(255,255,255,0.03);
  border:1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  padding: 8px 10px;
}
.timeline-time, .timeline-meta { font-size:12px; color:#8ea3be; }
.timeline-body strong { display:block; font-size:13px; }
.timeline-body div { font-size:12px; color:#c8d6e8; margin-top:2px; }

.danger-text { color:#ef4444; }

@media (max-width: 1400px) {
  .top-bar { grid-template-columns: 220px 1fr 280px; }
  .top-kpis { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .content-grid { grid-template-columns: 300px minmax(0, 1fr) 300px; }
}
</style>

<template>
  <div class="product-page">
    <header class="top-bar">
      <div>
        <h1>生产调度处置台</h1>
        <div class="sub">使用方式：左侧选案件 → 中间看详情 → 右侧执行动作</div>
      </div>
      <div class="top-kpis">
        <div class="kpi"><span>待处理案件</span><strong>{{ casePool.length }}</strong></div>
        <div class="kpi"><span>执行中任务</span><strong>{{ store.displayTasks.length }}</strong></div>
        <div class="kpi"><span>高风险区域</span><strong>{{ riskZoneCount }}</strong></div>
        <div class="kpi"><span>今日产量</span><strong>{{ store.kpi.total_tonnage || 0 }} 吨</strong></div>
      </div>
    </header>

    <section class="main-grid">
      <aside class="panel left-panel">
        <div class="panel-title">1. 待处理案件</div>
        <div class="case-list">
          <div
            v-for="item in casePool"
            :key="item.id"
            class="case-card"
            :class="['priority-' + item.priority, { active: selectedCase.id === item.id }]"
            @click="selectCase(item)"
          >
            <div class="case-with-thumb">
              <img :src="item.image" class="case-thumb" alt="案件缩略图" />
              <div class="case-main">
                <div class="case-title-row">
                  <strong>{{ item.title }}</strong>
                  <span class="priority-badge">{{ priorityLabel(item.priority) }}</span>
                </div>
                <div class="case-meta">{{ item.zone }} · {{ item.time }}</div>
                <div class="case-status">{{ item.status }}</div>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <main class="panel center-panel">
        <div class="panel-title">2. 当前案件详情</div>
        <div class="detail-hero" :class="'priority-' + selectedCase.priority">
          <div class="hero-line"><span>案件名称</span><strong>{{ selectedCase.title }}</strong></div>
          <div class="hero-line"><span>区域</span><strong>{{ selectedCase.zone }}</strong></div>
          <div class="hero-line"><span>来源</span><strong>{{ selectedCase.source }}</strong></div>
          <div class="hero-line"><span>当前状态</span><strong>{{ selectedCase.status }}</strong></div>
        </div>

        <div class="detail-section">
          <div class="detail-label">现场证据图像</div>
          <div class="evidence-image-box" @click="previewImage = selectedCase.image">
            <img :src="selectedCase.image" class="evidence-image" alt="案件证据图" />
            <div class="image-tip">点击查看大图</div>
          </div>
        </div>

        <div class="detail-section">
          <div class="detail-label">问题描述</div>
          <div class="detail-text">{{ selectedCase.message }}</div>
        </div>

        <div class="detail-section">
          <div class="detail-label">证据摘要</div>
          <div class="detail-text">{{ selectedCase.evidence }}</div>
        </div>

        <div class="detail-section">
          <div class="detail-label">建议处置</div>
          <ol class="plan-list">
            <li v-for="step in selectedCase.plan" :key="step">{{ step }}</li>
          </ol>
        </div>
      </main>

      <aside class="panel right-panel">
        <div class="panel-title">3. 执行动作</div>
        <div class="action-note">先点一个动作，底部流水会立即记录结果。</div>
        <div class="action-stack">
          <button class="btn primary" @click="takeOverCurrent">接管案件</button>
          <button class="btn" @click="dispatchCurrent">生成调度任务</button>
          <button class="btn danger" @click="closeCurrent">关闭事件</button>
        </div>

        <div class="result-box">
          <div class="detail-label">执行后果</div>
          <div class="detail-text">{{ actionHint }}</div>
        </div>
      </aside>
    </section>

    <footer class="panel bottom-panel">
      <div class="panel-title">4. 处置流水</div>
      <div class="timeline-list">
        <div class="timeline-item" v-for="event in timeline" :key="event.id">
          <span class="time">{{ event.time }}</span>
          <div class="body">
            <strong>{{ event.action }}</strong>
            <div>{{ event.target }}</div>
          </div>
          <span class="operator">{{ event.operator }}</span>
        </div>
      </div>
    </footer>

    <div v-if="previewImage" class="image-modal" @click="previewImage = ''">
      <img :src="previewImage" class="image-modal-content" alt="预览大图" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { useOperationsStore } from '../../store/operations'

const store = useOperationsStore()
let timer = null
let seq = 1000
const previewImage = ref('')

const makeEvidenceSvg = (title, sub, color) => `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
  <svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450">
    <defs>
      <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
        <stop offset="0%" stop-color="#0f172a"/>
        <stop offset="100%" stop-color="#111827"/>
      </linearGradient>
    </defs>
    <rect width="800" height="450" fill="url(#g)"/>
    <rect x="24" y="24" width="752" height="402" rx="16" fill="none" stroke="${color}" stroke-width="3"/>
    <rect x="46" y="52" width="220" height="32" rx="8" fill="${color}" fill-opacity="0.16"/>
    <text x="58" y="74" font-size="22" fill="#e5eefb" font-family="Arial, sans-serif">${title}</text>
    <text x="58" y="116" font-size="16" fill="#9fb3c8" font-family="Arial, sans-serif">${sub}</text>
    <rect x="110" y="170" width="180" height="96" rx="10" fill="none" stroke="${color}" stroke-width="3"/>
    <rect x="360" y="130" width="280" height="160" rx="12" fill="none" stroke="#e5eefb" stroke-opacity="0.6" stroke-width="2"/>
    <circle cx="430" cy="182" r="20" fill="none" stroke="#ef4444" stroke-width="4"/>
    <circle cx="520" cy="216" r="26" fill="none" stroke="#f59e0b" stroke-width="4"/>
    <circle cx="592" cy="168" r="16" fill="none" stroke="#22c55e" stroke-width="4"/>
    <text x="360" y="322" font-size="16" fill="#dbe4f0" font-family="Arial, sans-serif">现场证据图 / 事件关联图像</text>
  </svg>
`)}`

const casePool = ref([
  {
    id: 'CASE-001',
    title: '边坡裂缝异常',
    zone: 'SLOPE-ZONE-A',
    time: '01:08',
    source: '裂缝识别模型',
    priority: 'critical',
    status: '待处理',
    message: '裂缝宽度持续上升，建议立即发起复核并限制该区域作业。',
    evidence: '视觉识别检出 3 处裂缝，最大宽度上升；相关区域存在持续风险暴露。',
    image: '/demo-evidence/crack-evidence.png',
    plan: ['接管案件', '确认风险等级', '生成调度任务或转人工巡检']
  },
  {
    id: 'CASE-002',
    title: '运输卡口拥堵',
    zone: '主运输线',
    time: '01:05',
    source: '调度监控',
    priority: 'high',
    status: '处理中',
    message: '矿卡等待时长超过阈值，已影响当前班次运输效率。',
    evidence: '主运输线排队车辆增多，等待时间上升，当前调度链路负载偏高。',
    image: '/demo-evidence/traffic-evidence.png',
    plan: ['调整车辆流向', '重排运输任务', '观察拥堵缓解结果']
  },
  {
    id: 'CASE-003',
    title: '风速波动升高',
    zone: '西侧作业区',
    time: '01:02',
    source: '环境感知',
    priority: 'medium',
    status: '待确认',
    message: '风速接近飞行受限阈值，需确认无人机任务是否继续。',
    evidence: '风速抬升，当前能见度正常，但飞行条件存在进一步恶化风险。',
    image: '/demo-evidence/weather-evidence.png',
    plan: ['确认环境阈值', '保留人工巡检预案', '必要时暂停飞行任务']
  }
])

const selectedCase = ref(casePool.value[0])
const timeline = ref([
  { id: 1, time: '01:00', action: '系统告警', target: '边坡裂缝异常', operator: '系统' },
  { id: 2, time: '01:03', action: '任务下发', target: '矿卡调度 #1024', operator: '调度员' },
])
const actionHint = ref('接管后，案件状态会切换为“人工处理中”。')

const riskZoneCount = computed(() => new Set(casePool.value.map(i => i.zone)).size)

const priorityLabel = (p) => ({ critical: '高危', high: '重要', medium: '一般' }[p] || '一般')
const selectCase = (item) => {
  selectedCase.value = item
  actionHint.value = '请选择右侧动作之一，推进该案件进入下一步。'
}
const appendTimeline = (action, target, operator = '调度员') => {
  const d = new Date()
  timeline.value.unshift({ id: ++seq, time: d.toTimeString().slice(0, 5), action, target, operator })
}
const takeOverCurrent = () => {
  selectedCase.value.status = '人工处理中'
  actionHint.value = '案件已进入人工处理流程，下一步建议生成调度任务。'
  appendTimeline('接管案件', selectedCase.value.title)
}
const dispatchCurrent = () => {
  selectedCase.value.status = '已派单'
  actionHint.value = '已生成调度任务，接下来应跟踪执行回执。'
  appendTimeline('生成调度任务', selectedCase.value.title)
}
const closeCurrent = () => {
  selectedCase.value.status = '已闭环'
  actionHint.value = '案件已关闭，如需复盘可查看底部处置流水。'
  appendTimeline('关闭事件', selectedCase.value.title)
}

onMounted(() => {
  store.fetchAllData()
  timer = setInterval(() => store.fetchAllData(), 10000)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.product-page { min-height: 100vh; background: #0b1220; color: #dbe4f0; padding: 12px; display:flex; flex-direction:column; gap:10px; }
.top-bar, .panel, .kpi { background:#111b2f; border:1px solid #25344d; border-radius:10px; }
.top-bar { display:grid; grid-template-columns: 1fr 520px; gap:10px; align-items:center; padding:12px; }
h1 { margin:0; font-size:22px; }
.sub { margin-top:4px; color:#8ea3be; font-size:12px; }
.top-kpis { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:8px; }
.kpi { padding:8px; }
.kpi span { display:block; font-size:12px; color:#8ea3be; }
.kpi strong { display:block; margin-top:2px; font-size:18px; }
.main-grid { display:grid; grid-template-columns: 300px minmax(0,1fr) 260px; gap:10px; flex:1; min-height:0; }
.left-panel, .center-panel, .right-panel, .bottom-panel { padding:12px; min-height:0; overflow:hidden; }
.panel-title { font-size:16px; font-weight:700; margin-bottom:10px; }
.case-list, .timeline-list { display:flex; flex-direction:column; gap:8px; overflow:auto; height: calc(100% - 28px); }
.case-card { background:#0f1a2c; border:1px solid #22344c; border-left:4px solid #3b82f6; border-radius:10px; padding:10px; cursor:pointer; }
.case-with-thumb { display:grid; grid-template-columns: 64px 1fr; gap:10px; align-items:center; }
.case-thumb { width:64px; height:64px; object-fit:cover; border-radius:8px; border:1px solid rgba(255,255,255,.08); }
.case-main { min-width:0; }
.case-card.active { outline:1px solid #00d7ff; }
.case-card.priority-critical { border-left-color:#ef4444; }
.case-card.priority-high { border-left-color:#f59e0b; }
.case-card.priority-medium { border-left-color:#22c55e; }
.case-title-row { display:flex; justify-content:space-between; gap:8px; }
.case-title-row strong { font-size:14px; }
.priority-badge, .case-meta, .case-status { font-size:11px; color:#8ea3be; }
.case-meta { margin-top:4px; }
.case-status { margin-top:8px; }
.detail-hero { border-radius:10px; padding:12px; margin-bottom:10px; border:1px solid rgba(255,255,255,.08); }
.detail-hero.priority-critical { background:rgba(127,29,29,.22); }
.detail-hero.priority-high { background:rgba(120,53,15,.22); }
.detail-hero.priority-medium { background:rgba(20,83,45,.22); }
.hero-line { display:flex; justify-content:space-between; gap:10px; padding:6px 0; border-bottom:1px dashed rgba(255,255,255,.08); }
.hero-line:last-child { border-bottom:none; }
.hero-line span { color:#8ea3be; font-size:12px; }
.hero-line strong { font-size:14px; }
.detail-section { margin-top:12px; }
.evidence-image-box { position:relative; border-radius:10px; overflow:hidden; border:1px solid #22344c; background:#0f1a2c; cursor:pointer; }
.evidence-image { width:100%; height:240px; object-fit:cover; display:block; }
.image-tip { position:absolute; right:10px; bottom:10px; background:rgba(0,0,0,.55); color:#fff; font-size:12px; padding:4px 8px; border-radius:6px; }
.image-modal { position:fixed; inset:0; background:rgba(0,0,0,.7); display:flex; align-items:center; justify-content:center; z-index:9999; }
.image-modal-content { max-width:90vw; max-height:88vh; border-radius:12px; border:1px solid rgba(255,255,255,.12); box-shadow:0 10px 30px rgba(0,0,0,.45); }
.detail-label { font-size:13px; color:#8ea3be; margin-bottom:6px; }
.detail-text { font-size:13px; line-height:1.6; color:#dbe4f0; }
.plan-list { margin:0; padding-left:18px; line-height:1.8; font-size:13px; }
.action-note { color:#9ab0c7; font-size:13px; line-height:1.6; margin-bottom:12px; }
.action-stack { display:grid; gap:8px; }
.btn { height:36px; padding:0 12px; border:none; border-radius:6px; background:#1a2a40; color:#dbe4f0; cursor:pointer; }
.btn.primary { background:#114a62; } .btn.danger { background:#5b2331; }
.result-box { margin-top:16px; padding-top:12px; border-top:1px dashed rgba(255,255,255,.12); }
.bottom-panel { min-height: 180px; }
.timeline-item { display:grid; grid-template-columns: 56px 1fr 56px; gap:8px; align-items:center; background:#0f1a2c; border:1px solid #22344c; border-radius:8px; padding:8px 10px; }
.timeline-item .time, .timeline-item .operator { color:#8ea3be; font-size:11px; }
.timeline-item .body strong { display:block; font-size:13px; }
.timeline-item .body div { margin-top:2px; font-size:12px; color:#cbd7e7; }
</style>

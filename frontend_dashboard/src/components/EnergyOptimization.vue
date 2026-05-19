<template>
  <div class="energy-page">
    <section class="hero">
      <div>
        <div class="eyebrow">ENERGY OPTIMIZATION</div>
        <h1>能源优化中心</h1>
        <p>聚焦电耗、燃油、设备分组和规则触发，把节能建议做成真实可执行的调度台。</p>
      </div>

      <div class="hero-stats">
        <div v-for="card in statCards" :key="card.label" class="stat-card">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
          <small>{{ card.hint }}</small>
        </div>
      </div>
    </section>

    <section class="grid">
      <article class="panel chart-panel">
        <div class="panel-head">
          <div>
            <h2>能耗分项图</h2>
            <p>电耗 / 燃油 / 峰值负荷 / 空转损耗</p>
          </div>
          <div class="pill">实时监测</div>
        </div>

        <div class="split-chart">
          <div class="donut-card">
            <div class="donut-core">
              <strong>{{ energyScore }}</strong>
              <span>节能评分</span>
            </div>
          </div>
          <div class="breakdown-list">
            <div class="breakdown-item" v-for="item in breakdown" :key="item.label">
              <div class="breakdown-top">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
              <div class="bar-track"><div class="bar-fill animated" :style="{ width: item.percent + '%', background: item.color }"></div></div>
            </div>
          </div>
        </div>

        <div class="trend-panel">
          <div class="trend-head">
            <h3>趋势窗口</h3>
            <div class="trend-badges">
              <span>峰值 {{ energyBreakdown.peakLoad }}%</span>
              <span>单耗 {{ energyMetrics.kwhPerTon }} kWh/t</span>
            </div>
          </div>
          <div class="trend-bars">
            <div class="trend-bar" v-for="point in trendSeries" :key="point.label">
              <span>{{ point.label }}</span>
              <div class="trend-track"><div class="trend-fill animated" :style="{ height: point.value + '%' }"></div></div>
            </div>
          </div>
        </div>
      </article>

      <article class="panel device-panel">
        <div class="panel-head">
          <div>
            <h2>设备分组卡</h2>
            <p>按系统分组查看节能潜力</p>
          </div>
          <div class="pill success">已接入规则</div>
        </div>

        <div class="device-grid">
          <div
            v-for="group in deviceGroups"
            :key="group.name"
            class="device-card"
            :class="{ active: selectedGroup.name === group.name }"
            @click="selectedGroupIndex = deviceGroups.findIndex(g => g.name === group.name)"
          >
            <div class="device-top">
              <strong>{{ group.name }}</strong>
              <span>{{ group.saving }}</span>
            </div>
            <div class="device-load">
              <div class="device-load-bar"><div class="device-load-fill animated" :style="{ width: group.load + '%' }"></div></div>
              <b>{{ group.load }}%</b>
            </div>
            <small>{{ group.status }}</small>
          </div>
        </div>

        <div class="device-detail">
          <div class="panel-head compact">
            <div>
              <h3>当前选中</h3>
              <p>{{ selectedGroup.name }} · {{ selectedGroup.status }}</p>
            </div>
          </div>
          <p>该分组当前负荷 {{ selectedGroup.load }}%，建议节能收益约 {{ selectedGroup.saving }}，适合与调度系统联动。</p>
        </div>
      </article>

      <article class="panel rule-panel">
        <div class="panel-head">
          <div>
            <h2>规则触发引擎</h2>
            <p>基于生产/识别条件自动触发动作</p>
          </div>
          <div class="pill danger">动态触发</div>
        </div>

        <div class="rule-list">
          <div
            v-for="rule in rules"
            :key="rule.id"
            class="rule-item"
            :class="[{ active: selectedRule.id === rule.id }, 'level-' + rule.level]"
            @click="selectedRuleIndex = rules.findIndex(r => r.id === rule.id)"
          >
            <div class="rule-head">
              <strong>{{ rule.id }}</strong>
              <span>{{ rule.level }}</span>
            </div>
            <p>{{ rule.when }}</p>
            <small>触发后：{{ rule.then }}</small>
          </div>
        </div>

        <div class="trigger-box">
          <div class="trigger-head">
            <span>当前触发</span>
            <strong>{{ selectedRule.id }}</strong>
          </div>
          <p>{{ selectedRule.when }}</p>
          <div class="trigger-action">{{ selectedRule.then }}</div>
          <button class="trigger-btn" @click="fireRule">模拟触发规则</button>
        </div>
      </article>
    </section>

    <section class="panel footer-panel">
      <div class="panel-head">
        <div>
          <h2>节能流水</h2>
          <p>策略执行、规则触发与联动结果</p>
        </div>
      </div>
      <div class="timeline">
        <div class="timeline-item" v-for="item in timeline" :key="item.id">
          <span>{{ item.time }}</span>
          <strong>{{ item.action }}</strong>
          <small>{{ item.target }}</small>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { useOperationsStore } from '../store/operations'
import { API_ENDPOINTS } from '../config/api'

const store = useOperationsStore()
const API_BIZ_BASE = API_ENDPOINTS.biz

const energyMetrics = ref({ shiftEnergy: 2860, energyDelta: 6.8, kwhPerTon: '2.71', targetKwhPerTon: 2.4, idleVehicles: 2, projectedSavings: 12.5, energyScore: 84 })
const energyBreakdown = ref({ electricity: 1080, fuel: 2250, peakLoad: 68, idleLoss: 24, unitCost: 4.71 })
const selectedGroupIndex = ref(0)
const selectedRuleIndex = ref(0)
const timeline = ref([
  { id: 1, time: '01:04', action: '识别能耗异常', target: '主运输线空转率升高' },
  { id: 2, time: '01:09', action: '生成节能建议', target: '建议切换两台矿卡至侧线' },
  { id: 3, time: '01:12', action: '策略待下发', target: '等待值班长确认' },
])

const statCards = computed(() => ([
  { label: '班次总能耗', value: energyMetrics.value.shiftEnergy, hint: 'kWh 估算' },
  { label: '电耗占比', value: `${Math.round(energyBreakdown.value.electricity / (energyBreakdown.value.electricity + energyBreakdown.value.fuel) * 100)}%`, hint: '电力消耗' },
  { label: '燃油消耗', value: energyBreakdown.value.fuel, hint: 'L' },
  { label: '预估节省', value: `${energyMetrics.value.projectedSavings}%`, hint: '动态策略收益' },
]))

const breakdown = computed(() => ([
  { label: '电耗', value: `${energyBreakdown.value.electricity} kWh`, percent: Math.min(100, Math.round(energyBreakdown.value.electricity / 20)), color: 'linear-gradient(90deg,#38bdf8,#22d3ee)' },
  { label: '燃油', value: `${energyBreakdown.value.fuel} L`, percent: Math.min(100, Math.round(energyBreakdown.value.fuel / 30)), color: 'linear-gradient(90deg,#f59e0b,#fbbf24)' },
  { label: '峰值负荷', value: `${energyBreakdown.value.peakLoad}%`, percent: energyBreakdown.value.peakLoad, color: 'linear-gradient(90deg,#22c55e,#4ade80)' },
  { label: '空转损耗', value: `${energyBreakdown.value.idleLoss}%`, percent: energyBreakdown.value.idleLoss, color: 'linear-gradient(90deg,#ef4444,#fb7185)' },
]))

const energyScore = computed(() => energyMetrics.value.energyScore)
const deviceGroups = ref([
  { name: '运输车队', load: 58, status: '运行中', saving: '2.8%' },
  { name: '破碎站', load: 81, status: '高负荷', saving: '5.2%' },
  { name: '巡检链路', load: 34, status: '节能模式', saving: '3.4%' },
  { name: '供配电节点', load: 46, status: '平稳', saving: '1.6%' },
])
const rules = ref([
  { id: 'RULE-01', when: '运输空载率 > 35%', then: '下调车队巡航速度并重排装载顺序', level: 'high' },
  { id: 'RULE-02', when: '破碎站峰值负荷 > 70%', then: '切换到低谷排程窗口', level: 'medium' },
  { id: 'RULE-03', when: '智能识别告警升高', then: '自动提升巡检频率并保留高风险点位实时上报', level: 'critical' },
])
const trendSeries = ref([
  { label: '00:00', value: 40 }, { label: '00:10', value: 47 }, { label: '00:20', value: 54 }, { label: '00:30', value: 68 }, { label: '00:40', value: 72 }, { label: '00:50', value: 61 },
])

const selectedGroupIdx = ref(0)
const selectedRuleIdx = ref(0)
let ticker = null

const selectedGroup = computed(() => deviceGroups.value[selectedGroupIndex.value] || deviceGroups.value[0])
const selectedRule = computed(() => rules.value[selectedRuleIndex.value] || rules.value[0])

const fireRule = () => {
  const now = new Date().toTimeString().slice(0, 5)
  timeline.value.unshift({ id: Date.now(), time: now, action: `触发 ${selectedRule.value.id}`, target: selectedRule.value.then })
}

const loadEnergyData = async () => {
  try {
    const res = await axios.get(`${API_BIZ_BASE}/ops/energy-optimization`)
    const data = res.data || {}
    if (data.energyMetrics) energyMetrics.value = { ...energyMetrics.value, ...data.energyMetrics }
    if (data.energyBreakdown) energyBreakdown.value = { ...energyBreakdown.value, ...data.energyBreakdown }
    if (Array.isArray(data.deviceGroups) && data.deviceGroups.length) deviceGroups.value = data.deviceGroups
    if (Array.isArray(data.rules) && data.rules.length) rules.value = data.rules
    if (Array.isArray(data.trendSeries) && data.trendSeries.length) trendSeries.value = data.trendSeries
    if (Array.isArray(data.timeline) && data.timeline.length) timeline.value = data.timeline
  } catch (err) {
    console.warn('Energy optimization API unavailable, using fallback UI.', err)
  }
}

onMounted(() => {
  store.fetchAllData()
  loadEnergyData()
  ticker = setInterval(() => {
    selectedGroupIdx.value = (selectedGroupIdx.value + 1) % deviceGroups.value.length
    selectedRuleIdx.value = (selectedRuleIdx.value + 1) % rules.value.length
    selectedGroupIndex.value = selectedGroupIdx.value
    selectedRuleIndex.value = selectedRuleIdx.value
    fireRule()
  }, 5000)
})
</script>

<style scoped>
.energy-page { min-height: 100vh; padding: 76px 16px 16px; background: linear-gradient(180deg,#07101b 0%,#091525 45%,#07111d 100%); color:#e8f0ff; box-sizing:border-box; }
.hero { display:flex; justify-content:space-between; gap:16px; padding:20px; border-radius:18px; background:rgba(10,23,39,.92); border:1px solid rgba(64,129,192,.28); margin-bottom:12px; }
.eyebrow { color:#56c7ff; font-size:11px; letter-spacing:2px; margin-bottom:6px; }
h1 { margin:0; font-size:32px; }
.hero p { margin:10px 0 0; color:#8fb4d9; }
.hero-stats { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; min-width: 520px; }
.stat-card { padding:14px; border-radius:16px; background:rgba(12,39,63,.72); border:1px solid rgba(110,177,255,.12); }
.stat-card span, .stat-card small { display:block; color:#8fb4d9; font-size:11px; }
.stat-card strong { display:block; margin:8px 0; font-size:28px; }
.grid { display:grid; grid-template-columns: 1.15fr .95fr .9fr; gap:12px; align-items:stretch; }
.panel { padding:16px; border-radius:18px; background:rgba(10,23,39,.92); border:1px solid rgba(64,129,192,.28); }
.panel-head { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:14px; }
.panel-head h2, .panel-head h3 { margin:0; }
.panel-head p { margin:6px 0 0; color:#8fb4d9; font-size:12px; }
.pill { padding:4px 10px; border-radius:999px; font-size:11px; border:1px solid rgba(120,187,255,.24); background:rgba(24,58,89,.55); white-space:nowrap; }
.pill.success { color:#6ff2a8; border-color:rgba(34,197,94,.32); }
.pill.danger { color:#ff9b9b; border-color:rgba(239,68,68,.32); }
.split-chart { display:grid; grid-template-columns: .9fr 1.1fr; gap:12px; align-items:center; }
.donut-card, .device-card, .device-detail, .rule-item, .trigger-box { border-radius:16px; background:rgba(10, 24, 39, 0.86); border:1px solid rgba(110,177,255,.12); }
.donut-card { display:flex; align-items:center; justify-content:center; padding:8px 0; min-height:220px; }
.donut-core { width:160px; height:160px; border-radius:50%; display:flex; flex-direction:column; align-items:center; justify-content:center; background:radial-gradient(circle at center, rgba(34,211,238,.18) 0 42%, rgba(8,21,35,.95) 43% 100%); border:1px solid rgba(85,206,255,.4); box-shadow: inset 0 0 40px rgba(34,211,238,.12); }
.donut-core strong { font-size:34px; }
.donut-core span { color:#8fb4d9; font-size:12px; }
.breakdown-list { display:flex; flex-direction:column; gap:10px; }
.breakdown-item { padding:12px; border-radius:14px; background:rgba(10, 23, 38, 0.78); }
.breakdown-top { display:flex; justify-content:space-between; align-items:baseline; gap:8px; }
.breakdown-top span { color:#8fb4d9; font-size:11px; }
.breakdown-top strong { font-size:14px; }
.bar-track { height:10px; border-radius:999px; background:rgba(255,255,255,.07); overflow:hidden; margin-top:8px; }
.bar-fill { height:100%; border-radius:inherit; }
.trend-panel { margin-top:12px; padding:12px; border-radius:16px; background:rgba(8,21,35,.7); border:1px solid rgba(110,177,255,.12); }
.trend-head { display:flex; justify-content:space-between; gap:10px; align-items:center; }
.trend-head h3 { margin:0; font-size:14px; }
.trend-badges { display:flex; gap:8px; flex-wrap:wrap; }
.trend-badges span { font-size:11px; color:#8fb4d9; padding:4px 8px; border-radius:999px; background:rgba(24,58,89,.45); }
.trend-bars { display:grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap:8px; align-items:end; margin-top:12px; min-height:150px; }
.trend-bar { display:flex; flex-direction:column; align-items:center; gap:8px; height:100%; }
.trend-bar span { font-size:11px; color:#8fb4d9; }
.trend-track { width:100%; height:100px; display:flex; align-items:flex-end; border-radius:12px; background:rgba(255,255,255,.03); overflow:hidden; border:1px solid rgba(110,177,255,.08); }
.trend-fill { width:100%; border-radius:12px 12px 0 0; background:linear-gradient(180deg,#22d3ee,#38bdf8); }
.device-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.device-card { padding:12px; cursor:pointer; transition: transform .2s ease, border-color .2s ease; }
.device-card.active { border-color: rgba(85,206,255,.65); box-shadow: inset 0 0 0 1px rgba(85,206,255,.18); }
.device-top { display:flex; justify-content:space-between; gap:10px; align-items:baseline; }
.device-load { margin-top:10px; display:flex; align-items:center; gap:8px; }
.device-load-bar { flex:1; height:8px; border-radius:999px; overflow:hidden; background:rgba(255,255,255,.07); }
.device-load-fill { height:100%; border-radius:inherit; background:linear-gradient(90deg,#38bdf8,#22d3ee); }
.device-detail { margin-top:12px; padding:12px; }
.rule-list { display:flex; flex-direction:column; gap:10px; }
.rule-item { padding:12px; cursor:pointer; }
.rule-item.active { border-color: rgba(85,206,255,.65); box-shadow: inset 0 0 0 1px rgba(85,206,255,.18); }
.rule-head { display:flex; justify-content:space-between; gap:8px; align-items:baseline; }
.rule-item p, .rule-item small, .device-detail p, .timeline-item span, .timeline-item small { color:#8fb4d9; font-size:11px; }
.rule-item small { display:block; margin-top:6px; line-height:1.5; }
.level-critical { border-left:4px solid #ef4444; }
.level-high { border-left:4px solid #f59e0b; }
.level-medium { border-left:4px solid #22c55e; }
.trigger-box { margin-top:12px; padding:12px; }
.trigger-head { display:flex; justify-content:space-between; gap:10px; align-items:center; }
.trigger-action { margin:10px 0; padding:10px 12px; border-radius:12px; background:rgba(16,61,62,.3); border:1px solid rgba(34,197,94,.14); }
.trigger-btn { width:100%; height:42px; border:none; border-radius:12px; background:linear-gradient(180deg, rgba(23,46,72,.95), rgba(16,31,48,.95)); color:#eaf3ff; font-weight:600; cursor:pointer; }
.timeline { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
.timeline-item { padding:12px; border-radius:14px; background:rgba(10,23,38,.88); border:1px solid rgba(110,177,255,.1); }
.timeline-item strong { display:block; margin:7px 0 5px; font-size:14px; }
.timeline-item span, .timeline-item small { display:block; }
.animated { animation: glowPulse 2.8s ease-in-out infinite; }
@keyframes glowPulse { 0%,100% { filter: brightness(1); transform: translateY(0); } 50% { filter: brightness(1.14); transform: translateY(-1px); } }
@media (max-width: 1600px) { .hero { flex-direction:column; } .hero-stats { min-width:0; grid-template-columns:repeat(2,minmax(0,1fr)); } .grid { grid-template-columns:1fr; } .timeline { grid-template-columns:1fr; } }
</style>

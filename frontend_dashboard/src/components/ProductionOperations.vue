<template>
  <div class="production-ops-container">
    <!-- 0. Dynamic Background Effects Layer -->
    <div class="background-vfx">
      <div class="scanning-radar-line"></div>
      <div class="grid-layer"></div>
      <div class="vignette-layer"></div>
    </div>

    <!-- 1. Immersive Map Layer -->
    <div class="map-immersive-background">
      <div class="map-content">
        <!-- Vehicle OSD Markers -->
        <div 
          v-for="v in displayFleet" 
          :key="v.device_id"
          class="vehicle-hud-marker"
          :style="getPositionStyle(v.location)"
        >
          <div class="marker-base">
            <div class="pulse-ring"></div>
            <div class="ground-target"></div>
          </div>
          <div class="hud-lead-line"></div>
          <div class="hud-tag premium-tag">
            <div class="tag-header">
              <span class="v-id">{{ v.device_name }}</span>
              <span class="status-dot green"></span>
            </div>
            <div class="tag-body">
              <div class="data-group">
                <span class="label">VEL</span>
                <span class="val">{{ v.telemetry.speed }}<small>KM/H</small></span>
              </div>
              <div class="data-group">
                <span class="label">ALT</span>
                <span class="val">420<small>M</small></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Major Site Hotspots -->
        <div class="site-hotspot" style="left: 20%; top: 30%;">
          <div class="hotspot-cross"></div>
          <span class="hotspot-label">PIT FLOOR -420M</span>
        </div>
        <div class="site-hotspot" style="left: 78%; top: 62%;">
          <div class="hotspot-cross"></div>
          <span class="hotspot-label">PRIMARY CRUSHER #02</span>
        </div>
      </div>
    </div>

    <!-- 2. Top HUD: Mission Critical KPIs -->
    <header class="ops-hud-header glass-hud">
      <div class="hud-header-left">
        <div class="system-title">
          <h1 class="glow-text-blue">PRODUCTION INTEL <span>V2.4</span></h1>
          <div class="system-status-bar">
            <span class="status-node">SAT-LINK: OK</span>
            <span class="status-node">ENGINE: LIVE</span>
            <span class="status-node alert">LATENCY: 42MS</span>
          </div>
        </div>
      </div>

      <div class="hud-kpi-row">
        <div class="kpi-block" v-for="(val, label) in kpiSummary" :key="label">
          <div class="kpi-label-box">
            <span class="kpi-label">{{ label }}</span>
            <span class="kpi-trend">▲ 2.1%</span>
          </div>
          <div class="kpi-value-box">
            <span class="kpi-value glow-number">{{ val }}</span>
            <div class="kpi-mini-gauge"><div class="fill" :style="{ width: '75%' }"></div></div>
          </div>
        </div>
      </div>

      <div class="hud-clock-box">
        <div class="time-main">{{ currentTime }}</div>
        <div class="date-sub">{{ currentDate }} ({{ countdown }}S)</div>
      </div>
    </header>

    <!-- 3. Left HUD: Production Intelligence & Analytics -->
    <aside class="ops-hud-left glass-hud side-panel-premium">
      <div class="panel-header-bracket">
        <span class="panel-title-text">REALTIME PRODUCTION YIELD</span>
        <div class="panel-id">REF: PRD-004</div>
      </div>
      <div class="panel-inner">
        <div class="chart-box-enhanced" ref="trendChartRef"></div>
      </div>

      <div class="panel-header-bracket sub-header">
        <span class="panel-title-text">EQUIPMENT OEE RANKING</span>
      </div>
      <div class="panel-inner ranking-list">
        <div class="rank-item" v-for="(item, idx) in displayLeaderboard" :key="item.vehicle_id">
          <div class="rank-index">0{{ idx + 1 }}</div>
          <div class="rank-info">
            <div class="rank-meta">
              <span class="rank-name">{{ item.vehicle_id }}</span>
              <span class="rank-percent">{{ (item.total_tonnage / 12).toFixed(1) }}%</span>
            </div>
            <div class="rank-progress">
              <div class="rank-fill" :style="{ width: (item.total_tonnage / 1200 * 100) + '%' }"></div>
            </div>
          </div>
          <div class="rank-val">{{ item.total_tonnage }}T</div>
        </div>
      </div>
    </aside>

    <!-- 4. Right HUD: Dispatch Queue & Environment -->
    <aside class="ops-hud-right glass-hud side-panel-premium">
      <div class="panel-header-bracket">
        <span class="panel-title-text">ACTIVE DISPATCH FLOW</span>
        <div class="panel-id">FEED_LIVE_02</div>
      </div>
      <div class="panel-inner dispatch-list">
        <div class="dispatch-card-premium" v-for="task in displayTasks" :key="task.id">
          <div class="card-top">
            <span class="task-tag">TASK #{{ task.task_id }}</span>
            <span class="status-light" :class="task.status">{{ formatStatus(task.status) }}</span>
          </div>
          <div class="card-middle">
            <div class="node origin">{{ task.load_zone }}</div>
            <div class="flow-arrow">
              <div class="flow-particle"></div>
              <svg viewBox="0 0 100 10" preserveAspectRatio="none"><path d="M0 5H95L90 0M95 5L90 10" fill="none" stroke="currentColor"/></svg>
            </div>
            <div class="node dest">{{ task.unload_zone }}</div>
          </div>
          <div class="card-bottom">
            <div class="vehicle-info">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7H7"></path></svg>
              <span>{{ task.vehicle_id }}</span>
            </div>
            <div class="payload-info">EST: {{ task.weight_tons }}T</div>
          </div>
          <!-- Phase Indicator -->
          <div class="phase-steps">
            <div class="p-step" :class="{ active: ['loading'].includes(task.status), done: !['loading'].includes(task.status) && task.status }"></div>
            <div class="p-step" :class="{ active: ['hauling'].includes(task.status), done: ['unloading', 'returning'].includes(task.status) }"></div>
            <div class="p-step" :class="{ active: ['unloading'].includes(task.status), done: task.status === 'returning' }"></div>
            <div class="p-step" :class="{ active: task.status === 'returning' }"></div>
          </div>
        </div>
      </div>

      <!-- Environment Micro Panel (Added for richness) -->
      <div class="panel-header-bracket sub-header">
        <span class="panel-title-text">ENVIRONMENTAL TELEMETRY</span>
      </div>
      <div class="panel-inner environment-grid">
        <div class="env-item">
          <span class="label">AQI</span>
          <span class="val green">32</span>
        </div>
        <div class="env-item">
          <span class="label">WIND</span>
          <span class="val">4.2 m/s</span>
        </div>
        <div class="env-item">
          <span class="label">HUMD</span>
          <span class="val">45%</span>
        </div>
        <div class="env-item">
          <span class="label">TEMP</span>
          <span class="val">18.5°C</span>
        </div>
      </div>
    </aside>

    <!-- 5. Bottom HUD: Global Ticker & System Health -->
    <footer class="ops-hud-bottom glass-hud">
      <div class="incident-ticker">
        <div class="ticker-prefix">SYSTEM LOGS_</div>
        <div class="ticker-scroll">
          <div class="ticker-content-box">
             <span v-for="i in 5" :key="i"> [ALERT] 10:24:{{20+i}} - AUTONOMOUS TRUCK 0{{i}} HAS REACHED CRUSHER_01. DOCKING_INITIATED. // </span>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import { authState } from '../auth'
import * as echarts from 'echarts'

const API_BIZ_BASE = `http://${window.location.hostname}:8002/api/v1`

const kpi = ref({ total_tonnage: 830.7, avg_efficiency: 81.85, total_fuel: 2250, active_vehicle_count: 10, daily_trend: [] })
const fleet = ref([])
const activeTasks = ref([])
const leaderboard = ref([])
const countdown = ref(10)
const trendChartRef = ref(null)
const currentTime = ref('')
const currentDate = ref('')
let trendChart = null
let refreshTimer = null
let clockTimer = null

// --- Premium Mock Data (Ensures the UI is never empty) ---
const mockFleet = [
  { device_id: 'TRK-001', device_name: '卡车 TRK-01', location: { lng: 110.122, lat: 35.122 }, telemetry: { speed: 42.5 }, status: 'online' },
  { device_id: 'TRK-002', device_name: '卡车 TRK-02', location: { lng: 110.125, lat: 35.126 }, telemetry: { speed: 12.0 }, status: 'online' },
  { device_id: 'EXC-001', device_name: '挖机 EXC-01', location: { lng: 110.118, lat: 35.118 }, telemetry: { speed: 2.5 }, status: 'online' }
]
const mockTasks = [
  { id: 1, task_id: '1024', load_zone: 'PIT-01', unload_zone: 'CRS-02', vehicle_id: 'AUT-001', weight_tons: 85, status: 'hauling' },
  { id: 2, task_id: '1025', load_zone: 'PIT-03', unload_zone: 'CRS-01', vehicle_id: 'AUT-005', weight_tons: 72, status: 'loading' },
  { id: 3, task_id: '1026', load_zone: 'CRS-01', unload_zone: 'PIT-01', vehicle_id: 'AUT-002', weight_tons: 0, status: 'returning' }
]
const mockLeaderboard = [
  { vehicle_id: 'AUT-001', total_tonnage: 1250 },
  { vehicle_id: 'AUT-004', total_tonnage: 1180 },
  { vehicle_id: 'AUT-003', total_tonnage: 1020 },
  { vehicle_id: 'AUT-002', total_tonnage: 940 },
  { vehicle_id: 'AUT-005', total_tonnage: 810 }
]

const displayFleet = computed(() => fleet.value.length ? fleet.value : mockFleet)
const displayTasks = computed(() => activeTasks.value.length ? activeTasks.value : mockTasks)
const displayLeaderboard = computed(() => leaderboard.value.length ? leaderboard.value : mockLeaderboard)

const kpiSummary = computed(() => ({
  '当日产量': kpi.value.total_tonnage + ' T',
  '作业效率': kpi.value.avg_efficiency + ' T/H',
  '燃料消耗': kpi.value.total_fuel + ' L',
  '在线载具': kpi.value.active_vehicle_count + ' UNIT'
}))

const fetchData = async () => {
  try {
    const config = { headers: { Authorization: `Bearer ${authState.token}` } }
    const [resKpi, resFleet, resTasks, resLeader] = await Promise.all([
      axios.get(`${API_BIZ_BASE}/ops/production-kpi`, config),
      axios.get(`${API_BIZ_BASE}/ops/fleet/status`, config),
      axios.get(`${API_BIZ_BASE}/ops/tasks/active`, config),
      axios.get(`${API_BIZ_BASE}/ops/stats/efficiency-leaderboard`, config)
    ])
    
    kpi.value = resKpi.data
    fleet.value = resFleet.data
    activeTasks.value = resTasks.data
    leaderboard.value = resLeader.data.slice(0, 5)
    
    updateChart()
    countdown.value = 10
  } catch (err) {
    console.warn('Backend unavailable, using mock data baseline.', err)
  }
}

const updateClock = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  currentDate.value = now.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '.')
}

const getPositionStyle = (loc) => {
  const left = ((loc.lng - 110.115) / 0.02) * 100
  const top = (1 - (loc.lat - 35.115) / 0.02) * 100
  return { left: `${Math.min(95, Math.max(5, left))}%`, top: `${Math.min(95, Math.max(5, top))}%` }
}

const formatStatus = (s) => ({
  loading: '装载中', hauling: '运载中', unloading: '卸载中', returning: '返航中'
}[s] || s)

const updateChart = () => {
  if (!trendChart) return
  const mockTrend = Array.from({length: 12}, (_, i) => ({ 
    time: `1${i}:00`, 
    val1: 400 + Math.random()*200, 
    val2: 70 + Math.random()*30 
  }))
  const data = kpi.value.daily_trend.length ? kpi.value.daily_trend : mockTrend
  
  trendChart.setOption({
    xAxis: { data: data.map(d => d.time || new Date(d.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})) },
    series: [
      { name: '产量', data: data.map(d => d.val1 || d.tonnage) },
      { name: '效率', data: data.map(d => d.val2 || d.efficiency) }
    ]
  })
}

onMounted(() => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)

  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5, 12, 34, 0.95)', borderColor: '#3b82f6', textStyle: { color: '#fff', fontSize: 10 } },
      legend: { textStyle: { color: '#64748b', fontSize: 10 }, top: 0, icon: 'circle' },
      grid: { left: '30', right: '10', bottom: '20', top: '40' },
      xAxis: { type: 'category', axisLine: { lineStyle: { color: '#1e293b' } }, axisLabel: { color: '#475569', fontSize: 9 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } }, axisLabel: { color: '#475569', fontSize: 9 } },
      series: [
        { name: '产量', type: 'line', smooth: true, itemStyle: { color: '#00f0ff' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: 'rgba(0, 240, 255, 0.2)'}, {offset: 1, color: 'transparent'}]) } },
        { name: '效率', type: 'line', smooth: true, itemStyle: { color: '#3b82f6' } }
      ]
    })
    updateChart()
  }

  fetchData()
  refreshTimer = setInterval(() => {
    if (countdown.value > 1) countdown.value--
    else fetchData()
  }, 1000)
})

onUnmounted(() => {
  clearInterval(refreshTimer)
  clearInterval(clockTimer)
  trendChart?.dispose()
})
</script>

<style scoped>
.production-ops-container {
  width: 100vw; height: 100vh;
  background: #02060c;
  color: #cdd6f4;
  overflow: hidden;
  position: relative;
  font-family: 'Inter', system-ui, sans-serif;
  padding-top: 60px;
}

/* Background & Effects */
.background-vfx {
  position: absolute; inset: 0; pointer-events: none; z-index: 5;
}
.scanning-radar-line {
  position: absolute; top: 0; left: 0; width: 100%; height: 2px;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.2), transparent);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
  animation: scan-radar 8s infinite linear;
}
@keyframes scan-radar { from { top: -10%; } to { top: 110%; } }

.grid-layer {
  position: absolute; inset: 0;
  background-image: radial-gradient(circle, rgba(59, 130, 246, 0.05) 1px, transparent 1px);
  background-size: 40px 40px;
}

.map-immersive-background {
  position: absolute; inset: 0;
  background-image: url('/images/digital_twin_map.png');
  background-size: cover; background-position: center;
  mix-blend-mode: soft-light; opacity: 0.35;
}

/* Vehicle OSD Premium Style */
.vehicle-hud-marker {
  position: absolute; z-index: 100;
  transform: translate(-50%, -100%);
}
.marker-base { position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); }
.pulse-ring {
  width: 40px; height: 40px; border-radius: 50%;
  border: 1px solid rgba(16, 185, 129, 0.5);
  transform: scale(0.5); animation: sonar 2s infinite ease-out;
}
@keyframes sonar { from { transform: scale(0.5); opacity: 1; } to { transform: scale(2); opacity: 0; } }

.hud-lead-line {
  width: 2px; height: 50px;
  background: linear-gradient(to top, #3b82f6 20%, transparent);
  margin: 0 auto;
}

.premium-tag {
  background: rgba(10, 20, 35, 0.95);
  border: 1px solid #3b82f6;
  border-top: 3px solid #3b82f6;
  padding: 10px; border-radius: 2px; width: 150px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}
.tag-header { display: flex; justify-content: space-between; font-size: 10px; font-weight: 900; color: #fff; margin-bottom: 8px; }
.tag-body { display: flex; gap: 15px; }
.data-group { display: flex; flex-direction: column; }
.data-group .label { font-size: 8px; color: #64748b; }
.data-group .val { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #3b82f6; font-weight: 800; }
.data-group small { font-size: 8px; margin-left: 2px; }

/* Site Hotspots */
.site-hotspot { position: absolute; color: #64748b; opacity: 0.6; }
.hotspot-cross { width: 10px; height: 10px; border-left: 1px solid currentColor; border-top: 1px solid currentColor; margin-bottom: 5px; }
.hotspot-label { font-size: 10px; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px; }

/* Glass HUD Styling */
.glass-hud {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 4px 50px rgba(0,0,0,0.6);
}

.ops-hud-header {
  position: absolute; top: 100px; left: 50%; transform: translateX(-50%);
  width: 95%; height: 80px; padding: 0 30px;
  border-radius: 4px; display: flex; align-items: center; justify-content: space-between; z-index: 500;
}

.glow-text-blue {
  margin: 0; font-size: 20px; font-weight: 900; letter-spacing: 4px; color: #fff;
  text-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}
.glow-text-blue span { font-size: 10px; vertical-align: top; color: #3b82f6; }

.system-status-bar { display: flex; gap: 15px; margin-top: 5px; }
.status-node { font-size: 9px; font-weight: 800; color: #10b981; font-family: 'JetBrains Mono', monospace; }
.status-node.alert { color: #f59e0b; }

.hud-kpi-row { display: flex; gap: 40px; flex: 1; justify-content: center; }
.kpi-block { display: flex; flex-direction: column; width: 140px; }
.kpi-label-box { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
.kpi-label { font-size: 10px; color: #94a3b8; font-weight: 700; }
.kpi-trend { font-size: 9px; color: #10b981; }
.kpi-value { font-size: 28px; font-weight: 900; font-family: 'JetBrains Mono', monospace; color: #fff; line-height: 1; }
.glow-number { text-shadow: 0 0 15px rgba(255,255,255,0.2); }
.kpi-mini-gauge { width: 100%; height: 2px; background: rgba(59,130,246,0.1); margin-top: 6px; }
.kpi-mini-gauge .fill { height: 100%; background: #3b82f6; box-shadow: 0 0 5px #3b82f6; }

.hud-clock-box { text-align: right; }
.time-main { font-size: 24px; font-weight: 900; font-family: 'JetBrains Mono', monospace; color: #fff; }
.date-sub { font-size: 10px; color: #64748b; margin-top: 2px; }

/* Side Panels Premium */
.side-panel-premium {
  position: absolute; top: 195px; bottom: 120px; width: 340px;
  border-radius: 4px; padding: 20px; z-index: 500;
}
.ops-hud-left { left: 25px; }
.ops-hud-right { right: 25px; width: 380px; }

.panel-header-bracket {
  display: flex; justify-content: space-between; align-items: center;
  border-left: 3px solid #3b82f6; padding-left: 12px; margin-bottom: 20px;
}
.panel-title-text { font-size: 13px; font-weight: 900; color: #fff; letter-spacing: 1px; }
.panel-id { font-size: 9px; color: #3b82f6; font-family: 'JetBrains Mono', monospace; opacity: 0.6; }

.sub-header { margin-top: 40px; }

.chart-box-enhanced { width: 100%; height: 220px; }

.rank-item { display: flex; align-items: center; gap: 15px; margin-bottom: 18px; }
.rank-index { font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 900; color: #1e293b; -webkit-text-stroke: 1px #3b82f6; }
.rank-info { flex: 1; }
.rank-meta { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 11px; }
.rank-name { font-weight: 800; color: #cdd6f4; }
.rank-percent { color: #10b981; }
.rank-progress { width: 100%; height: 4px; background: rgba(0,0,0,0.3); border-radius: 2px; }
.rank-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #10b981); border-radius: 2px; }
.rank-val { font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 800; color: #fff; width: 50px; text-align: right; }

/* Dispatch Queue Premium */
.dispatch-list { display: flex; flex-direction: column; gap: 15px; height: 320px; overflow-y: auto; }
.dispatch-card-premium {
  background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.04);
  padding: 15px; padding-bottom: 20px; border-radius: 4px; border-left: 2px solid #3b82f6;
  position: relative; transition: all 0.2s;
}
.dispatch-card-premium:hover { background: rgba(255, 255, 255, 0.04); transform: scale(1.02); }

.card-top { display: flex; justify-content: space-between; margin-bottom: 12px; }
.task-tag { font-size: 10px; font-weight: 900; color: #64748b; }
.status-light { font-size: 10px; font-weight: 900; color: #10b981; display: flex; align-items: center; gap: 5px; }
.status-light::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; box-shadow: 0 0 5px currentColor; }
.status-light.loading { color: #3b82f6; }
.status-light.returning { color: #94a3b8; }

.card-middle { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; }
.node { font-size: 14px; font-weight: 900; color: #fff; font-family: 'JetBrains Mono', monospace; }
.flow-arrow { flex: 1; position: relative; color: #1e293b; padding: 0 10px; height: 10px; }
.flow-particle {
  position: absolute; width: 6px; height: 2px; background: #3b82f6; border-radius: 2px;
  animation: flow-move 2s infinite linear;
}
@keyframes flow-move { from { left: 0; opacity: 1; } to { left: 100%; opacity: 0; } }

.card-bottom { display: flex; justify-content: space-between; font-size: 10px; font-weight: 700; color: #64748b; }
.vehicle-info { display: flex; align-items: center; gap: 5px; color: #3b82f6; }

.phase-steps { display: flex; gap: 4px; position: absolute; bottom: 0; left: 0; width: 100%; padding: 0 15px 5px; }
.p-step { flex: 1; height: 2px; background: #1e293b; }
.p-step.active { background: #3b82f6; box-shadow: 0 0 5px #3b82f6; }
.p-step.done { background: #10b981; }

/* Environment Grid */
.environment-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.env-item {
  background: rgba(0,0,0,0.2); padding: 12px; border-radius: 4px;
  display: flex; flex-direction: column; gap: 5px; border: 1px solid rgba(255,255,255,0.02);
}
.env-item .label { font-size: 9px; font-weight: 800; color: #64748b; }
.env-item .val { font-size: 16px; font-weight: 900; color: #fff; font-family: 'JetBrains Mono', monospace; }
.env-item .val.green { color: #10b981; }

/* Bottom HUD: Ticker */
.ops-hud-bottom {
  position: absolute; bottom: 25px; left: 50%; transform: translateX(-50%);
  width: 95%; height: 40px; display: flex; align-items: center; padding: 0 25px;
  border-radius: 4px; z-index: 500;
}
.incident-ticker { display: flex; gap: 20px; align-items: center; width: 100%; overflow: hidden; }
.ticker-prefix { font-size: 11px; font-weight: 900; color: #ef4444; flex-shrink: 0; }
.ticker-scroll { overflow: hidden; flex: 1; font-size: 10px; font-family: 'JetBrains Mono', monospace; color: #64748b; }
.ticker-content-box { animation: ticker-run 60s linear infinite; white-space: nowrap; }
@keyframes ticker-run { from { transform: translateX(100%); } to { transform: translateX(-100%); } }

/* Animations & Scrollbar */
.animate-slide-right { animation: panel-in-left 0.8s cubic-bezier(0.16, 1, 0.3, 1); }
.animate-slide-left { animation: panel-in-right 0.8s cubic-bezier(0.16, 1, 0.3, 1); }
@keyframes panel-in-left { from { opacity: 0; transform: translateX(-30px); } to { opacity: 1; transform: translateX(0); } }
@keyframes panel-in-right { from { opacity: 0; transform: translateX(30px); } to { opacity: 1; transform: translateX(0); } }

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #3b82f6; border-radius: 10px; }
</style>

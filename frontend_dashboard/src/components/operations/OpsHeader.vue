<template>
  <header class="ops-hud-header glass-hud">
    <div class="hud-header-left">
      <div class="system-title">
        <h1 class="glow-text-blue">生产运营智控中心 <span>V2.4</span></h1>
        <div class="system-status-bar">
          <span class="status-node">卫星链路: 正常</span>
          <span class="status-node">核心引擎: 运行中</span>
          <span class="status-node alert">延迟: 42MS</span>
        </div>
      </div>
    </div>

    <div class="hud-kpi-row">
      <div class="kpi-block" v-for="(val, label) in store.kpiSummary" :key="label">
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
      <div class="date-sub">{{ currentDate }}</div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useOperationsStore } from '../../store/operations'

const store = useOperationsStore()
const currentTime = ref('')
const currentDate = ref('')
let clockTimer = null

const updateClock = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  currentDate.value = now.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '.')
}

onMounted(() => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
})

onUnmounted(() => {
  clearInterval(clockTimer)
})
</script>

<style scoped>
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
</style>

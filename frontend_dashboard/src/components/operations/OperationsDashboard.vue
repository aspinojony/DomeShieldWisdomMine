<template>
  <div class="production-ops-container">
    <!-- 1. Immersive 3D Map Context -->
    <Map3DViewer />

    <!-- 0. Dynamic Background VFX Overlay over map -->
    <div class="background-vfx-overlay">
      <div class="scanning-radar-line"></div>
      <div class="grid-layer-cyber"></div>
      <div class="vignette-layer"></div>
    </div>

    <!-- 2. Top HUD -->
    <OpsHeader />

    <!-- 3. Left HUD -->
    <aside class="ops-hud-left side-panel-premium tech-panel">
      <YieldTrendChart />
      <EquipmentRanking />
    </aside>

    <!-- 4. Right HUD -->
    <aside class="ops-hud-right side-panel-premium tech-panel">
      <ActiveDispatchQueue />
      <EnvironmentTelemetry />
    </aside>

    <!-- 6. Center Bottom Hub (New) -->
    <div class="center-bottom-hub tech-panel">
      <div class="hub-item" v-for="(val, key) in store.kpiSummary" :key="key">
        <div class="hub-label">{{ key }}</div>
        <div class="hub-val glowing-text">{{ val.split(' ')[0] }}<small class="unit">{{ val.split(' ')[1] }}</small></div>
      </div>
    </div>

    <!-- 5. Bottom HUD -->
    <footer class="ops-hud-bottom tech-panel-bottom">
      <div class="incident-ticker">
        <div class="ticker-prefix">系统日志_</div>
        <div class="ticker-scroll">
          <div class="ticker-content-box">
             <span v-for="i in 5" :key="i"> [系统提示] 10:24:{{20+i}} - 无人驾驶矿卡 0{{i}} 已到达 01 号破碎站。开始自动泊车接驳。 // </span>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useOperationsStore } from '../../store/operations'
import Map3DViewer from './Map3DViewer.vue'
import OpsHeader from './OpsHeader.vue'
import YieldTrendChart from './YieldTrendChart.vue'
import EquipmentRanking from './EquipmentRanking.vue'
import ActiveDispatchQueue from './ActiveDispatchQueue.vue'
import EnvironmentTelemetry from './EnvironmentTelemetry.vue'

const store = useOperationsStore()
let refreshTimer = null

onMounted(() => {
  store.fetchAllData()
  refreshTimer = setInterval(() => {
    store.fetchAllData()
  }, 10000)
})

onUnmounted(() => {
  clearInterval(refreshTimer)
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

/* Cyber Background & Effects Overlay */
.background-vfx-overlay { position: absolute; inset: 0; pointer-events: none; z-index: 5; }
.scanning-radar-line {
  position: absolute; top: 0; left: 0; width: 100%; height: 2px;
  background: linear-gradient(90deg, transparent, rgba(0, 240, 255, 0.4), transparent);
  box-shadow: 0 0 15px rgba(0, 240, 255, 0.5);
  animation: scan-radar 8s infinite linear;
}
@keyframes scan-radar { from { top: -10%; } to { top: 110%; } }

.grid-layer-cyber {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(to right, rgba(0, 240, 255, 0.03) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
}
.vignette-layer {
  position: absolute; inset: 0;
  background: radial-gradient(circle at center, transparent 40%, rgba(2, 6, 12, 0.95) 100%);
}

/* --------------------------------------------------------------------------
   GLOBAL CYBER-MINING DESIGN TOKENS (Shared across Ops components)
-----------------------------------------------------------------------------*/
:deep(.tech-panel) {
  background: rgba(10, 25, 47, 0.85); /* 深空蓝, 继承自主控大屏 */
  border: 1px solid rgba(0, 240, 255, 0.4);
  backdrop-filter: blur(15px);
  box-shadow:
    inset 0 0 20px rgba(0, 240, 255, 0.15),
    0 8px 32px rgba(0, 0, 0, 0.8);
  position: relative;
}

:deep(.tech-panel::before) {
  content: ''; position: absolute; top: -1px; left: -1px; width: 20px; height: 20px;
  border-top: 2px solid #00f0ff; border-left: 2px solid #00f0ff;
}
:deep(.tech-panel::after) {
  content: ''; position: absolute; bottom: -1px; right: -1px; width: 20px; height: 20px;
  border-bottom: 2px solid #00f0ff; border-right: 2px solid #00f0ff;
}

/* 底部专属：略去顶部装饰角 */
.tech-panel-bottom {
  background: rgba(10, 25, 47, 0.85);
  border: 1px solid rgba(0, 240, 255, 0.4);
  backdrop-filter: blur(15px);
  box-shadow: inset 0 -10px 20px rgba(0, 240, 255, 0.1), 0 0 32px rgba(0, 0, 0, 0.8);
}

:deep(.panel-header-cyber) {
  position: relative;
  padding: 1rem 1rem 0.5rem 1rem;
  border-bottom: 1px dashed rgba(0, 240, 255, 0.2);
  margin-bottom: 15px;
  display: flex; align-items: center; justify-content: space-between;
}

:deep(.title-deco) {
  width: 4px; height: 16px; 
  background: #00f0ff; 
  margin-right: 10px;
  box-shadow: 0 0 8px #00f0ff;
}

:deep(.glowing-text) {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 900;
  color: #cdd6f4;
  text-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
  letter-spacing: 1px;
}
:deep(.panel-id) { 
  font-size: 0.65rem; color: #00f0ff; font-family: 'JetBrains Mono', monospace; opacity: 0.8; 
  background: rgba(0, 240, 255, 0.1); padding: 2px 6px; border-radius: 2px;
}

:deep(.sub-header) { margin-top: 30px; border-top: 1px dashed rgba(0, 240, 255, 0.1); padding-top: 15px; }

/* Side Panels Premium */
.side-panel-premium {
  position: absolute; top: 120px; bottom: 85px; width: 360px;
  border-radius: 4px; padding: 15px; z-index: 500;
  display: flex; flex-direction: column;
}
.ops-hud-left { left: 20px; }
.ops-hud-right { right: 20px; width: 400px; }

/* Bottom HUD: Ticker */
.ops-hud-bottom {
  position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
  width: calc(100% - 880px); height: 45px; display: flex; align-items: center; padding: 0 25px;
  border-radius: 4px; z-index: 500;
}
.incident-ticker { display: flex; gap: 20px; align-items: center; width: 100%; overflow: hidden; }
.ticker-prefix { font-size: 11px; font-weight: 900; color: #00f0ff; flex-shrink: 0; text-shadow: 0 0 8px rgba(0,240,255,0.5); }
.ticker-scroll { overflow: hidden; flex: 1; font-size: 10px; font-family: 'JetBrains Mono', monospace; color: #8892b0; }
.ticker-content-box { animation: ticker-run 100s linear infinite; white-space: nowrap; }
@keyframes ticker-run { from { transform: translateX(100%); } to { transform: translateX(-100%); } }

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-thumb { background: rgba(0, 240, 255, 0.4); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 240, 255, 0.8); }

/* Center Bottom Hub */
.center-bottom-hub {
  position: absolute; bottom: 85px; left: 50%; transform: translateX(-50%);
  display: flex; justify-content: space-around; align-items: center;
  width: 600px; padding: 15px 30px; border-radius: 4px; z-index: 500;
  background: rgba(10, 25, 47, 0.7);
  box-shadow: inset 0 0 15px rgba(0, 240, 255, 0.2), 0 5px 20px rgba(0,0,0,0.5);
  border: 1px solid rgba(0, 240, 255, 0.3);
  border-top: 2px solid #00f0ff;
}
.hub-item { display: flex; flex-direction: column; align-items: center; gap: 5px; }
.hub-label { font-size: 11px; color: #8892b0; letter-spacing: 2px; }
.hub-val { font-family: 'Orbitron', monospace; font-size: 20px; color: #00f0ff; }
.hub-val .unit { font-size: 10px; color: #cdd6f4; margin-left: 4px; opacity: 0.8; font-family: 'JetBrains Mono', monospace; }
</style>

<template>
  <div>
    <div class="panel-header-cyber sub-header">
      <div style="display:flex; align-items:center;">
         <div class="title-deco"></div>
         <span class="glowing-text">设备效能 (OEE) 榜单</span>
      </div>
    </div>
    <div class="panel-inner ranking-list">
      <div class="rank-item" v-for="(item, idx) in store.displayLeaderboard" :key="item.vehicle_id">
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
  </div>
</template>

<script setup>
import { useOperationsStore } from '../../store/operations'

const store = useOperationsStore()
</script>

<style scoped>
.ranking-list { margin-top: 5px; }
.rank-item { display: flex; align-items: center; gap: 15px; margin-bottom: 18px; }
.rank-index { font-family: 'Orbitron', monospace; font-size: 16px; font-weight: 900; color: transparent; -webkit-text-stroke: 1px #00f0ff; opacity: 0.8; }
.rank-info { flex: 1; }
.rank-meta { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 11px; }
.rank-name { font-weight: 800; color: #cdd6f4; font-family: 'JetBrains Mono', monospace;}
.rank-percent { color: #00ff88; font-family: 'Orbitron', monospace; }
.rank-progress { width: 100%; height: 4px; background: rgba(0, 240, 255, 0.1); border-radius: 2px; }
.rank-fill { height: 100%; background: linear-gradient(90deg, #00f0ff, #00ff88); border-radius: 2px; box-shadow: 0 0 8px #00ff88; }
.rank-val { font-family: 'Orbitron', monospace; font-size: 12px; font-weight: 800; color: #fff; width: 50px; text-align: right; }
</style>

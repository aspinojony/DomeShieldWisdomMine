<template>
  <div>
    <div class="panel-header-cyber">
      <div style="display:flex; align-items:center;">
         <div class="title-deco"></div>
         <span class="glowing-text">实时智能调度流</span>
      </div>
      <div class="panel-id">链路: LIVE_02</div>
    </div>
    <div class="panel-inner dispatch-list">
      <div class="dispatch-card-premium" v-for="task in store.displayTasks" :key="task.id">
        <div class="card-top">
          <span class="task-tag">任务 #{{ task.task_id }}</span>
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
          <div class="payload-info">预估载重: {{ task.weight_tons }}T</div>
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
  </div>
</template>

<script setup>
import { useOperationsStore } from '../../store/operations'

const store = useOperationsStore()

const formatStatus = (s) => ({
  loading: '装载中', hauling: '运载中', unloading: '卸载中', returning: '返航中'
}[s] || s)
</script>

<style scoped>
.dispatch-list { display: flex; flex-direction: column; gap: 15px; height: 320px; overflow-y: auto; overflow-x: hidden; }
.dispatch-list::-webkit-scrollbar { width: 3px; }
.dispatch-list::-webkit-scrollbar-track { background: transparent; }
.dispatch-list::-webkit-scrollbar-thumb { background: rgba(0, 240, 255, 0.4); border-radius: 2px; }

.dispatch-card-premium {
  background: rgba(10, 25, 47, 0.6); border: 1px solid rgba(0, 240, 255, 0.2);
  padding: 15px; padding-bottom: 20px; border-radius: 4px; border-left: 3px solid #00f0ff;
  position: relative; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.dispatch-card-premium:hover { 
  background: rgba(0, 240, 255, 0.05); transform: translateX(5px); 
  box-shadow: 0 0 15px rgba(0, 240, 255, 0.2); border-color: rgba(0, 240, 255, 0.5);
}

.card-top { display: flex; justify-content: space-between; margin-bottom: 12px; }
.task-tag { font-size: 10px; font-weight: 900; color: #8892b0; letter-spacing: 1px; }
.status-light { font-size: 10px; font-weight: 900; color: #00ff88; display: flex; align-items: center; gap: 5px; }
.status-light::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; box-shadow: 0 0 8px currentColor; }
.status-light.loading { color: #00f0ff; }
.status-light.returning { color: #8892b0; }

.card-middle { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; }
.node { font-size: 14px; font-weight: 900; color: #fff; font-family: 'Orbitron', monospace; letter-spacing: 1px;}
.flow-arrow { flex: 1; position: relative; color: rgba(0, 240, 255, 0.2); padding: 0 10px; height: 10px; }
.flow-particle {
  position: absolute; width: 8px; height: 2px; background: #00f0ff; border-radius: 2px;
  box-shadow: 0 0 10px #00f0ff;
  animation: flow-move 1.5s infinite linear;
}
@keyframes flow-move { from { left: 0; opacity: 1; } to { left: 100%; opacity: 0; } }

.card-bottom { display: flex; justify-content: space-between; font-size: 10px; font-weight: 700; color: #8892b0; }
.vehicle-info { display: flex; align-items: center; gap: 5px; color: #00f0ff; font-family: 'Orbitron', monospace; }

.phase-steps { display: flex; gap: 4px; position: absolute; bottom: 0; left: 0; width: 100%; padding: 0; }
.p-step { flex: 1; height: 2px; background: rgba(0, 240, 255, 0.1); }
.p-step.active { background: #00f0ff; box-shadow: 0 0 5px #00f0ff; }
.p-step.done { background: #00ff88; box-shadow: 0 0 5px #00ff88; }
</style>

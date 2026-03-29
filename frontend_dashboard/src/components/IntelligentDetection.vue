<template>
  <div class="intel-detection-container">
    <!-- Header Section (Simplified to avoid overlap with App header) -->
    <header class="intel-header">
      <div class="header-breadcrumb">
        <span class="root">AI CORE</span>
        <span class="separator">/</span>
        <span class="leaf">诊断工作台</span>
      </div>
      
      <div class="header-controls">
        <div class="mode-selector">
          <button :class="{ active: mode === 'manual' }" @click="mode = 'manual'">
            <span class="icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
            </span> 本地研判
          </button>
          <button :class="{ active: mode === 'auto' }" @click="mode = 'auto'">
            <span class="icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
            </span> 实时侦察
          </button>
        </div>

        <div class="system-status">
          <div class="status-item">
            <span class="label">引擎状态:</span>
            <span class="value" :class="{ online: isEngineLive }">
              <span class="status-dot" :class="{ online: isEngineLive }"></span>
              {{ isEngineLive ? '在线推演' : '连接中断' }}
            </span>
          </div>
          <div class="status-item">
            <span class="label">当前模型:</span>
            <span class="value model-id">YOLOv10-Mining-PRO</span>
          </div>
        </div>
      </div>
    </header>

    <main class="intel-main">
      <!-- Left: Analysis Area -->
      <section class="analysis-panel card-glass">
        <div class="panel-header">
          <div class="flex-align">
            <span class="pulse-dot" v-if="mode === 'auto'"></span>
            <h3>{{ mode === 'manual' ? '本地图像研判' : '现场实时侦察流' }}</h3>
          </div>
          <div v-if="mode === 'auto'" class="auto-controls">
            <button @click="triggerAutomaticInspection" class="btn-action" :disabled="isAnalyzing">
              发起自动巡检
            </button>
          </div>
        </div>
        
        <div class="work-area">
          <!-- Manual Upload Zone -->
          <div v-if="mode === 'manual'" 
               class="upload-zone" 
               @dragover.prevent 
               @drop.prevent="handleDrop"
               :class="{ 'is-dragging': isDragging }"
               @dragenter="isDragging = true"
               @dragleave="isDragging = false">
            
            <div v-if="!currentImage" class="upload-placeholder">
              <div class="scanner-line"></div>
              <div class="icon-up">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>
              </div>
              <p>拖拽无人机航拍图或点击上传</p>
              <input type="file" ref="fileInput" @change="handleFileSelect" hidden accept="image/*">
              <button @click="$refs.fileInput.click()" class="btn-primary">选择图像文件</button>
            </div>

            <div v-else class="image-preview-container">
              <img :src="currentImage" alt="Preview" class="preview-img">
              <div v-if="isAnalyzing" class="analysis-overlay">
                <div class="loader-ring"></div>
                <p>正在进行语义分割与几何解算...</p>
              </div>
            </div>
          </div>

          <!-- Autonomous Monitor Zone -->
          <div v-else class="auto-monitor-zone">
             <div v-if="!latestAutoImage" class="no-feed">
               <div class="glitch-text" data-text="WAITING FOR FEED...">WAITING FOR FEED...</div>
               <p>当前无活动侦察任务，点击“发起自动巡检”启动无人机</p>
             </div>
             <div v-else class="feed-container">
               <div class="stream-info">
                 <span class="cam-id">CAM-UAV-01</span>
                 <span class="timestamp">{{ latestAutoResult?.timestamp }}</span>
               </div>
               <img :src="`http://localhost:8003${latestAutoImage}`" alt="Live Feed" class="feed-img">
               <div class="overlay-frames"></div>
               <div class="scan-bar"></div>
             </div>
          </div>
        </div>

        <!-- Dynamic Metrics Footer -->
        <div class="metrics-bar" v-if="currentResult">
          <div class="metric">
            <span class="label">特征物数量</span>
            <span class="value">{{ currentResult.anomalies_found }}</span>
          </div>
          <div class="metric">
            <span class="label">最大宽幅 (mm)</span>
            <span class="value orange">{{ currentResult.max_width_mm }}</span>
          </div>
          <div class="metric">
            <span class="label">风险等级</span>
            <span class="value" :class="getLevelClass(currentResult.alert_level)">{{ currentResult.alert_level }}</span>
          </div>
          <div class="metric">
            <span class="label">推演延迟 (ms)</span>
            <span class="value">{{ currentResult.processing_time_ms }}</span>
          </div>
        </div>
      </section>

      <!-- Right: History Area -->
      <aside class="history-panel card-glass">
        <div class="panel-header">
          <h3>研判审计历史</h3>
          <button @click="fetchHistory" class="btn-refresh" title="刷新">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"/></svg>
          </button>
        </div>
        <div class="history-scroll">
          <div v-for="item in history" :key="item.id" class="history-card" @click="selectHistoryItem(item)">
            <div class="card-thumb">
              <img :src="`http://localhost:8003${item.image_url}`" alt="Thumb">
              <div class="card-tag" :class="getLevelClass(item.alert_level)">{{ item.alert_level.split(' ')[0] }}</div>
            </div>
            <div class="card-content">
              <div class="card-time">{{ item.timestamp.split(' ')[1] }}</div>
              <div class="card-brief">宽度: {{ item.max_width_mm }}mm / 发现: {{ item.anomalies_found }}</div>
            </div>
          </div>
          <div v-if="history.length === 0" class="empty-list">暂无研判数据</div>
        </div>
      </aside>
    </main>

    <!-- Modal remains similar but cleaner -->
    <div v-if="showDetail" class="modal-overlay" @click.self="showDetail = false">
      <div class="modal-content card-glass">
        <div class="modal-header">
          <h3>检测报告 - {{ selectedItem?.id }}</h3>
          <button @click="showDetail = false" class="btn-close">×</button>
        </div>
        <div class="modal-split">
          <div class="modal-img-box">
             <img :src="`http://localhost:8003${selectedItem?.image_url}`">
          </div>
          <div class="modal-details">
             <h4>AI 系统研判结论</h4>
             <div class="detail-row">
               <span>采集时间</span>
               <span>{{ selectedItem?.timestamp }}</span>
             </div>
             <div class="detail-row">
               <span>风险级别</span>
               <span :class="getLevelClass(selectedItem?.alert_level)">{{ selectedItem?.alert_level }}</span>
             </div>
             <div class="detail-row">
               <span>最大裂缝参数</span>
               <span class="highlight">{{ selectedItem?.max_width_mm }} mm</span>
             </div>
             <div class="action-grid">
               <button class="btn-primary">同步至数字孪生</button>
               <button class="btn-outline">下发人工核查</button>
             </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import axios from 'axios'

const mode = ref('manual') // 'manual' or 'auto'
const currentImage = ref(null)
const isAnalyzing = ref(false)
const manualResult = ref(null)
const latestAutoResult = ref(null)
const isEngineLive = ref(true)
const history = ref([])
const isDragging = ref(false)
const showDetail = ref(false)
const selectedItem = ref(null)

let pollTimer = null

const currentResult = computed(() => {
  return mode.value === 'manual' ? manualResult.value : latestAutoResult.value
})

const latestAutoImage = computed(() => {
  return latestAutoResult.value?.image_url || null
})

const fetchHistory = async () => {
  try {
    const res = await axios.get('http://localhost:8003/api/v1/vision/history')
    history.value = res.data
  } catch (e) {
    console.error("Fetch history failed", e)
    isEngineLive.value = false
  }
}

const fetchLatestAuto = async () => {
  try {
    const res = await axios.get('http://localhost:8003/api/v1/vision/latest')
    const result = res?.data?.data || res?.data
    if (result && (!latestAutoResult.value || result.id !== latestAutoResult.value.id)) {
      latestAutoResult.value = result
      fetchHistory() // Refresh the sidebar
    }
  } catch (e) {
    console.warn("Auto polling failed", e)
  }
}

const triggerAutomaticInspection = async () => {
  isAnalyzing.value = true
  try {
    await axios.post('http://localhost:8001/api/v1/ai/trigger_crisis')
    // The drone flight takes some time, it will automatically update via polling
  } catch (e) {
    alert("触发自动巡检失败")
  } finally {
    setTimeout(() => { isAnalyzing.value = false }, 2000)
  }
}

const startPolling = () => {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(fetchLatestAuto, 2000)
}

watch(mode, (newMode) => {
  if (newMode === 'auto') {
    startPolling()
  } else {
    if (pollTimer) clearInterval(pollTimer)
  }
})

onMounted(() => {
  fetchHistory()
  if (mode.value === 'auto') startPolling()
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

// --- Manual Upload Logic ---
const handleFileSelect = (e) => {
  const file = e.target.files[0]
  if (file) processManualFile(file)
}

const handleDrop = (e) => {
  const file = e.dataTransfer.files[0]
  if (file) processManualFile(file)
  isDragging.value = false
}

const processManualFile = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    currentImage.value = e.target.result
    analyzeManual(file)
  }
  reader.readAsDataURL(file)
}

const analyzeManual = async (file) => {
  isAnalyzing.value = true
  manualResult.value = null
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await axios.post('http://localhost:8003/api/v1/vision/analyze_crack', formData)
    if (res.data.status === 'success') {
      manualResult.value = res.data.data
      fetchHistory()
    }
  } catch (e) {
    alert("分析失败: 视觉推演服务未就绪")
  } finally {
    isAnalyzing.value = false
  }
}

const selectHistoryItem = (item) => {
  selectedItem.value = item
  showDetail.value = true
}

const getLevelClass = (level) => {
  if (!level) return ''
  if (level.includes('三级') || level.includes('警报')) return 'level-danger'
  if (level.includes('二级') || level.includes('预警')) return 'level-warning'
  if (level.includes('一级') || level.includes('监控')) return 'level-info'
  return 'level-safe'
}
</script>

<style scoped>
.intel-detection-container {
  padding: 0;
  background: #060b13;
  color: #cdd6f4;
  height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  overflow: hidden;
  padding-top: 60px; /* Offset for Global App Header */
}

.intel-header {
  height: 60px;
  background: rgba(15, 23, 42, 0.4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 25px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.header-breadcrumb {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-breadcrumb .root {
  color: #00f0ff;
  font-weight: 800;
  font-size: 11px;
  letter-spacing: 1px;
}

.header-breadcrumb .leaf {
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
}

.header-breadcrumb .separator {
  color: #1e293b;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 30px;
}

.mode-selector {
  background: #0f172a;
  padding: 4px;
  border-radius: 8px;
  display: flex;
  gap: 4px;
  border: 1px solid #1e293b;
}

.mode-selector button {
  background: transparent;
  border: none;
  color: #64748b;
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.mode-selector button.active {
  background: #00f0ff;
  color: #000;
}

.system-status {
  display: flex;
  gap: 20px;
}

.status-item {
  display: flex;
  flex-direction: column;
}

.status-item .label {
  font-size: 10px;
  color: #64748b;
}

.status-item .value {
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #64748b;
}

.status-dot.online {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

.model-id {
  color: #38bdf8;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px !important;
}

.value.online {
  color: #10b981;
}

.intel-main {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 2px; /* Dark grid line effect */
  background: #1e293b;
}

.card-glass {
  background: #0a111f;
  position: relative;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 20px 25px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.flex-align {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.work-area {
  flex: 1;
  padding: 0 25px;
  min-height: 0;
}

/* Common zone styling */
.upload-zone, .auto-monitor-zone {
  height: calc(100% - 20px);
  background: #020617;
  border-radius: 12px;
  border: 1px solid #1e293b;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.upload-zone.is-dragging {
  border-color: #00f0ff;
  box-shadow: inset 0 0 20px rgba(0,240,255,0.1);
}

.upload-placeholder {
  text-align: center;
}

.icon-up {
  font-size: 48px;
  margin-bottom: 20px;
  filter: drop-shadow(0 0 10px #00f0ff);
}

.scanner-line {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 2px;
  background: #00f0ff;
  box-shadow: 0 0 15px #00f0ff;
  animation: scan 4s infinite linear;
  opacity: 0.3;
}

.btn-primary {
  background: #00f0ff;
  color: #000;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-primary:hover {
  transform: scale(1.05);
}

.image-preview-container, .feed-container {
  width: 100%;
  height: 100%;
  padding: 15px;
  display: flex;
  flex-direction: column;
}

.preview-img, .feed-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 8px;
}

/* Auto Monitor Styles */
.no-feed {
  text-align: center;
}

.glitch-text {
  font-size: 24px;
  font-weight: 900;
  color: #1e293b;
  letter-spacing: 4px;
}

.stream-info {
  position: absolute;
  top: 30px;
  left: 40px;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px);
  padding: 6px 12px;
  border-radius: 4px;
  display: flex;
  gap: 15px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  z-index: 10;
}

.scan-bar {
  position: absolute;
  width: 100%;
  height: 1px;
  background: rgba(0, 240, 255, 0.5);
  top: 0;
  animation: scan 3s infinite linear;
}

/* Metrics Bar */
.metrics-bar {
  height: 100px;
  margin: 20px 25px;
  background: #0f172a;
  border-radius: 12px;
  border: 1px solid #1e293b;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  padding: 20px;
}

.metric {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border-right: 1px solid #1e293b;
}

.metric:last-child { border: none; }

.metric .label {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 4px;
}

.metric .value {
  font-size: 24px;
  font-weight: 800;
  font-family: 'JetBrains Mono', monospace;
}

.metric .value.orange { color: #f97316; }

/* History Sidebar */
.history-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-card {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 10px;
  padding: 8px;
  display: flex;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.history-card:hover {
  border-color: #00f0ff;
  transform: translateX(-4px);
}

.card-thumb {
  width: 80px;
  height: 60px;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.card-thumb img {
  width: 100%; height: 100%; object-fit: cover;
}

.card-tag {
  position: absolute;
  top: 0; right: 0;
  font-size: 8px;
  padding: 2px 4px;
  border-bottom-left-radius: 4px;
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card-time { font-size: 11px; color: #64748b; }
.card-brief { font-size: 11px; font-weight: 600; margin-top: 2px; }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 23, 0.9);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  width: 1000px;
  max-width: 90vw;
  background: #0a111f;
  padding: 30px;
  border-radius: 16px;
  border: 1px solid #1e293b;
}

.modal-split {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 30px;
  margin-top: 20px;
}

.modal-img-box {
  background: #000;
  border-radius: 12px;
  overflow: hidden;
}

.modal-img-box img { width: 100%; height: auto; display: block; }

.modal-details h4 { margin: 0 0 20px; color: #00f0ff; }

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #1e293b;
  font-size: 14px;
}

.detail-row span:first-child { color: #64748b; }

.highlight { font-weight: 800; color: #f97316; }

.action-grid {
  margin-top: 40px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-outline {
  padding: 10px;
  border-radius: 6px;
  background: transparent;
  border: 1px solid #1e293b;
  color: #fff;
  cursor: pointer;
}

/* Animations & Utilities */
.level-danger { color: #f43f5e; background: rgba(244, 63, 94, 0.1); }
.level-warning { color: #f59e0b; background: rgba(245, 158, 11, 0.1); }
.level-info { color: #0ea5e9; background: rgba(14, 165, 233, 0.1); }

@keyframes scan {
  from { top: 0; }
  to { top: 100%; }
}

.pulse-dot {
  width: 8px; height: 8px;
  background: #10b981;
  border-radius: 50%;
  box-shadow: 0 0 8px #10b981;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.5; }
  100% { transform: scale(1); opacity: 1; }
}

.loader-ring {
  width: 40px; height: 40px;
  border: 3px solid rgba(0,240,255,0.1);
  border-top-color: #00f0ff;
  border-radius: 50%;
  animation: spin 1s infinite linear;
  margin-bottom: 15px;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
</style>

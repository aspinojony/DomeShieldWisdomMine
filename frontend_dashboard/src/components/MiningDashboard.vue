<template>
  <div class="app-wrapper">
    <div class="dashboard-grid">
      <!-- 左侧监控列表 (折叠式) -->
      <aside class="side-panel tech-panel left-panel">
      <!-- 1: 作业设备 -->
      <div class="left-section">
        <div class="panel-header">
           <div class="title-deco"></div>
           <h2 class="glowing-text">作业设备</h2>
        </div>
        <div class="section-body device-summary">
            <div class="ds-row interactive-item" v-for="(stat, type) in miningSummary.asset_stats" :key="type" @click="focusOnCategory(type)">
              <div class="ds-icon" :class="getAssetColor(type)">
                <svg v-if="type === 'excavator'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l2-4h14l2 4"></path><path d="M1 9h22v6H1z"></path></svg>
                <svg v-else-if="type === 'truck'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><path d="M2 14h20v6H2z"></path></svg>
                <svg v-else-if="type === 'uav'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v19M5 8l14 8M19 8L5 16"></path></svg>
              </div>
              <div class="ds-info"><span>{{ formatAssetType(type) }}</span> 总数 <strong class="text-white">{{ stat.total }}</strong>台</div>
              <div class="ds-status text-cyan">在线 <strong>{{ stat.online }}</strong>台</div>
            </div>
        </div>
      </div>

      <!-- 2: 作业动态 -->
      <div class="left-section" style="border-top: 1px dashed rgba(0,240,255,0.2);">
        <div class="panel-header">
           <div class="title-deco"></div>
           <h2 class="glowing-text">作业动态</h2>
        </div>
        <div class="section-body dynamic-log custom-scrollbar">
           <div class="log-item interactive-item" v-for="(log, i) in miningSummary.operation_logs" :key="i" @click="showLogDetail(log)">
             <span class="log-time">{{ log.time }}</span>
             <span class="log-event" :class="{'text-cyan': log.level === 'info', 'text-green': log.level === 'success'}">
               {{ log.event }}
             </span>
           </div>
           <div v-if="miningSummary.operation_logs.length === 0" class="empty-hint" style="padding: 10px; color: #8892b0; font-size: 0.8rem; text-align: center;">暂无动态记录</div>
        </div>
      </div>

      <!-- 3: 预警信息 -->
      <div class="left-section flex-grow" style="border-top: 1px dashed rgba(0,240,255,0.2);">
        <div class="panel-header">
           <div class="title-deco"></div>
           <h2 class="glowing-text">预警信息</h2>
        </div>
        <div class="section-body alert-list custom-scrollbar">
           <div class="alert-item" v-for="alert in miningSummary.recent_alerts" :key="alert.id" @click="flyToSensor(alert.device_id)">
             <div class="alert-level" :class="'level-' + getAlertLevel(alert.alert_level)">
               {{ formatLevelName(alert.alert_level) }}
             </div>
             <div class="alert-content">
               {{ alert.message }}
               <br/><span class="alert-time">{{ formatDateSimple(alert.triggered_at) }}</span>
             </div>
           </div>
           <div v-if="miningSummary.recent_alerts.length === 0" class="empty-hint">暂无异常告警</div>
        </div>
      </div>

      <!-- 4: 2024吨成本 -->
      <div class="left-section" style="border-top: 1px dashed rgba(0,240,255,0.2);">
        <div class="panel-header" style="justify-content: space-between;">
           <div style="display:flex;align-items:center;">
              <div class="title-deco"></div>
              <h2 class="glowing-text">2024吨成本</h2>
           </div>
           <span class="unit" style="font-size:0.7rem;color:#8892b0;">元/吨</span>
        </div>
        <div class="section-body cost-panel" style="display: flex; align-items: center; justify-content: space-around;">
           <div ref="chartCost" class="echart-box" style="height: 120px; width: 120px;"></div>
           <div class="cost-legend">
              <div class="cl-row" v-for="(c, i) in miningSummary.cost_metrics" :key="i">
                <i class="dot" :style="{ background: c.color }"></i>{{ c.name }} 
                <strong :style="{ color: c.color }">{{ c.cost }}</strong> 
                <span>{{ c.value }}%</span>
              </div>
           </div>
        </div>
      </div>
    </aside>

    <!-- 中央核心视图与底是指控台 -->
    <section class="main-view tech-panel">
      <!-- 移除原有占位遮罩，正式展示 Cesium -->
      <div id="cesiumContainer" class="cesium-placeholder"></div>

      <!-- 视围交互：底部影视级导播台 -->
      <div class="cinematic-pov-controls glass-card">
        <button class="pov-btn" @click="flyToGlobal"> 全局鸟瞰</button>
        <button class="pov-btn" @click="flyToUAV"> UAV 跟飞</button>
        <button class="pov-btn danger-btn" @click="flyToDanger"> 高危抵近</button>
      </div>

      <!-- 视围交互：右下角环境干涉面板 -->
      <div class="env-control-panel glass-card">
        <h4>环境干涉台</h4>
        <label><input type="checkbox" v-model="envSettings.shadows" @change="toggleShadows">  实时光照与阴影</label>
        <label><input type="checkbox" v-model="envSettings.fence" @change="toggleFence">  电子红带警戒图层</label>
      </div>
      
      <!-- 3D 实体点击弹窗 -->
      <div 
        v-if="selectedSensor" 
        class="sensor-popup glass-card"
        :style="{ left: popupPosition.x + 'px', top: popupPosition.y + 'px' }"
      >
        <div class="popup-header">
          <h4> {{ selectedSensor.device_id }}</h4>
          <button class="close-btn" @click="closePopup">×</button>
        </div>
        <div class="popup-body">
          <p><strong>型号:</strong> {{ formatType(selectedSensor.device_type) }}</p>
          <p><strong>状态:</strong> 
            <span :class="isAlert(selectedSensor) ? 'danger-text' : 'safe-text'">
              {{ isAlert(selectedSensor) ? '告警中' : '运行正常' }}
            </span>
          </p>
          <div class="popup-data">
            <p v-if="selectedSensor.crack_width_mm !== undefined">裂缝宽度: <span>{{ selectedSensor.crack_width_mm }} mm</span></p>
            <p v-if="selectedSensor.energy_level !== undefined">微震能量: <span>{{ selectedSensor.energy_level }} J</span></p>
            <p v-if="selectedSensor.settlement_mm !== undefined">沉降量: <span>{{ selectedSensor.settlement_mm }} mm</span></p>
            <p v-if="selectedSensor.pressure_kpa !== undefined">孔隙水压力: <span>{{ selectedSensor.pressure_kpa }} kPa</span></p>
          </div>
          <button class="btn btn-detail" @click="viewDetailAction(selectedSensor)"> 查看分析图谱</button>
        </div>
      </div>
      
      <!-- 悬浮状态栏 -->
      <div class="status-overlay">
        <span class="status-badge"><i class="dot bg-green"></i> 注册设备: {{ sysStats.deviceCount }} 台</span>
        <span class="status-badge"><i class="dot bg-green"></i> 告警规则: {{ sysStats.ruleCount }} 条</span>
        <span class="status-badge"><i class="dot bg-green"></i> 无人机云台就绪</span>
      </div>

      <!-- 空天指控中心 (悬浮于底部) -->
      <div 
        class="uav-command-center"
        :class="{'uav-active-mode': activeUavCount > 0 || forceShowUav, 'uav-minimized': activeUavCount === 0 && !forceShowUav}"
      >
        <h3 class="uav-title" @click="forceShowUav = !forceShowUav">
           空天无人机指控集群 
          <span v-if="activeUavCount > 0" class="mini-status-badge">任务中 ({{ activeUavCount }})</span>
          <span v-else class="mini-status-badge inactive">待命</span>
          <span class="uav-toggle-hint">{{ (activeUavCount > 0 || forceShowUav) ? '▼' : '▲' }}</span>
        </h3>
        <div class="uav-fleet-list">
          <div 
            v-for="drone in uavFleet" 
            :key="drone.id" 
            class="uav-card"
            :class="{'uav-active': drone.status !== '待命闲置' && drone.status !== '已返航'}"
          >
            <div class="uav-info">
              <span class="uav-id">{{ drone.id }}</span>
              <span class="uav-type">{{ drone.type }}</span>
            </div>
            <div class="uav-state">
              <span class="uav-status-badge" :class="getStatusClass(drone.status)">
                {{ drone.status }}
              </span>
              <span class="uav-target" v-if="drone.target"> 锁定: {{ drone.target }}</span>
            </div>
            
            <!-- 进度条模拟飞行 -->
            <div class="uav-progress-bar" v-if="drone.status !== '待命闲置' && drone.status !== '已返航'">
               <div class="uav-progress-fill" :style="{ width: drone.progress + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 无人机实时侦察画面 (新增) -->
      <div v-if="latestVisionResult && activeUavCount > 0" class="uav-vision-feed glass-card animate-slide-up">
        <div class="feed-header">
           <span class="live-tag">● LIVE</span>
           <span class="feed-title">无人机载视觉智脑联测</span>
        </div>
        <div class="feed-body">
           <img :src="`http://${window.location.hostname}:8003` + latestVisionResult.data.image_url" alt="Drone Vision" class="vision-img" />
           <div class="vision-overlay">
              <div class="overlay-row"><span>目标:</span> <strong class="text-cyan">SLOPE-ZONE-A</strong></div>
              <div class="overlay-row"><span>研判:</span> <strong :class="latestVisionResult.data.alert_level.includes('安全') ? 'safe-text' : 'danger-text'">{{ latestVisionResult.data.alert_level }}</strong></div>
           </div>
        </div>
      </div>
    </section>

    <!-- 底部指控台：全局物流与核心效率 -->
    <aside class="side-panel tech-panel bottom-panel">
      <!-- OEE 全局分析 -->
      <div class="bottom-section" style="flex: 1.2;">
        <div class="panel-header" style="display:flex; justify-content: space-between; align-items: center;">
           <h2 class="glowing-text">OEE 综合效率</h2>
           <span class="text-green" style="font-weight: bold; font-size: 1.1rem; text-shadow: 0 0 5px #00ff88;">{{ miningSummary.equipment_oee?.oee_score }}%</span>
        </div>
        <div class="section-body device-info-panel" style="flex-direction: column; align-items: stretch; justify-content: center;">
           <div class="oee-bar-row">
              <span class="oee-label">时间稼动率</span>
              <div class="oee-bar"><div class="oee-fill bg-cyan" :style="{ width: miningSummary.equipment_oee?.availability + '%' }"></div></div>
              <span class="oee-val">{{ miningSummary.equipment_oee?.availability }}%</span>
           </div>
           <div class="oee-bar-row">
              <span class="oee-label">性能表现率</span>
              <div class="oee-bar"><div class="oee-fill bg-blue" :style="{ width: miningSummary.equipment_oee?.performance + '%' }"></div></div>
              <span class="oee-val">{{ miningSummary.equipment_oee?.performance }}%</span>
           </div>
           <div class="oee-bar-row">
              <span class="oee-label">出矿质量率</span>
              <div class="oee-bar"><div class="oee-fill bg-green" :style="{ width: miningSummary.equipment_oee?.quality + '%' }"></div></div>
              <span class="oee-val">{{ miningSummary.equipment_oee?.quality }}%</span>
           </div>
        </div>
      </div>
      
      <!-- 物流卡口 (防癌点) -->
      <div class="bottom-section" style="flex: 1.5; border-left: 1px dashed rgba(0,240,255,0.2);">
        <div class="panel-header">
           <h2 class="glowing-text">物流拥堵卡口预警</h2>
        </div>
        <div class="section-body material-quality-panel" style="flex-direction: column; gap: 4px; overflow-y: auto; padding: 4px 10px;">
           <div class="chokepoint-row interactive-item" v-for="(cp, i) in miningSummary.logistic_chokepoints" :key="i" :class="cp.status" @click="focusChokepoint(cp)">
              <span class="cp-loc"><i class="dot" :class="cp.status === 'congested' ? 'bg-orange' : 'bg-green'"></i> {{ cp.location }}</span>
              <span class="cp-wait">等候车辆: <strong :class="cp.status === 'congested' ? 'danger-text' : 'text-white'">{{ cp.waiting_trucks }}</strong> 辆</span>
              <span class="cp-time">平均耗时: <strong>{{ cp.avg_wait_min }}</strong> min</span>
           </div>
        </div>
      </div>

      <!-- 产量与剥离量双核心 -->
      <div class="bottom-section" style="flex: 1.5; border-left: 1px dashed rgba(0,240,255,0.2);">
        <div class="panel-header">
           <h2 class="glowing-text">核心采剥进度</h2>
        </div>
        <div class="section-body production-panel">
           <div class="gauge-card">
              <div ref="chartYield" class="echart-box" style="height: 120px; width: 120px;"></div>
           </div>
           <div class="gauge-text-group">
              <div class="gauge-info">
                 <div class="g-title">{{ miningSummary.production_today.current }} <small>采矿量 (吨)</small></div>
                 <div class="g-val color-green">
                    <svg width="100" height="30" viewBox="0 0 100 30">
                       <rect x="0" y="10" width="100" height="10" rx="5" fill="rgba(255,255,255,0.1)"></rect>
                       <rect x="0" y="10" :width="Math.min(100, (miningSummary.production_today.current/miningSummary.production_today.target)*100)" height="10" rx="5" fill="#00ff88"></rect>
                    </svg>
                 </div>
                 <div class="g-sub">目标: {{ miningSummary.production_today.target }} 吨</div>
              </div>
              <div class="gauge-info">
                 <div class="g-title">{{ miningSummary.stripping_progress?.current_m3 || 0 }} <small>剥离进度 (m³)</small></div>
                 <div class="g-val color-orange">
                     <svg width="100" height="30" viewBox="0 0 100 30">
                       <rect x="0" y="10" width="100" height="10" rx="5" fill="rgba(255,255,255,0.1)"></rect>
                       <rect x="0" y="10" :width="Math.min(100, ((miningSummary.stripping_progress?.current_m3 || 0)/(miningSummary.stripping_progress?.target_m3 || 1))*100)" height="10" rx="5" fill="#ff9f00"></rect>
                    </svg>
                 </div>
                 <div class="g-sub">实时剥采比: {{ miningSummary.stripping_progress?.ratio }}</div>
              </div>
           </div>
        </div>
      </div>
    </aside>
  </div>
  </div>
  <!-- AI 推演证据弹窗 (新增核心交互) -->
  <div v-if="selectedAiAlert" class="ai-modal-overlay" @click.self="closeAiDetail">
      <div class="ai-modal-content glass-card animate-zoom-in">
          <div class="modal-header">
              <h3 class="glowing-text"> 算法深度研判：{{ selectedAiAlert.id }}</h3>
              <button class="close-btn" @click="closeAiDetail">×</button>
          </div>
          <div class="modal-body">
              <div class="risk-info-grid">
                  <div class="risk-meter-box">
                      <div class="meter-header">
                        <span>坍塌概率阈值推演</span>
                        <strong :style="{ color: getProbColor(selectedAiAlert.probability) }">{{ selectedAiAlert.probability }}%</strong>
                      </div>
                      <div class="meter-track">
                          <div class="meter-fill" :style="{ width: selectedAiAlert.probability + '%', background: getProbColor(selectedAiAlert.probability) }"></div>
                      </div>
                  </div>
                  <div class="risk-context">
                      <p><strong>判别级别:</strong> <span :class="getProbLevelClass(selectedAiAlert.probability)">{{ selectedAiAlert.level }}</span></p>
                      <p><strong>关联设备:</strong> {{ selectedAiAlert.device }}</p>
                      <p><strong>指令预案:</strong> {{ selectedAiAlert.action }}</p>
                  </div>
              </div>
              
              <div class="evidence-section">
                  <h4> 60 min 联合传感器滑动窗口 (LSTM 证据链)</h4>
                  <div ref="aiEvidenceChart" class="evidence-chart-view"></div>
              </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-primary" @click="flyToSensor(selectedAiAlert.device); closeAiDetail(); forceShowUav = true"> 定位至该区域</button>
            <button class="btn btn-outline" @click="closeAiDetail">关闭研判</button>
          </div>
      </div>
  </div>

  <!-- HT 分级展示：设备精细化交互 (Micro View) -->
  <EquipmentDetailHT 
    v-if="selectedEquipment" 
    :equipment="selectedEquipment" 
    @close="selectedEquipment = null" 
  />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import * as Cesium from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'
import EquipmentDetailHT from './EquipmentDetailHT.vue'

const API_BASE = `http://${window.location.hostname}:8000/api/v1`
const API_AI_BASE = `http://${window.location.hostname}:8001/api/v1`
const API_BIZ_BASE = `http://${window.location.hostname}:8002/api/v1` // 新增核心业务API
const API_VISION_BASE = `http://${window.location.hostname}:8003/api/v1` // 新增无人机智能视觉API

const sensors = ref([])
const aiAlerts = ref([])
const uavFleet = ref([]) // 新增：无人机舰队状态
const alertRecords = ref([])
const miningSummary = ref({
  safety_status: 'green',
  asset_stats: { excavator: {online:0, total:0}, truck: {online:0, total:0}, uav: {online:0, total:0}, crusher: {online:0, total:0} },
  production_today: { current: 0, target: 5000.0, efficiency: 0, material_stock: 0, fuel_stock: 0 },
  recent_alerts: [],
  environment: { wind_speed: 0, visibility: 0, pm25: 0 },
  operation_logs: [],
  cost_metrics: [],
  key_equipment: [],
  material_quality: []
})
const sysStats = ref({ deviceCount: 0, ruleCount: 0 })
const selectedAiAlert = ref(null)
const latestVisionResult = ref(null) // 新增：最近视觉研判结果
const selectedEquipment = ref(null) // 新增：分级展示选中的精细化模型
const aiEvidenceChart = ref(null)
let aiEvidenceChartInstance = null
const forceShowUav = ref(false)
const activeUavCount = computed(() => uavFleet.value.filter(d => d.status !== '待命闲置' && d.status !== '已返航').length)
// 保存从业务后端获取的设备元数据
let deviceRegistry = {}

const loading = ref(true)
const leftSections = ref({ devices: true, logs: true, alerts: true, costs: true })
const activeTab = ref('ai')
let pollingTimer = null

const toggleSection = (name) => {
  leftSections.value[name] = !leftSections.value[name]
  if (name === 'radar' && leftSections.value.radar) {
    nextTick(() => chartRadarInstance?.resize())
  }
}

const switchTab = (tab) => {
  activeTab.value = tab
  nextTick(() => {
    if (tab === 'seismic') chartSeismicInstance?.resize()
    if (tab === 'crack') chartCrackInstance?.resize()
  })
}

const openAiDetail = (alert) => {
  selectedAiAlert.value = alert
  nextTick(() => {
    renderEvidenceChart()
  })
}

const closeAiDetail = () => {
  selectedAiAlert.value = null
  aiEvidenceChartInstance?.dispose()
  aiEvidenceChartInstance = null
}

const getProbColor = (p) => {
  if (p > 80) return '#ff003c'
  if (p > 50) return '#ff9900'
  return '#00f0ff'
}

const getProbLevelClass = (p) => {
  if (p > 80) return 'danger-text'
  if (p > 50) return 'warning-text'
  return 'safe-text'
}

const renderEvidenceChart = () => {
  if (!aiEvidenceChart.value || !selectedAiAlert.value?.evidence) return
  
  if (!aiEvidenceChartInstance) {
    aiEvidenceChartInstance = echarts.init(aiEvidenceChart.value)
  }

  const data = selectedAiAlert.value.evidence
  const features = ['裂缝(mm)', '微震(J)', '倾角(°)', '沉降(mm)']
  const series = features.map((name, i) => ({
    name,
    type: 'line',
    showSymbol: false,
    data: data.map(point => point[i]),
    smooth: true,
    lineStyle: { width: 2 }
  }))

  const option = {
    color: ['#00f0ff', '#00ff88', '#ff9900', '#ff003c'],
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(5, 12, 34, 0.9)', borderColor: '#00f0ff', textStyle: { color: '#fff' } },
    legend: { textStyle: { color: '#8892b0' }, bottom: 0 },
    grid: { top: 40, left: 40, right: 20, bottom: 60 },
    xAxis: { type: 'category', data: Array.from({length: 60}, (_, i) => -60 + i + 'min'), axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: 'white', opacity: 0.05 } } },
    series
  }
  
  aiEvidenceChartInstance.setOption(option)
}

// 界面交互函数
const focusOnCategory = (category) => {
  if(!viewer) return;
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(109.95+Math.random()*0.02, 39.80+Math.random()*0.02, 800),
    duration: 1.5
  })
}

const showLogDetail = (log) => {
  // Can be extended to show modal or fly
  console.log('点击了日志', log)
}

const focusChokepoint = (cp) => {
  if(!viewer) return;
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(109.958, 39.805, 500),
    duration: 1.0,
    orientation: {
      heading: Cesium.Math.toRadians(45.0),
      pitch: Cesium.Math.toRadians(-45.0)
    }
  })
}

// 图表实例
let chartCostInstance = null
let chartYieldInstance = null
const chartCost = ref(null)
const chartYield = ref(null)

// 新仪表盘图表渲染
const renderNewCharts = () => {
  if (chartCost.value && !chartCostInstance) {
    chartCostInstance = echarts.init(chartCost.value);
    chartCostInstance.setOption({
      tooltip: { trigger: 'item' },
      series: [
        {
          name: '成本',
          type: 'pie',
          radius: ['20%', '80%'],
          center: ['50%', '50%'],
          roseType: 'area',
          label: { show: false },
          data: [
            { value: 40, name: '炸药', itemStyle: { color: '#00f0ff' } },
            { value: 38, name: '中保', itemStyle: { color: '#3a86ff' } },
            { value: 32, name: '工资', itemStyle: { color: '#ff9900' } },
            { value: 30, name: '柴油', itemStyle: { color: '#ccd6f6' } },
          ]
        }
      ]
    });
  }
  
  if (chartYield.value && !chartYieldInstance) {
    chartYieldInstance = echarts.init(chartYield.value);
    chartYieldInstance.setOption({
      series: [
        {
          type: 'gauge',
          startAngle: 180,
          endAngle: 0,
          min: 0,
          max: 100,
          splitNumber: 5,
          axisLine: {
            lineStyle: { width: 10, color: [[0.32, '#00f0ff'], [1, 'rgba(0, 240, 255, 0.2)']] }
          },
          pointer: { show: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          detail: {
            valueAnimation: true,
            fontSize: 24,
            offsetCenter: [0, '-10%'],
            color: '#fff',
            formatter: '{value}%'
          },
          data: [{ value: 32 }]
        }
      ]
    });
  }
}


// 三维标签弹窗状态
const selectedSensor = ref(null)
const popupPosition = ref({ x: -1000, y: -1000 })
let selectedEntity = null

const closePopup = () => {
  selectedSensor.value = null
  selectedEntity = null
}

const viewDetailAction = (sensor) => {
  switchTab(sensor.device_type === 'crack_meter' ? 'crack' : 'seismic')
}

// 工具：警报阈值判断
const isAlert = (s) => {
  if (s.device_type === 'crack_meter' && s.crack_width_mm > 10) return true;
  if (s.device_type === 'micro_seismic' && s.energy_level > 100) return true;
  if (s.device_type === 'inclinometer' && s.angle_x > 2) return true;
  if (s.device_type === 'settlement' && s.settlement_mm > 10) return true;
  if (s.device_type === 'water_pressure' && s.pressure_kpa > 200) return true;
  return false;
}

const formatType = (type) => {
  const map = {
    'crack_meter': '边坡裂缝计',
    'micro_seismic': '深部微震仪',
    'inclinometer': '岩体倾角计',
    'settlement': '地表沉降计',
    'water_pressure': '孔隙水压计'
  }
  return map[type] || type
}

// 状态样式映射
const getStatusClass = (status) => {
  if (status === '待命闲置') return 'status-idle'
  if (status === '紧急起飞' || status === '前往目标') return 'status-flying'
  if (status === '抵近侦察中') return 'status-inspecting'
  if (status === '返航中') return 'status-returning'
  return 'status-done'
}

// 抓取业务平台的元数据
const fetchBusinessData = async () => {
  try {
    const config = { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
    
    // 1. 获取汇总概览
    const summaryRes = await axios.get(`${API_BIZ_BASE}/ops/mining-summary`, config)
    miningSummary.value = summaryRes.data
    
    // 2. 更新基础统计
    sysStats.value.deviceCount = Object.values(miningSummary.value.asset_stats).reduce((acc, curr) => acc + curr.total, 0)
    
    // 3. 更新图表与仪表盘
    if (chartYieldInstance) {
      const progress = (miningSummary.value.production_today.current / miningSummary.value.production_today.target) * 100
      chartYieldInstance.setOption({ series: [{ data: [{ value: Math.min(100, progress.toFixed(1)) }] }] })
    }
    
    if (chartCostInstance && miningSummary.value.cost_metrics.length > 0) {
      const pieData = miningSummary.value.cost_metrics.map(c => ({
          value: c.value, name: c.name, itemStyle: { color: c.color }
      }))
      chartCostInstance.setOption({ series: [{ data: pieData }] })
    }

    // 更新设备元数据字典 (保持原有逻辑)
    const devRes = await axios.get(`${API_BIZ_BASE}/devices`, config)
    devRes.data.forEach(d => { deviceRegistry[d.device_id] = d })

  } catch(err) {
    console.warn("未能连接核心业务后台:", err)
  }
}

const formatAssetType = (type) => {
  const map = { 'excavator': '挖掘机', 'truck': '工程大客', 'uav': '巡检无人机', 'crusher': '破碎机系统' }
  return map[type] || type
}
const getAssetColor = (type) => {
  const map = { 'excavator': 'bg-green', 'truck': 'bg-blue', 'uav': 'bg-orange', 'crusher': 'bg-cyan' }
  return map[type] || 'bg-blue'
}
const getAlertLevel = (lvl) => {
  if (lvl === 'danger') return '1'
  if (lvl === 'warning') return '2'
  return '3'
}
const formatLevelName = (lvl) => {
  const map = { 'danger': '一级\n极危', 'warning': '二级\n异常', 'info': '三级\n提示' }
  return map[lvl] || '三级'
}
const formatDateSimple = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth()+1}-${d.getDate()} ${d.getHours()}:${d.getMinutes()}`
}

// 抓取最新实时流数据并与元数据融合
const fetchLatestData = async () => {
  try {
    const res = await axios.get(`${API_BASE}/sensors/latest`)
    if (res.data.status === 'success') {
      // 数据融合：补充经纬度和设备名
      sensors.value = res.data.data.map(s => {
        const meta = deviceRegistry[s.device_id] || {};
        return {
          ...s,
          device_name: meta.device_name || '',
          longitude: meta.longitude,
          latitude: meta.latitude
        }
      });
      loading.value = false
    }
  } catch (err) {
    console.error("API获取失败: ", err)
  }
}

// 抓取 AI 预警日志
const fetchAiAlerts = async () => {
  try {
    const res = await axios.get(`${API_AI_BASE}/ai/alerts`)
    if (res.data.status === 'success') {
      aiAlerts.value = res.data.data
    }
  } catch (err) {
    console.error("AI API获取失败: ", err)
  }
}

// 抓取无人机编队状态
const fetchUavStatus = async () => {
  try {
    const res = await axios.get(`${API_AI_BASE}/drones/status`)
    if (res.data.status === 'success') {
      uavFleet.value = res.data.data
    }
  } catch (err) {
    console.error("无人机状态获取失败: ", err)
  }
}

// 抓取最新视觉分析结果
const fetchLatestVision = async () => {
  try {
    const res = await axios.get(`${API_AI_BASE}/vision/latest`)
    if (res.data.status === 'success') {
      latestVisionResult.value = res.data.data
    }
  } catch (err) {
    console.error("视觉结果获取失败: ", err)
  }
}

// Cesium 初始化与数据点映射
let viewer = null
let entityCollection = {}

const initCesium = () => {
  // 设置 Cesium Ion Access Token (用户已注册)
  Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIxMTExYjQxMy0zZTA1LTRhZTctOTE4Yy03ZTgzZTc1ODA1YmYiLCJpZCI6Mzk2NTMwLCJpYXQiOjE3NzI0MzYwNjN9.VI6BBt8gZF0fXaqdw_KPYwumT-hutwSF4GT3czmam-4';

  viewer = new Cesium.Viewer('cesiumContainer', {
    animation: false,
    timeline: false,
    navigationHelpButton: false,
    baseLayerPicker: false,
    infoBox: false,
    geocoder: false,
    homeButton: false,
    sceneModePicker: false
  });

  // 加载 Cesium Ion 世界地形 (只会按需加载矿区附近的高程数据)
  Cesium.createWorldTerrainAsync().then(terrain => {
    viewer.terrainProvider = terrain;
  }).catch(() => {});
  
  // 隐藏底部的版权信息
  viewer._cesiumWidget._creditContainer.style.display = 'none';

  // 大气层偏蓝科技感
  viewer.scene.skyAtmosphere.hueShift = -0.5;

  // 镜头定位到一个模拟露天矿山坐标 (内蒙古露天矿区附近)
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(109.84, 39.63, 2000),
    orientation: {
      heading: Cesium.Math.toRadians(0.0),
      pitch: Cesium.Math.toRadians(-45.0),
    }
  });

  // 为每个传感器对应的坐标在地球上绘制实体
  sensors.value.forEach((s, idx) => {
    // 优先使用 MySQL 真实的经纬度，如果没有再 fallback
    const lat = s.latitude || (39.635 + (Math.random() - 0.5) * 0.01);
    const lng = s.longitude || (109.840 + (Math.random() - 0.5) * 0.01);
    
    // 渲染传感器指示针
    const isAlerting = isAlert(s)
    const color = isAlerting ? Cesium.Color.RED : Cesium.Color.fromCssColorString('#00f0ff')
    
    const entity = viewer.entities.add({
      id: s.device_id,
      position: Cesium.Cartesian3.fromDegrees(lng, lat, 1400),
      point: {
        pixelSize: 15,
        color: color,
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: 2
      },
      label: {
        text: s.device_id,
        font: '12pt "Orbitron", sans-serif',
        fillColor: color,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        outlineWidth: 2,
        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
        pixelOffset: new Cesium.Cartesian2(0, -10)
      }
    });
    
    entityCollection[s.device_id] = entity;
  });

  // ========== 加载 3D 资产 (以加载示例 3D Tiles 为例) ==========
  try {
    Cesium.createOsmBuildingsAsync().then(buildings => {
      viewer.scene.primitives.add(buildings);
    });
    // 真实项目中这里将加载无人机切片：
    // const tileset = await Cesium.Cesium3DTileset.fromUrl('http://your-server/3dtiles/tileset.json');
    // viewer.scene.primitives.add(tileset);
  } catch(e) { console.warn("3D Tiles 加载跳过", e); }

  // ========== 屏幕点击与数据解算 ==========
  const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
  handler.setInputAction((click) => {
    // 拾取被点击的 3D 对象
    const pickedObject = viewer.scene.pick(click.position);
    if (Cesium.defined(pickedObject) && Cesium.defined(pickedObject.id)) {
      const entityId = pickedObject.id.id; // 获取我们设置的 device_id
      const sensor = sensors.value.find(s => s.device_id === entityId);
      if (sensor) {
        selectedSensor.value = sensor;
        selectedEntity = pickedObject.id;
        // 缩放视角靠近它
        viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(sensor.longitude || 109.840, sensor.latitude || 39.635, 1500),
          duration: 1.5
        });

        // 如果用户点击的是高级设备，可以联动触发 HT 分级展示
        // 这里模拟逻辑：如果是 1#PSZ 或 2#PSZ 这种关键设备，支持进入微观场景
        if (sensor.device_id.includes('PSZ') || sensor.device_id.includes('EAGLE')) {
           // 延迟 1s 进入，等 Cesium 缩放动画完成，体验更好
           setTimeout(() => {
             selectedEquipment.value = {
               id: sensor.device_id,
               name: sensor.device_id === 'UAV-EAGLE-01' ? '先锋级侦察无人机' : '板喂机系统 (1#PSZ)',
               type: sensor.device_id.includes('UAV') ? 'UAV' : 'FIXED'
             };
           }, 1000);
        }
      }
    } else {
      // 点击空白处关闭
      closePopup();
    }
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

  // ========== 帧前渲染监听：动态更新弹窗在屏幕的像素坐标 ==========
  viewer.scene.preRender.addEventListener(() => {
    if (selectedSensor.value && selectedEntity && selectedEntity.position) {
      const positionCartesian3 = selectedEntity.position.getValue(viewer.clock.currentTime);
      if (positionCartesian3) {
        const winPos = Cesium.SceneTransforms.wgs84ToWindowCoordinates(viewer.scene, positionCartesian3);
        if (winPos) {
          // 向上偏移，不遮挡指示针
          popupPosition.value = { x: winPos.x + 15, y: winPos.y - 120 };
        }
      }
    }
  });

}

// 监听数据异动，动态改变 3D 地图上的针脚颜色
watch(sensors, (newSensors) => {
  if(!viewer) return;
  newSensors.forEach(s => {
     if(entityCollection[s.device_id]) {
       const isAlerting = isAlert(s)
       const entity = entityCollection[s.device_id];
       entity.point.color = isAlerting ? Cesium.Color.RED : Cesium.Color.fromCssColorString('#00f0ff')
       entity.label.fillColor = isAlerting ? Cesium.Color.RED : Cesium.Color.fromCssColorString('#00f0ff')
       
       if (isAlerting) {
          // 为了酷炫感，如果报警让点变大
          entity.point.pixelSize = 25;
       } else {
          entity.point.pixelSize = 15;
       }
     }
  })
}, { deep: true })

// 抓取历史数据并渲染图表
const fetchHistoryAndRenderChart = async (deviceId, field, chartInstance, title, color) => {
  try {
    const res = await axios.get(`${API_BASE}/sensors/history/${deviceId}?minutes=60`)
    if (res.data.status === 'success') {
      const data = res.data.data.filter(d => d.field === field)
      
      const times = data.map(d => d.time)
      const values = data.map(d => d.value)
      
      const option = {
        grid: { top: 30, right: 10, bottom: 20, left: 40 },
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(0,0,0,0.7)', textStyle: { color: '#fff' } },
        xAxis: { type: 'category', data: times, axisLine: { lineStyle: { color: '#8892b0' } } },
        yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }, axisLine: { lineStyle: { color: '#8892b0' } } },
        series: [{
          name: title,
          data: values,
          type: 'line',
          smooth: true,
          lineStyle: { color: color, width: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: color },
              { offset: 1, color: 'transparent' }
            ])
          },
          symbol: 'none'
        }]
      };
      
      if(chartInstance) {
          chartInstance.setOption(option)
      }
    }
  } catch (err) {
    console.error(`图表数据获取失败 [${deviceId}]:`, err)
  }
}

onMounted(async () => {
  // 先拉取静态业务数据（必须先拉，以便赋予传感器真实经纬度）
  await fetchBusinessData()
  
  await fetchLatestData()
  await fetchAiAlerts()
  await fetchUavStatus()
  
  await nextTick()
  // 初始化 ECharts
  renderNewCharts()

  // 引入 Cesium
  initCesium()

  // 定时刷新 (真实连通后端)
  pollingTimer = setInterval(() => {
    fetchBusinessData()  // 拉取矿山总览与设备元数据
    fetchLatestData()    // 拉取传感器实时数据
    fetchAiAlerts()      // 拉取AI模型研判结果
    fetchUavStatus()     // 拉取无人机集群状态
    fetchLatestVision()  // 实时无人机视觉流状态
  }, 2000)
})

onUnmounted(() => {
  clearInterval(pollingTimer)
  chartCostInstance?.dispose()
  chartYieldInstance?.dispose()
  if (viewer) {
    viewer.destroy()
  }
})

// ============= 三维深度交互逻辑 (Cinematic Interactions) =============

const envSettings = ref({
  shadows: false,
  fence: true
});

// 飞到全局视角
const flyToGlobal = () => {
  if (!viewer) return;
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(109.84, 39.63, 2000),
    orientation: {
      heading: 0,
      pitch: Cesium.Math.toRadians(-45.0),
    },
    duration: 2.0
  });
};

// 飞到无人机 FPV 追踪视角
const flyToUAV = () => {
  if (!viewer) return;
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(109.845, 39.635, 120),
    orientation: {
      heading: Cesium.Math.toRadians(45.0),
      pitch: Cesium.Math.toRadians(-20.0),
    },
    duration: 2.5
  });
};

// 飞到最高危沉降区
const flyToDanger = () => {
  if (!viewer) return;
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(109.838, 39.628, 50),
    orientation: {
      heading: Cesium.Math.toRadians(-30.0),
      pitch: Cesium.Math.toRadians(-15.0),
    },
    duration: 2.0
  });
};

// 数据反查穿透联动
const flyToSensor = (deviceId) => {
  if (!viewer || !entityCollection[deviceId]) return;
  
  const entity = entityCollection[deviceId];
  viewer.flyTo(entity, {
    duration: 1.5,
    offset: new Cesium.HeadingPitchRange(0, Cesium.Math.toRadians(-30), 80)
  });
  
  // 触发红色特效反馈
  if (entity.point) {
    const origColor = entity.point.color.getValue();
    const origOutline = entity.point.outlineColor.getValue();
    entity.point.color = Cesium.Color.RED;
    entity.point.outlineColor = Cesium.Color.YELLOW;
    entity.point.pixelSize = 25;
    
    setTimeout(() => {
      entity.point.color = origColor;
      entity.point.outlineColor = origOutline;
      entity.point.pixelSize = 15;
    }, 2000);
  }
};

// 环境控制台
const toggleShadows = () => {
  if (!viewer) return;
  viewer.shadows = envSettings.value.shadows;
  if (envSettings.value.shadows) {
    viewer.clock.currentTime = Cesium.JulianDate.fromIso8601("2023-10-01T04:00:00Z");
    viewer.clock.multiplier = 3600;
    viewer.clock.shouldAnimate = true;
  } else {
    viewer.clock.shouldAnimate = false;
  }
};

const toggleFence = () => {
  // 预留：控制电子围栏图层的显隐
};

// =======================================================
</script>

<style scoped>
.app-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
  color: #fff;
  font-family: 'Inter', system-ui, sans-serif;
  position: relative;
}
.app-wrapper::after {
  content: " ";
  display: block;
  position: absolute;
  top: 0; left: 0; bottom: 0; right: 0;
  /* 减轻全屏扫描线的浓度，避免遮挡地球 */
  background: linear-gradient(rgba(0, 0, 0, 0) 50%, rgba(0, 0, 0, 0.05) 50%);
  background-size: 100% 4px;
  z-index: 999;
  pointer-events: none;
}

/* 去除冗余头部的 CSS */

.dashboard-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 320px 1fr;
  grid-template-rows: 1fr 240px;
  grid-template-areas:
    "left main"
    "bottom bottom";
  gap: 10px;
  width: 100%;
  height: 100vh;
  padding: 10px;
  padding-top: 70px; /* 留出 App header 的高度 */
  overflow: hidden;
}

.left-panel {
  grid-area: left;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 自定义左面板滚动条 */
.left-panel::-webkit-scrollbar { width: 4px; }
.left-panel::-webkit-scrollbar-track { background: transparent; }
.left-panel::-webkit-scrollbar-thumb { background: rgba(0,240,255,0.3); border-radius: 2px; }

.main-view {
  grid-area: main;
  position: relative;
  overflow: hidden;
}

.bottom-panel {
  grid-area: bottom;
  display: flex;
  flex-direction: row !important; /* override tech-panel's column */
  overflow: hidden;
}

.panel-header {
  position: relative;
  padding: 1rem;
  border-bottom: 1px solid rgba(0, 240, 255, 0.2);
}

.panel-header h2 {
  font-size: 1.2rem;
  margin: 0;
}

.side-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 折叠区块 */
.collapsible-section {
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid rgba(0, 240, 255, 0.15);
}
.collapsible-section:last-child { border-bottom: none; }

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 1rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}
.section-header:hover { background: rgba(0, 240, 255, 0.05); }
.section-header h2 { font-size: 1rem; margin: 0; }

.collapse-icon {
  color: #00f0ff;
  font-size: 0.8rem;
  transition: transform 0.3s;
}

.section-body {
  overflow-y: auto;
  min-height: 0;
}
.section-body::-webkit-scrollbar { display: none; }

.sensor-list {
  overflow-y: auto;
  padding: 0.5rem 0.8rem;
  max-height: calc(100vh - 380px);
}
.sensor-list::-webkit-scrollbar { display: none; }

/* 气象环境与矿卡调度组件 CSS */
.p-10 { padding: 10px; }
.mt-10 { margin-top: 10px; }
.text-cyan { color: #00f0ff; }

.weather-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.weather-item {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.1);
  padding: 8px;
  border-radius: 4px;
  text-align: center;
}
.w-label {
  display: block;
  font-size: 0.75rem;
  color: #8892b0;
  margin-bottom: 4px;
}
.w-value {
  font-size: 1.1rem;
  color: #fff;
  font-family: 'Orbitron', monospace;
}
.w-value small { font-size: 0.7rem; color: #8892b0; }

.weather-warning {
  margin-top: 10px;
  padding: 8px;
  background: rgba(255, 0, 60, 0.2);
  border: 1px solid #ff003c;
  color: #ff003c;
  border-radius: 4px;
  font-size: 0.8rem;
  text-align: center;
  animation: bg-pulse 1.5s infinite;
}

.truck-stats {
  font-size: 0.85rem;
}
.stat-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  color: #ccd6f6;
}
.truck-progress {
  height: 6px;
  background: rgba(255,255,255,0.1);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}
.truck-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #00ff88, #00f0ff);
  transition: width 1s ease-in-out;
}

.sensor-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  padding: 0.5rem 0.7rem;
  margin-bottom: 0.4rem;
  transition: all 0.3s;
}

.alert-state {
  background: rgba(255, 0, 60, 0.15);
  border: 1px solid rgba(255, 0, 60, 0.4);
  box-shadow: 0 0 15px rgba(255, 0, 60, 0.2);
  animation: pulse-red 2s infinite;
}

@keyframes pulse-red {
  0% { box-shadow: 0 0 0 0 rgba(255, 0, 60, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(255, 0, 60, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 0, 60, 0); }
}

.sensor-title {
  display: flex;
  align-items: center;
  font-family: 'Orbitron', sans-serif;
  font-size: 1.1rem;
  color: #fff;
}

.dot {
  width: 8px; height: 8px; border-radius: 50%; margin-right: 10px;
}
.bg-green { background: #00ff88; box-shadow: 0 0 8px #00ff88; }
.bg-red { background: #ff003c; box-shadow: 0 0 8px #ff003c; }

.sensor-type {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-top: 5px;
}

.sensor-value {
  margin-top: 4px;
  font-size: 1rem;
  color: var(--primary-color);
}
.sensor-value strong { font-size: 1.2rem; }

.sensor-time {
  margin-top: 4px;
  text-align: right;
  font-size: 0.75rem;
  color: #555;
  font-family: monospace;
}

/* 中间主视图 */
.main-view {
  position: relative;
  overflow: hidden;
}

.cesium-placeholder {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: url('https://cesium.com/images/default-image.jpg') center/cover;
}

/* --- 三维标牌弹窗 --- */
.sensor-popup {
  position: absolute;
  width: 250px;
  z-index: 100;
  pointer-events: auto;
  transform: translateY(-50%);
  padding: 12px;
  background: rgba(10, 25, 47, 0.85); /* 继承玻璃态 */
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px dashed rgba(0, 240, 255, 0.3);
  padding-bottom: 8px;
  margin-bottom: 5px;
}

.popup-header h4 { margin: 0; color: #00f0ff; font-family: 'Orbitron', sans-serif;}
.popup-header .close-btn { background: none; border: none; font-size: 1.2rem; color: #8892b0; cursor: pointer; }
.popup-header .close-btn:hover { color: #fff; }

.popup-body p { margin: 5px 0; font-size: 0.85rem; color: #ccd6f6; }
.safe-text { color: #00ff88; font-weight: bold; }

.popup-data {
  background: rgba(0,0,0,0.3);
  padding: 8px;
  border-radius: 4px;
  margin: 10px 0;
  border-left: 2px solid #00f0ff;
}
.popup-data p { margin: 3px 0; display: flex; justify-content: space-between; font-size: 0.8rem;}
.popup-data span { font-weight: bold; color: #fff; }

.btn-detail {
  width: 100%;
  padding: 6px;
  background: rgba(0, 240, 255, 0.15);
  border: 1px solid rgba(0, 240, 255, 0.4);
  color: #00f0ff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.85rem;
}
.btn-detail:hover { background: rgba(0, 240, 255, 0.3); box-shadow: 0 0 10px rgba(0, 240, 255, 0.2); }

/* 给整个主要大屏地图增加一个极隐微的蓝色发光覆盖层，呈现“全息科技感” */
.main-view::before {
  content: ''; position: absolute; top:0; left:0; right:0; bottom:0;
  background: rgba(0, 60, 255, 0.08); /* 深海蓝色的薄纱滤镜 */
  pointer-events: none;
  z-index: 5;
}

.status-overlay {
  position: absolute;
  top: 20px; left: 20px;
  display: flex; gap: 10px;
  z-index: 10;
}

.status-badge {
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid var(--border-neon);
  padding: 5px 12px;
  border-radius: 4px;
  font-size: 0.85rem;
  display: flex; align-items: center;
  backdrop-filter: blur(4px);
}

/* Tab 切换栏 */
.tab-bar {
  display: flex;
  padding: 0 0.8rem;
  gap: 2px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.2);
}

.tab-btn {
  flex: 1;
  padding: 8px 0;
  background: transparent;
  border: none;
  color: #8892b0;
  font-size: 0.85rem;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  font-family: inherit;
}
.tab-btn:hover { color: #00f0ff; }
.tab-btn.active {
  color: #00f0ff;
  border-bottom-color: #00f0ff;
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
}

/* Tab 内容区 */
.tab-content {
  flex: 1;
  padding: 0.8rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.tab-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tab-pane h3 {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 8px;
  padding-left: 10px;
  border-left: 3px solid var(--primary-color);
}

.echart-box {
  flex: 1;
  width: 100%;
  min-height: 0;
}

/* AI 预警区域样式 (Tab 内) */
.ai-title {
  color: #ff9900 !important;
  border-left-color: #ff9900 !important;
}

.ai-alerts-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
  flex: 1;
  padding-right: 5px;
}
.ai-alerts-list::-webkit-scrollbar { display: none; }

.ai-alert-item {
  background: rgba(255, 255, 255, 0.05);
  border-left: 3px solid #00f0ff;
  padding: 8px 10px;
  border-radius: 4px;
  font-size: 0.85rem;
}

.ai-alert-item.level-2 {
  border-left-color: #ffaa00;
  background: rgba(255, 170, 0, 0.1);
}

.ai-alert-item.level-3 {
  border-left-color: #ff003c;
  background: rgba(255, 0, 60, 0.15);
  box-shadow: 0 0 10px rgba(255, 0, 60, 0.2);
}

.alert-time {
  color: #8892b0;
  font-size: 0.75rem;
  margin-bottom: 4px;
}

.alert-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.level-badge {
  background: rgba(255,255,255,0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: bold;
}

.unacked-badge {
  background: rgba(255,0,0,0.5);
  border: 1px solid #ff003c;
  color: #fff;
  animation: bg-pulse 1.5s infinite;
}

.acked-badge {
  background: rgba(0, 255, 136, 0.2);
  border: 1px solid rgba(0, 255, 136, 0.5);
  color: #00ff88;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  border-bottom: 1px dashed rgba(255,255,255,0.1);
  padding-bottom: 4px;
}
.alert-device {
  color: #00f0ff;
  font-family: monospace;
}

@keyframes bg-pulse {
  0%, 100% { filter: brightness(1); }
  50% { filter: brightness(1.5); box-shadow: 0 0 10px rgba(255, 0, 60, 0.5); }
}

.pulse-anim {
  animation: bg-pulse 1s infinite alternate;
}

/* 过渡动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 无人机实时侦察画面 (新增样式) */
.uav-vision-feed {
  position: absolute;
  bottom: 20px;
  left: 320px; /* 避开左侧面板 */
  width: 280px;
  background: rgba(13, 27, 42, 0.85);
  border: 1px solid rgba(0, 240, 255, 0.4);
  border-radius: 8px;
  overflow: hidden;
  z-index: 1000;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
}

.feed-header {
  padding: 8px 12px;
  background: rgba(0, 240, 255, 0.1);
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.2);
}

.live-tag {
  color: #ff003c;
  font-size: 0.75rem;
  font-weight: bold;
  animation: bg-pulse 1.5s infinite;
}

.feed-title {
  font-size: 0.85rem;
  color: #ccd6f6;
  font-weight: 600;
}

.feed-body {
  position: relative;
  height: 180px;
}

.vision-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.vision-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 10px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.overlay-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #8892b0;
}

.overlay-row strong {
  font-family: 'Orbitron', sans-serif;
}

.animate-slide-up {
  animation: slide-up 0.5s ease-out;
}

@keyframes slide-up {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(0, 240, 255, 0.3);
  border-radius: 2px;
}

.tab-badge {
  background-color: #ff003c;
  color: white;
  border-radius: 10px;
  padding: 1px 6px;
  font-size: 0.75rem;
  margin-left: 6px;
  box-shadow: 0 0 5px rgba(255, 0, 60, 0.5);
}

.danger-text { color: #ff003c; }

.alert-action {
  color: #a8b2d1;
  font-style: italic;
}

/* 无人机调度台样式 - 联动化重构 */
.uav-command-center {
  position: absolute;
  bottom: 0px; left: 50%;
  transform: translateX(-50%);
  width: 90%;
  background: rgba(10, 25, 47, 0.9);
  border: 1px solid rgba(0, 240, 255, 0.4);
  backdrop-filter: blur(15px);
  border-radius: 12px 12px 0 0;
  padding: 12px 20px; 
  z-index: 100;
  box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.5);
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
}

.uav-minimized {
  height: 40px;
  width: 300px;
  background: rgba(10, 25, 47, 0.6);
  border-color: rgba(0, 240, 255, 0.2);
  cursor: pointer;
  opacity: 0.7;
}
.uav-minimized:hover {
  opacity: 1;
  background: rgba(10, 25, 47, 0.8);
  border-color: rgba(0, 240, 255, 0.8);
}

.uav-active-mode {
  height: 180px;
  width: 90%;
  border-top-width: 2px;
  border-color: #00f0ff;
  box-shadow: 0 -10px 40px rgba(0, 240, 255, 0.2);
}

.uav-title {
  margin: 0;
  font-size: 1rem;
  color: #00f0ff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding-bottom: 10px;
  border-bottom: 1px dashed rgba(0, 240, 255, 0.2);
}

.uav-minimized .uav-title {
  border-bottom: none;
  padding-bottom: 0;
}

.mini-status-badge {
  font-size: 0.7rem;
  padding: 2px 8px;
  background: rgba(255, 0, 60, 0.2);
  color: #ff003c;
  border: 1px solid #ff003c;
  border-radius: 4px;
  margin-left: 10px;
  animation: breathe 2s infinite;
}
.mini-status-badge.inactive {
  background: rgba(255, 255, 255, 0.05);
  color: #8892b0;
  border-color: rgba(255, 255, 255, 0.1);
  animation: none;
}
.uav-toggle-hint { font-size: 0.8rem; color: #8892b0; margin-left: auto;}

@keyframes breathe {
  0%, 100% { box-shadow: 0 0 5px rgba(255, 0, 60, 0.2); }
  50% { box-shadow: 0 0 15px rgba(255, 0, 60, 0.6); }
}

.uav-fleet-list {
  display: flex;
  justify-content: space-around;
  gap: 15px;
}

.uav-card {
  flex: 1;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 10px;
  border-radius: 6px;
  transition: all 0.3s;
}

.uav-active {
  border-color: #ff003c;
  background: rgba(255, 0, 60, 0.1);
  box-shadow: 0 0 10px rgba(255, 0, 60, 0.2);
}

.uav-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.uav-id { font-family: 'Orbitron', sans-serif; font-weight: bold; color: #fff;}
.uav-type { font-size: 0.8rem; color: #8892b0; }

.uav-state {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.uav-status-badge {
  padding: 3px 6px;
  border-radius: 3px;
  font-weight: bold;
}
.status-idle { background: rgba(255,255,255,0.1); color: #8892b0; }
.status-flying { background: #ff9900; color: #000; animation: blink 1s infinite; }
.status-inspecting { background: #00f0ff; color: #000; box-shadow: 0 0 8px #00f0ff;}
.status-returning { background: #00ff88; color: #000; }
.status-done { background: rgba(255,255,255,0.1); }

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.uav-target { color: #ff003c; font-weight: bold; }

.uav-progress-bar {
  height: 4px;
  background: rgba(255,255,255,0.1);
  margin-top: 10px;
  border-radius: 2px;
  overflow: hidden;
}

.uav-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff003c, #00f0ff);
  transition: width 0.5s linear;
}


/* ========= 新增交互动作 CSS ========= */
.cinematic-pov-controls {
  position: absolute;
  bottom: 120px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 15px;
  padding: 10px 20px;
  z-index: 10;
  border-top: 2px solid rgba(0, 240, 255, 0.4);
}
.pov-btn {
  background: rgba(0, 30, 60, 0.7);
  border: 1px solid #00f0ff;
  color: #fff;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s;
}
.pov-btn:hover {
  background: rgba(0, 240, 255, 0.3);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
}
.pov-btn.danger-btn {
  border-color: #ff003c;
  color: #ff9999;
}
.pov-btn.danger-btn:hover {
  background: rgba(255, 0, 60, 0.3);
  box-shadow: 0 0 10px rgba(255, 0, 60, 0.5);
}

.env-control-panel {
  position: absolute;
  bottom: 110px;
  right: 25px;
  padding: 15px;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 0.9rem;
}
.env-control-panel h4 {
  margin: 0 0 5px 0;
  color: #00f0ff;
  border-bottom: 1px dashed rgba(0,240,255,0.4);
  padding-bottom: 5px;
}
.click-pointer {
  cursor: pointer;
  transition: transform 0.2s, border-left 0.2s;
}
.click-pointer:hover {
  transform: translateX(-5px);
  border-left: 4px solid #00f0ff;
}

/* AI Modal Styles */
.ai-modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(0, 5, 15, 0.85);
  backdrop-filter: blur(8px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ai-modal-content {
  width: 800px;
  max-width: 90%;
  border: 1px solid rgba(0, 240, 255, 0.3);
  padding: 0;
  overflow: hidden;
  box-shadow: 0 0 50px rgba(0, 240, 255, 0.2);
}
.modal-header {
  padding: 15px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(0, 240, 255, 0.05);
}
.modal-header h3 { margin: 0; font-size: 1.2rem; }
.modal-body { padding: 25px; }
.risk-info-grid {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 30px;
  margin-bottom: 25px;
}
.meter-header { display: flex; justify-content: space-between; margin-bottom: 10px; font-weight: bold; }
.meter-track { height: 12px; background: rgba(255,255,255,0.05); border-radius: 6px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); }
.meter-fill { height: 100%; transition: width 1s ease-out; box-shadow: 0 0 15px currentColor; }

.risk-context p { margin: 8px 0; font-size: 0.95rem; color: #8892b0; }
.risk-context strong { color: #fff; }

.evidence-section h4 { 
  margin: 15px 0; 
  font-size: 1rem; 
  color: #00f0ff; 
  border-left: 3px solid #00f0ff; 
  padding-left: 10px; 
}
.evidence-chart-view { height: 350px; width: 100%; }

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid rgba(255,255,255,0.1);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: rgba(255,255,255,0.02);
}

.animate-zoom-in {
  animation: zoomIn 0.3s ease-out;
}
@keyframes zoomIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

.btn-outline {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.3);
  color: #8892b0;
}
.btn-outline:hover {
  background: rgba(255,255,255,0.1);
  color: #fff;
}

/* =======================================================
   New Dashboard Widget Styles (Left & Bottom Panels)
   ======================================================= */
.left-section, .bottom-section {
  display: flex;
  flex-direction: column;
}

.left-section {
  flex: 0 0 auto;
}

.left-section .panel-header {
  padding: 8px 12px;
  border-bottom: none;
}
.left-section .panel-header h2 {
  font-size: 0.85rem;
}
.left-section .section-body {
  padding: 4px 8px;
}

.bottom-section {
  overflow: hidden;
}
.bottom-section .panel-header {
  padding: 6px 12px;
  border-bottom: 1px solid rgba(0,240,255,0.15);
}
.bottom-section .panel-header h2 {
  font-size: 0.8rem;
}

.device-summary .ds-row {
  display: flex;
  align-items: center;
  padding: 5px 10px;
  background: rgba(255, 255, 255, 0.03);
  margin-bottom: 3px;
  border-radius: 4px;
}
.interactive-item {
  cursor: pointer;
  transition: all 0.2s;
}
.interactive-item:hover {
  background: rgba(0, 240, 255, 0.1) !important;
  transform: translateX(4px);
  border-left: 2px solid #00f0ff;
}

.ds-icon {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}
.ds-icon svg { width: 20px; height: 20px; }
.ds-info { flex: 1; font-size: 0.85rem; color: #8892b0; }
.ds-info strong { font-size: 1.1rem; }
.ds-status { font-size: 0.85rem; font-weight: bold; width: 60px; text-align: right; }

.dynamic-log .log-item {
  display: flex;
  gap: 10px;
  padding: 8px 15px;
  font-size: 0.8rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.log-time { color: #8892b0; font-family: monospace; }
.log-event { flex: 1; color: #ccd6f6; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.alert-list .alert-item {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  background: rgba(255, 255, 255, 0.03);
  margin-bottom: 5px;
  border-radius: 4px;
}
.alert-level {
  width: 45px; height: 45px;
  display: flex; align-items: center; justify-content: center;
  text-align: center;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: bold;
  margin-right: 15px;
}
.level-3 { background: rgba(0, 240, 255, 0.2); border: 1px solid #00f0ff; color: #00f0ff; }
.level-2 { background: rgba(255, 170, 0, 0.2); border: 1px solid #ffaa00; color: #ffaa00; }
.level-1 { background: rgba(255, 0, 60, 0.2); border: 1px solid #ff003c; color: #ff003c; }
.alert-content { flex: 1; font-size: 0.8rem; color: #ccd6f6; line-height: 1.4; }
.alert-time { font-size: 0.7rem; color: #8892b0; }

.cost-panel {
  padding: 10px;
}
.cost-legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 0.85rem;
  color: #8892b0;
}
.cl-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.cl-row strong { color: #fff; width: 35px; }

.device-info-panel, .material-quality-panel, .production-panel {
  padding: 5px 10px;
  display: flex;
  flex: 1;
  align-items: center;
}
.device-icon-area {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 70px;
}
.device-list { flex: 1; }
.device-header-row {
  display: flex; font-size: 0.75rem; color: #8892b0; padding: 4px 8px; border-bottom: 1px dashed rgba(255,255,255,0.1);
}
.device-header-row span { flex: 1; text-align: center; }
.device-header-row .spacer { flex: 1; text-align: left; }
.device-row {
  display: flex; align-items: center; padding: 6px 8px; font-size: 0.85rem; color: #ccd6f6; background: rgba(255,255,255,0.02); margin-top: 4px;
}
.device-name { flex: 1; display: flex; align-items: center; }
.device-val { flex: 1; font-family: monospace; text-align: center; font-weight: bold; }

.material-quality-panel { gap: 8px; justify-content: space-around; }
.m-card {
  flex: 1;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.2);
  border-radius: 6px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 8px 5px;
}
.m-val { font-size: 1.2rem; font-family: 'Orbitron', monospace; font-weight: bold; margin-bottom: 3px; }
.m-name { font-size: 0.8rem; color: #ccd6f6; margin-bottom: 5px; }
.m-range { font-size: 0.65rem; color: #8892b0; background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 10px; }
.m-card.warning-card { background: rgba(255, 170, 0, 0.05); border-color: rgba(255, 170, 0, 0.2); }
.m-card.danger-card { background: rgba(255, 0, 60, 0.05); border-color: rgba(255, 0, 60, 0.2); }

.production-panel { align-items: center; gap: 10px; }
.gauge-card { position: relative; flex-shrink: 0; }
.gauge-text-group { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.gauge-info { text-align: left; background: rgba(0, 240, 255, 0.03); padding: 5px 10px; border-radius: 4px;}
.g-title { font-size: 0.95rem; font-family: 'Orbitron', sans-serif; font-weight: bold; color: #fff; display: flex; justify-content: space-between; align-items: center;}
.g-title small { font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #8892b0; font-weight: normal; }
.g-val { margin: 3px 0; }
.g-val svg { width: 100%; height: 20px; }
.g-sub { font-size: 0.65rem; color: #8892b0; text-align: right;}

/* OEE */
.oee-bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 0.8rem; color: #ccd6f6; padding: 4px; border-radius: 4px; transition: background 0.2s; cursor: pointer;}
.oee-bar-row:hover { background: rgba(0, 240, 255, 0.05); }
.oee-label { width: 70px; text-align: left; }
.oee-bar { flex: 1; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.oee-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease;}
.oee-val { width: 40px; text-align: right; font-family: 'Orbitron', sans-serif; font-weight: bold;}

/* Chokepoints */
.chokepoint-row { display: flex; align-items: center; font-size: 0.8rem; padding: 6px 10px; background: rgba(255,255,255,0.02); border-radius: 4px; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.05);}
.chokepoint-row.congested { background: rgba(255, 153, 0, 0.05); box-shadow: inset 0 0 0 1px rgba(255, 153, 0, 0.2); }
.cp-loc { flex: 1.5; color: #fff;}
.cp-wait { flex: 1; color: #8892b0;}
.cp-time { flex: 1; text-align: right; color: #8892b0;}
.cp-wait strong { font-size: 0.95rem; font-family: 'Orbitron', sans-serif;}
.cp-time strong { font-size: 0.95rem; font-family: 'Orbitron', sans-serif; color: #00f0ff;}

.bg-cyan { background-color: #00f0ff; }
.bg-blue { background-color: #3a86ff; }
.bg-green { background-color: #00ff88; }
.bg-orange { background-color: #ff9900; }
.color-green { color: #00ff88; }
.color-orange { color: #ff9900; }
.text-cyan { color: #00f0ff; }
.text-blue { color: #3a86ff; }
.text-orange { color: #ff9900; }
.text-white { color: #ffffff; }
.text-green { color: #00ff88; }
</style>

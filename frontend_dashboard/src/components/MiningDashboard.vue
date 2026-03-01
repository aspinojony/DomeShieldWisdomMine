<template>
  <div class="app-wrapper">
    <div class="dashboard-grid">
      <!-- 左侧监控列表 (折叠式) -->
      <aside class="side-panel tech-panel left-panel">
        <!-- 折叠区块 1：传感器列表 -->
        <div class="collapsible-section">
          <div class="section-header" @click="toggleSection('sensors')">
            <h2 class="glowing-text">📡 实时设备状态</h2>
            <span class="collapse-icon">{{ leftSections.sensors ? '▼' : '▶' }}</span>
          </div>
          <div class="section-body" v-show="leftSections.sensors">
            <div class="sensor-list">
              <div v-if="loading" class="loading-state">数据链路建立中...</div>
              <div 
                v-for="sensor in sensors" 
                :key="sensor.device_id"
                class="sensor-card"
                :class="{'alert-state': isAlert(sensor)}"
              >
                <div class="sensor-title">
                  <span class="dot" :class="isAlert(sensor) ? 'bg-red' : 'bg-green'"></span>
                  {{ sensor.device_id }} 
                  <span style="font-size: 0.8rem; color: #8892b0; margin-left: 8px;">
                    [{{ sensor.device_name || '未命名' }}]
                  </span>
                </div>
                <div class="sensor-type">{{ formatType(sensor.device_type) }}</div>
                <div class="sensor-value">
                  <template v-if="sensor.device_type === 'crack_meter'">
                    裂缝: <strong>{{ sensor.crack_width_mm?.toFixed(2) }}</strong> mm
                  </template>
                  <template v-else-if="sensor.device_type === 'micro_seismic'">
                    能量: <strong>{{ sensor.energy_level?.toFixed(2) }}</strong>
                    频率: <strong>{{ sensor.frequency_hz?.toFixed(1) }}</strong> Hz
                  </template>
                  <template v-else-if="sensor.device_type === 'inclinometer'">
                    X轴倾角: <strong>{{ sensor.angle_x?.toFixed(3) }}</strong> °
                  </template>
                  <template v-else-if="sensor.device_type === 'settlement'">
                    沉降量: <strong>{{ sensor.settlement_mm?.toFixed(2) }}</strong> mm
                  </template>
                  <template v-else-if="sensor.device_type === 'water_pressure'">
                    孔隙水压: <strong>{{ sensor.pressure_kpa?.toFixed(2) }}</strong> KPa
                  </template>
                </div>
                <div class="sensor-time">{{ sensor.last_update?.split(' ')[1] }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 折叠区块 2：雷达图 -->
        <div class="collapsible-section">
          <div class="section-header" @click="toggleSection('radar')">
            <h2 class="glowing-text" style="font-size: 1rem;">🕸 边坡风险雷达</h2>
            <span class="collapse-icon">{{ leftSections.radar ? '▼' : '▶' }}</span>
          </div>
          <div class="section-body" v-show="leftSections.radar">
            <div ref="chartRadar" class="echart-box" style="height: 200px;"></div>
          </div>
        </div>
      </aside>

    <!-- 中央核心视图与底是指控台 -->
    <section class="main-view tech-panel">
      <!-- 移除原有占位遮罩，正式展示 Cesium -->
      <div id="cesiumContainer" class="cesium-placeholder"></div>
      
      <!-- 悬浮状态栏 -->
      <div class="status-overlay">
        <span class="status-badge"><i class="dot bg-green"></i> 注册设备: {{ sysStats.deviceCount }} 台</span>
        <span class="status-badge"><i class="dot bg-green"></i> 告警规则: {{ sysStats.ruleCount }} 条</span>
        <span class="status-badge"><i class="dot bg-green"></i> 无人机云台就绪</span>
      </div>

      <!-- 空天指控中心 (悬浮于底部) -->
      <div class="uav-command-center">
        <h3 class="uav-title">🚀 空天无人机指控集群</h3>
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
              <span class="uav-target" v-if="drone.target">🎯 锁定: {{ drone.target }}</span>
            </div>
            
            <!-- 进度条模拟飞行 -->
            <div class="uav-progress-bar" v-if="drone.status !== '待命闲置' && drone.status !== '已返航'">
               <div class="uav-progress-fill" :style="{ width: drone.progress + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 右侧分析面板 (Tab 切换) -->
    <aside class="side-panel tech-panel right-panel">
      <div class="panel-header">
        <h2 class="glowing-text">关键趋势与AI智判</h2>
      </div>

      <!-- Tab 栏 -->
      <div class="tab-bar">
        <button class="tab-btn" :class="{ active: activeTab === 'ai' }" @click="switchTab('ai')">🧠 AI研判</button>
        <button class="tab-btn" :class="{ active: activeTab === 'seismic' }" @click="switchTab('seismic')">📈 微震</button>
        <button class="tab-btn" :class="{ active: activeTab === 'crack' }" @click="switchTab('crack')">📉 裂缝</button>
      </div>

      <!-- Tab 内容区 -->
      <div class="tab-content">
        <!-- AI 研判 Tab -->
        <div v-show="activeTab === 'ai'" class="tab-pane">
          <h3 class="ai-title">🧠 智能研判预警中心</h3>
          <div class="ai-alerts-list">
            <div v-if="aiAlerts.length === 0" class="loading-state">AI 引擎监控中，暂无异常...</div>
            <div 
              v-for="(alert, index) in aiAlerts" 
              :key="index"
              class="ai-alert-item"
              :class="{'level-3': alert.level.includes('三级'), 'level-2': alert.level.includes('二级')}"
            >
              <div class="alert-time">{{ alert.time.split(' ')[1] }} | {{ alert.device }}</div>
              <div class="alert-info">
                <span>塌方概率: <strong :class="{'danger-text': alert.probability > 80}">{{ alert.probability }}%</strong></span>
                <span class="level-badge">{{ alert.level }}</span>
              </div>
              <div class="alert-action">{{ alert.action }}</div>
            </div>
          </div>
          
          <h3 class="ai-title" style="margin-top: 15px;">🚨 业务阈值预警记录</h3>
          <div class="ai-alerts-list">
            <div v-if="alertRecords.length === 0" class="loading-state">当前无业务阈值告警...</div>
            <div 
              v-for="record in alertRecords" 
              :key="record.id"
              class="ai-alert-item"
              :class="{'level-3': record.alert_level === 'critical', 'level-2': record.alert_level === 'warning'}"
            >
              <div class="alert-time">{{ record.triggered_at ? record.triggered_at.split(' ')[1] : '' }} | {{ record.device_id }}</div>
              <div class="alert-info">
                <span>{{ record.metric_field }}: <strong>{{ parseFloat(record.metric_value).toFixed(2) }}</strong> (阈值: {{ record.threshold }})</span>
                <span class="level-badge" v-if="!record.is_acknowledged" style="background: rgba(255,0,0,0.5); border-color: red;">未处理</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 微震 Tab -->
        <div v-show="activeTab === 'seismic'" class="tab-pane">
          <h3>微震仪异常振幅追踪 [SENSOR-MV-101]</h3>
          <div ref="chartSeismic" class="echart-box"></div>
        </div>

        <!-- 裂缝 Tab -->
        <div v-show="activeTab === 'crack'" class="tab-pane">
          <h3>边坡裂缝扩展演化 [SENSOR-DE-001]</h3>
          <div ref="chartCrack" class="echart-box"></div>
        </div>
      </div>
    </aside>
  </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import * as Cesium from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'

const API_BASE = 'http://127.0.0.1:8000/api/v1'
const API_AI_BASE = 'http://127.0.0.1:8001/api/v1'
const API_BIZ_BASE = 'http://127.0.0.1:8002/api/v1' // 新增核心业务API

const sensors = ref([])
const aiAlerts = ref([])
const uavFleet = ref([]) // 新增：无人机舰队状态
const alertRecords = ref([])
const sysStats = ref({ deviceCount: 0, ruleCount: 0 })
// 保存从业务后端获取的设备元数据
let deviceRegistry = {}

const loading = ref(true)
const leftSections = ref({ sensors: true, radar: true })
const activeTab = ref('ai')
let pollingTimer = null

const toggleSection = (name) => {
  leftSections.value[name] = !leftSections.value[name]
  if (name === 'radar') {
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

// 图表实例
let chartSeismicInstance = null
let chartCrackInstance = null
let chartRadarInstance = null
const chartSeismic = ref(null)
const chartCrack = ref(null)
const chartRadar = ref(null)

// 风险雷达渲染逻辑
const renderRadarChart = () => {
  if (!chartRadarInstance) return;
  const option = {
    radar: {
      indicator: [
        { name: '沉降异常度', max: 100 },
        { name: '微震活动频数', max: 100 },
        { name: '孔隙水压风险', max: 100 },
        { name: '裂缝扩展率', max: 100 },
        { name: '支护应力突变', max: 100 }
      ],
      splitArea: { areaStyle: { color: ['rgba(0, 240, 255, 0.02)', 'rgba(0, 240, 255, 0.05)'] } },
      axisLine: { lineStyle: { color: 'rgba(0, 240, 255, 0.3)' } },
      splitLine: { lineStyle: { color: 'rgba(0, 240, 255, 0.2)' } },
      axisName: { color: '#8892b0', fontSize: 10 }
    },
    series: [{
      type: 'radar',
      data: [{
        value: [
          30 + Math.random() * 20, 
          aiAlerts.value.length > 0 ? 80 : 20, 
          40 + Math.random() * 10, 
          20 + Math.random() * 15, 
          50
        ],
        name: '当前矿区风险画像',
        itemStyle: { color: '#00f0ff' },
        areaStyle: { color: 'rgba(0, 240, 255, 0.3)' },
        lineStyle: { color: '#00f0ff', width: 2 }
      }]
    }]
  };
  chartRadarInstance.setOption(option);
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

// 抓取业务平台的元数据（设备列表、告警规则、系统概况）
const fetchBusinessData = async () => {
  try {
    const [devRes, ruleRes, alertRes] = await Promise.all([
      axios.get(`${API_BIZ_BASE}/devices`),
      axios.get(`${API_BIZ_BASE}/alert-rules`),
      axios.get(`${API_BIZ_BASE}/alert-records?limit=5`)
    ]);
    
    // 建立设备元数据字典
    devRes.data.forEach(d => {
      deviceRegistry[d.device_id] = d;
    });
    
    sysStats.value.deviceCount = devRes.data.length;
    sysStats.value.ruleCount = ruleRes.data.length;
    alertRecords.value = alertRes.data;
  } catch(err) {
    console.warn("未能连接核心业务后台:", err);
  }
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

// Cesium 初始化与数据点映射
let viewer = null
let entityCollection = {}

const initCesium = () => {
  // 设置 Cesium Ion Token (用默认测试环境)
  // 初始化地图底图 (添加一个科技感底图或者直接开启默认)
  viewer = new Cesium.Viewer('cesiumContainer', {
    terrainProvider: async () => {
        try {
           return await Cesium.createWorldTerrainAsync();
        } catch { return undefined;}
    },
    animation: false,
    timeline: false,
    navigationHelpButton: false,
    baseLayerPicker: false,
    infoBox: false,
    geocoder: false,
    homeButton: false,
    sceneModePicker: false
  });
  
  // 隐藏底部的版权信息
  viewer._cesiumWidget._creditContainer.style.display = 'none';

  // 恢复基础地球贴图外观，通过 CSS 给一个幽蓝色的遮罩层
  viewer.scene.skyAtmosphere.hueShift = -0.5; // 轻微偏蓝

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
  if (chartSeismic.value) {
    chartSeismicInstance = echarts.init(chartSeismic.value)
  }
  if (chartCrack.value) {
    chartCrackInstance = echarts.init(chartCrack.value)
  }
  if (chartRadar.value) {
    chartRadarInstance = echarts.init(chartRadar.value)
  }
  
  fetchHistoryAndRenderChart('SENSOR-MV-101', 'energy_level', chartSeismicInstance, '微震能量', '#ff003c')
  fetchHistoryAndRenderChart('SENSOR-DE-001', 'crack_width_mm', chartCrackInstance, '裂缝宽度', '#00f0ff')
  renderRadarChart()

  // 引入 Cesium
  initCesium()

  // 定时刷新 (假装是 Websocket)
  pollingTimer = setInterval(() => {
    fetchBusinessData()  // 拉取告警记录
    fetchLatestData()
    fetchAiAlerts()
    fetchUavStatus()
    fetchHistoryAndRenderChart('SENSOR-MV-101', 'energy_level', chartSeismicInstance, '微震能量', '#ff003c')
    fetchHistoryAndRenderChart('SENSOR-DE-001', 'crack_width_mm', chartCrackInstance, '裂缝宽度', '#00f0ff')
    renderRadarChart()
  }, 2000)
})

onUnmounted(() => {
  clearInterval(pollingTimer)
  chartSeismicInstance?.dispose()
  chartCrackInstance?.dispose()
  if (viewer) {
    viewer.destroy()
  }
})
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
  grid-template-columns: 350px 1fr 400px;
  gap: 1.5rem;
  width: 100%;
  padding: 15px; /* 留出边距 */
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
  overflow: hidden;
}

.sensor-list {
  overflow-y: auto;
  padding: 0.5rem 0.8rem;
  max-height: calc(100vh - 380px);
}
.sensor-list::-webkit-scrollbar { display: none; }

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
  width: 100%; height: 100%;
  position: absolute;
  top: 0; left: 0;
  background: #000;
}

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

.danger-text { color: #ff003c; }

.alert-action {
  color: #a8b2d1;
  font-style: italic;
}

/* 无人机调度台样式 */
.uav-command-center {
  position: absolute;
  bottom: 0px; left: 50%;
  transform: translateX(-50%);
  width: 90%;
  background: rgba(10, 25, 47, 0.85);
  border: 1px solid rgba(0, 240, 255, 0.4);
  backdrop-filter: blur(10px);
  border-radius: 8px 8px 0 0;
  padding: 10px 15px; 
  z-index: 15;
  box-shadow: 0 -5px 20px rgba(0, 240, 255, 0.15);
  max-height: 160px; /* 限制高度防止溢出 */
  overflow: hidden;
}

.uav-title {
  margin: 0 0 10px 0;
  font-size: 1rem;
  color: #00f0ff;
  border-bottom: 1px dashed rgba(0, 240, 255, 0.2);
  padding-bottom: 5px;
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

</style>

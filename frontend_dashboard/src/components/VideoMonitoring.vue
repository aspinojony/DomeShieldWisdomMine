<template>
  <div class="vm-root">
    <!-- Header Bar -->
    <header class="vm-header">
      <div class="vm-header-left">
        <div class="vm-stat-chip">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
          <span class="chip-label">在线</span>
          <span class="chip-val">22</span>
          <span class="chip-sep">/</span>
          <span class="chip-total">24</span>
        </div>
        <div class="vm-stat-chip warn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v2m0 4h.01M5.07 19h13.86c1.54 0 2.5-1.67 1.73-3L13.73 4.99c-.77-1.33-2.69-1.33-3.46 0L3.34 16c-.77 1.33.19 3 1.73 3z"/></svg>
          <span class="chip-label">告警</span>
          <span class="chip-val">3</span>
        </div>
        <div class="vm-stat-chip ok">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          <span class="chip-label">已处理</span>
          <span class="chip-val">1222</span>
        </div>
      </div>
      <div class="vm-header-center">
        <h1>视频监控中心</h1>
        <span class="vm-subtitle">穹盾智矿 · 工业视频智能管理</span>
      </div>
      <div class="vm-header-right">
        <span class="vm-clock">{{ clock }}</span>
        <div class="vm-rec-badge" :class="{ blink: true }">
          <span class="rec-dot"></span> REC
        </div>
      </div>
    </header>

    <main class="vm-body">
      <!-- Left: Charts -->
      <aside class="vm-sidebar">
        <div class="vm-panel">
          <div class="vm-panel-head">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
            高发区域统计
          </div>
          <div ref="chartBar" class="vm-chart"></div>
        </div>
        <div class="vm-panel">
          <div class="vm-panel-head">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            风险趋势 (近7日)
          </div>
          <div ref="chartLine" class="vm-chart"></div>
        </div>
        <div class="vm-panel">
          <div class="vm-panel-head">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0110 10"/><path d="M12 2a10 10 0 00-6.83 17.13"/></svg>
            告警分类
          </div>
          <div ref="chartDonut" class="vm-chart"></div>
        </div>
      </aside>

      <!-- Center: Video Grid -->
      <section class="vm-center">
        <div class="vm-toolbar">
          <div class="vm-grid-btns">
            <button :class="{ active: gridLayout === 1 }" @click="gridLayout = 1" title="单画面">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="1"/></svg>
            </button>
            <button :class="{ active: gridLayout === 4 }" @click="gridLayout = 4" title="四画面">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/><rect x="13" y="13" width="8" height="8" rx="1"/></svg>
            </button>
            <button :class="{ active: gridLayout === 9 }" @click="gridLayout = 9" title="九画面">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="5" height="5" rx="0.5"/><rect x="9.5" y="3" width="5" height="5" rx="0.5"/><rect x="16" y="3" width="5" height="5" rx="0.5"/><rect x="3" y="9.5" width="5" height="5" rx="0.5"/><rect x="9.5" y="9.5" width="5" height="5" rx="0.5"/><rect x="16" y="9.5" width="5" height="5" rx="0.5"/><rect x="3" y="16" width="5" height="5" rx="0.5"/><rect x="9.5" y="16" width="5" height="5" rx="0.5"/><rect x="16" y="16" width="5" height="5" rx="0.5"/></svg>
            </button>
          </div>
          <div class="vm-toolbar-actions">
            <button @click="triggerReport" title="截图告警">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>
              抓拍
            </button>
            <button title="全屏播放">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/></svg>
              全屏
            </button>
          </div>
        </div>

        <div class="vm-grid" :class="'g-' + gridLayout">
          <div v-for="(cam, idx) in visibleCams" :key="cam.id"
            class="vm-cell"
            :class="{ selected: selectedCam === idx }"
            @click="selectedCam = idx">
            <!-- OSD overlay top -->
            <div class="cell-osd-top">
              <span class="osd-id">{{ cam.ch }}</span>
              <span class="osd-name">{{ cam.name }}</span>
              <span class="osd-rec" v-if="cam.online"><span class="rec-indicator"></span>REC</span>
              <span class="osd-offline" v-else>离线</span>
            </div>
            <img :src="cam.src" :alt="cam.name" class="cell-feed" loading="lazy">
            <!-- OSD overlay bottom -->
            <div class="cell-osd-bottom">
              <span class="osd-ts">{{ cam.ts }}</span>
              <span class="osd-res">{{ cam.res }}</span>
            </div>
            <!-- Corner brackets -->
            <div class="cell-corners">
              <i class="c-tl"></i><i class="c-tr"></i><i class="c-bl"></i><i class="c-br"></i>
            </div>
          </div>
        </div>
      </section>

      <!-- Right: Alert Feed -->
      <aside class="vm-sidebar vm-sidebar-right">
        <div class="vm-panel vm-panel-grow">
          <div class="vm-panel-head alert-head">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"/></svg>
            AI 实时告警
            <span class="alert-count">{{ aiAlerts.length }}</span>
          </div>
          <div class="vm-alert-list">
            <div v-for="a in aiAlerts" :key="a.id" class="vm-alert-item" :class="'level-' + a.level">
              <div class="alert-img-wrap">
                <img :src="a.thumb" alt="">
                <span class="alert-level-tag">{{ a.levelText }}</span>
              </div>
              <div class="alert-body">
                <div class="alert-title">{{ a.type }}</div>
                <div class="alert-meta">
                  <span>{{ a.location }}</span>
                  <span>{{ a.time }}</span>
                </div>
                <div class="alert-actions">
                  <button class="btn-sm btn-process">处理</button>
                  <button class="btn-sm btn-ignore">忽略</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- PTZ Control Mini Panel -->
        <div class="vm-panel vm-ptz">
          <div class="vm-panel-head">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v4m0 12v4m10-10h-4M6 12H2m15.07-7.07l-2.83 2.83M9.76 14.24l-2.83 2.83m0-10.14l2.83 2.83m4.48 4.48l2.83 2.83"/></svg>
            云台控制
          </div>
          <div class="ptz-grid">
            <button class="ptz-btn" @click="ptzMove('up')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
            </button>
            <button class="ptz-btn" @click="ptzMove('left')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
            </button>
            <button class="ptz-btn ptz-home" @click="ptzMove('home')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
            <button class="ptz-btn" @click="ptzMove('right')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </button>
            <button class="ptz-btn" @click="ptzMove('down')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>
            </button>
            <div class="ptz-zoom">
              <button @click="ptzZoom('in')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              </button>
              <span>变焦</span>
              <button @click="ptzZoom('out')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              </button>
            </div>
          </div>
        </div>
      </aside>
    </main>

    <!-- Modal -->
    <Transition name="modal">
      <div v-if="showModal" class="vm-modal-overlay" @click.self="showModal = false">
        <div class="vm-modal">
          <div class="vm-modal-header">
            <h3>视频抓拍上报</h3>
            <button class="modal-close" @click="showModal = false">&times;</button>
          </div>
          <div class="vm-modal-body">
            <div class="modal-preview">
              <img :src="visibleCams[selectedCam]?.src || '/images/cctv/shaft.png'" alt="">
              <div class="preview-osd">{{ visibleCams[selectedCam]?.ch }} · {{ visibleCams[selectedCam]?.name }}</div>
            </div>
            <div class="modal-form">
              <div class="form-row">
                <label>抓拍时间</label>
                <input type="text" :value="clock" disabled>
              </div>
              <div class="form-row">
                <label>告警类型</label>
                <select v-model="form.type">
                  <option value="">请选择</option>
                  <option>违规作业</option><option>区域侵入</option><option>设备故障</option><option>未佩戴安全帽</option>
                </select>
              </div>
              <div class="form-row">
                <label>告警等级</label>
                <select v-model="form.level">
                  <option value="blue">蓝色·一般</option><option value="yellow">黄色·注意</option>
                  <option value="orange">橙色·严重</option><option value="red">红色·紧急</option>
                </select>
              </div>
              <div class="form-row">
                <label>发生位置</label>
                <select v-model="form.location">
                  <option>主井口</option><option>皮带廊道</option><option>炸药库</option><option>选矿厂</option><option>泵站</option><option>提升机房</option>
                </select>
              </div>
              <div class="form-row full">
                <label>情况描述</label>
                <textarea v-model="form.desc" rows="3" placeholder="描述现场情况..."></textarea>
              </div>
              <div class="form-btns">
                <button class="btn-cancel" @click="showModal = false">取消</button>
                <button class="btn-submit" @click="submitReport">确认上报</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Bottom Nav -->
    <nav class="vm-nav">
      <button class="vm-nav-btn active">视频智能检测</button>
      <button class="vm-nav-btn">人工远程巡查</button>
      <button class="vm-nav-btn" @click="$router.push('/')">返回总览</button>
    </nav>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts'

// --- State ---
const gridLayout = ref(4)
const selectedCam = ref(0)
const showModal = ref(false)
const clock = ref('')
const form = ref({ type: '', level: 'orange', location: '主井口', desc: '' })

// Camera data - realistic
const allCams = [
  { id: 1, ch: 'CH01', name: '主井口',   src: '/images/cctv/shaft.png',     ts: '2026-03-05 20:15:42', res: '1920×1080', online: true },
  { id: 2, ch: 'CH02', name: '皮带廊道', src: '/images/cctv/conveyor.png',   ts: '2026-03-05 20:16:08', res: '1920×1080', online: true },
  { id: 3, ch: 'CH03', name: '炸药库外围', src: '/images/cctv/explosive.png', ts: '2026-03-05 20:17:23', res: '2560×1440', online: true },
  { id: 4, ch: 'CH04', name: '选矿厂',   src: '/images/cctv/plant.png',      ts: '2026-03-05 20:18:55', res: '1920×1080', online: true },
  { id: 5, ch: 'CH05', name: '井下泵站', src: '/images/cctv/pump.png',       ts: '2026-03-05 20:19:30', res: '1280×720',  online: true },
  { id: 6, ch: 'CH06', name: '提升机房', src: '/images/cctv/hoist.png',      ts: '2026-03-05 20:20:12', res: '1920×1080', online: true },
  { id: 7, ch: 'CH07', name: '副井台口', src: '/images/cctv/entrance.png',   ts: '2026-03-05 20:21:45', res: '1920×1080', online: true },
  { id: 8, ch: 'CH08', name: '露天采场', src: '/images/cctv/pit.png',        ts: '2026-03-05 20:22:01', res: '2560×1440', online: true },
  { id: 9, ch: 'CH09', name: '尾矿库',  src: '/images/cctv/shaft.png',      ts: '2026-03-05 20:23:18', res: '1920×1080', online: false },
]

const visibleCams = computed(() => allCams.slice(0, gridLayout.value))

const aiAlerts = [
  { id: 1, type: '未佩戴安全帽', time: '20:10:32', location: 'CH01 主井口', thumb: '/images/cctv/shaft.png', level: 'orange', levelText: '橙色' },
  { id: 2, type: '非法进入禁区', time: '20:08:15', location: 'CH03 炸药库', thumb: '/images/cctv/explosive.png', level: 'red', levelText: '红色' },
  { id: 3, type: '皮带跑偏检测', time: '20:05:44', location: 'CH02 廊道', thumb: '/images/cctv/conveyor.png', level: 'yellow', levelText: '黄色' },
  { id: 4, type: '离岗超时预警', time: '19:58:20', location: 'CH06 提升机房', thumb: '/images/cctv/hoist.png', level: 'blue', levelText: '蓝色' },
  { id: 5, type: '运输车辆超速', time: '19:45:11', location: 'CH08 采场', thumb: '/images/cctv/pit.png', level: 'orange', levelText: '橙色' },
]

// Clock
let clockTimer
onMounted(() => {
  const tick = () => { clock.value = new Date().toLocaleString('zh-CN', { hour12: false }) }
  tick()
  clockTimer = setInterval(tick, 1000)
})

const triggerReport = () => { showModal.value = true }
const submitReport = () => { alert('告警已上报至调度指挥中心'); showModal.value = false }
const ptzMove = (dir) => { console.log('PTZ:', dir) }
const ptzZoom = (dir) => { console.log('Zoom:', dir) }

// --- Charts ---
const chartBar = ref(null)
const chartLine = ref(null)
const chartDonut = ref(null)

onMounted(() => {
  // Bar
  const bChart = echarts.init(chartBar.value)
  bChart.setOption({
    grid: { left: '15%', right: '8%', bottom: '18%', top: '12%' },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(30,41,59,0.95)', borderColor: '#334155', textStyle: { color: '#e2e8f0', fontSize: 12 } },
    xAxis: { type: 'category', data: ['主井口', '皮带廊', '选矿厂', '泵站', '提升机', '炸药库'], axisLabel: { color: '#94a3b8', fontSize: 10, rotate: 20 }, axisLine: { lineStyle: { color: '#334155' } } },
    yAxis: { type: 'value', name: '次', nameTextStyle: { color: '#64748b', fontSize: 10 }, splitLine: { lineStyle: { color: '#1e293b' } }, axisLabel: { color: '#64748b', fontSize: 10 } },
    series: [{ data: [142, 231, 198, 87, 165, 53], type: 'bar', barWidth: '50%',
      itemStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#3b82f6'},{offset:1,color:'#1e40af'}]), borderRadius: [3,3,0,0] }
    }]
  })

  // Line
  const lChart = echarts.init(chartLine.value)
  lChart.setOption({
    grid: { left: '12%', right: '8%', bottom: '18%', top: '15%' },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(30,41,59,0.95)', borderColor: '#334155', textStyle: { color: '#e2e8f0', fontSize: 12 } },
    legend: { data: ['告警数', '已处理'], textStyle: { color: '#94a3b8', fontSize: 10 }, top: 0, right: 10, itemWidth: 12, itemHeight: 8 },
    xAxis: { type: 'category', data: ['02-27','02-28','03-01','03-02','03-03','03-04','03-05'],
      axisLabel: { color: '#94a3b8', fontSize: 10 }, axisLine: { lineStyle: { color: '#334155' } } },
    yAxis: { type: 'value', name: '件', nameTextStyle: { color: '#64748b', fontSize: 10 }, splitLine: { lineStyle: { color: '#1e293b' } }, axisLabel: { color: '#64748b', fontSize: 10 } },
    series: [
      { name: '告警数', data: [18,24,15,31,22,19,26], type: 'line', smooth: true, symbol: 'circle', symbolSize: 5,
        itemStyle: { color: '#f59e0b' }, lineStyle: { width: 2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(245,158,11,0.15)'},{offset:1,color:'rgba(245,158,11,0)'}]) } },
      { name: '已处理', data: [17,22,15,28,21,19,23], type: 'line', smooth: true, symbol: 'circle', symbolSize: 5,
        itemStyle: { color: '#22c55e' }, lineStyle: { width: 2, type: 'dashed' } }
    ]
  })

  // Donut
  const dChart = echarts.init(chartDonut.value)
  dChart.setOption({
    tooltip: { trigger: 'item', backgroundColor: 'rgba(30,41,59,0.95)', borderColor: '#334155', textStyle: { color: '#e2e8f0', fontSize: 12 } },
    legend: { orient: 'vertical', right: 5, top: 'center', textStyle: { color: '#94a3b8', fontSize: 10 }, itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie', radius: ['45%', '72%'], center: ['35%', '50%'],
      label: { show: false }, labelLine: { show: false },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' } },
      data: [
        { value: 412, name: '未戴安全帽', itemStyle: { color: '#f59e0b' } },
        { value: 287, name: '区域侵入',   itemStyle: { color: '#ef4444' } },
        { value: 198, name: '车辆违规',   itemStyle: { color: '#3b82f6' } },
        { value: 156, name: '离岗检测',   itemStyle: { color: '#8b5cf6' } },
        { value: 89,  name: '设备异常',   itemStyle: { color: '#06b6d4' } },
      ]
    }]
  })
})
</script>

<style scoped>
/* ===================== ROOT ===================== */
.vm-root {
  height: 100vh;
  background: #0c1222;
  color: #cbd5e1;
  display: flex;
  flex-direction: column;
  padding: 12px 16px;
  gap: 10px;
  overflow: hidden;
  font-family: -apple-system, 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif;
  padding-top: 58px;
}

/* ===================== HEADER ===================== */
.vm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: rgba(15,23,42,0.7);
  border: 1px solid #1e293b;
  border-radius: 8px;
  flex-shrink: 0;
}

.vm-header-left { display: flex; gap: 14px; align-items: center; }
.vm-header-center { text-align: center; }
.vm-header-center h1 {
  font-size: 18px;
  font-weight: 700;
  color: #e2e8f0;
  letter-spacing: 2px;
  margin: 0;
}
.vm-subtitle { font-size: 11px; color: #64748b; letter-spacing: 1px; }
.vm-header-right { display: flex; gap: 16px; align-items: center; }

.vm-stat-chip {
  display: flex; align-items: center; gap: 6px;
  background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.2);
  padding: 5px 12px; border-radius: 6px; font-size: 12px;
}
.vm-stat-chip svg { color: #3b82f6; }
.chip-label { color: #64748b; }
.chip-val { font-weight: 700; color: #e2e8f0; font-family: 'SF Mono', 'JetBrains Mono', monospace; }
.chip-sep { color: #475569; }
.chip-total { color: #64748b; font-family: 'SF Mono', 'JetBrains Mono', monospace; }
.vm-stat-chip.warn { background: rgba(245,158,11,0.08); border-color: rgba(245,158,11,0.25); }
.vm-stat-chip.warn svg { color: #f59e0b; }
.vm-stat-chip.warn .chip-val { color: #f59e0b; }
.vm-stat-chip.ok { background: rgba(34,197,94,0.08); border-color: rgba(34,197,94,0.2); }
.vm-stat-chip.ok svg { color: #22c55e; }

.vm-clock {
  font-family: 'SF Mono', 'JetBrains Mono', monospace;
  font-size: 13px; color: #94a3b8; letter-spacing: 0.5px;
}
.vm-rec-badge {
  display: flex; align-items: center; gap: 5px;
  font-size: 11px; font-weight: 700; color: #ef4444;
  background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25);
  padding: 3px 10px; border-radius: 4px;
}
.rec-dot { width: 7px; height: 7px; background: #ef4444; border-radius: 50%; }
.vm-rec-badge.blink .rec-dot { animation: blink 1.2s infinite; }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.2; } }

/* ===================== BODY GRID ===================== */
.vm-body {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr 300px;
  gap: 10px;
  min-height: 0;
}

/* ===================== SIDEBAR ===================== */
.vm-sidebar { display: flex; flex-direction: column; gap: 10px; min-height: 0; }
.vm-sidebar-right { }

.vm-panel {
  background: rgba(15,23,42,0.6);
  border: 1px solid #1e293b;
  border-radius: 8px;
  display: flex; flex-direction: column;
  min-height: 0;
  flex: 1;
}
.vm-panel-grow { flex: 2; }

.vm-panel-head {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px;
  font-size: 13px; font-weight: 600; color: #e2e8f0;
  border-bottom: 1px solid #1e293b;
  flex-shrink: 0;
}
.vm-panel-head svg { color: #3b82f6; flex-shrink: 0; }

.vm-chart { flex: 1; min-height: 120px; }

/* ===================== CENTER VIDEO ===================== */
.vm-center { display: flex; flex-direction: column; gap: 8px; min-height: 0; }

.vm-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 12px;
  background: rgba(15,23,42,0.6);
  border: 1px solid #1e293b;
  border-radius: 8px;
  flex-shrink: 0;
}

.vm-grid-btns { display: flex; gap: 4px; }
.vm-grid-btns button {
  background: transparent; border: 1px solid transparent; color: #64748b;
  padding: 5px 8px; cursor: pointer; border-radius: 4px; transition: all 0.2s;
  display: flex; align-items: center;
}
.vm-grid-btns button:hover { color: #94a3b8; background: rgba(255,255,255,0.03); }
.vm-grid-btns button.active { color: #3b82f6; border-color: rgba(59,130,246,0.3); background: rgba(59,130,246,0.08); }

.vm-toolbar-actions { display: flex; gap: 6px; }
.vm-toolbar-actions button {
  display: flex; align-items: center; gap: 5px;
  background: transparent; border: 1px solid #1e293b; color: #94a3b8;
  padding: 5px 12px; border-radius: 5px; font-size: 12px; cursor: pointer; transition: all 0.2s;
}
.vm-toolbar-actions button:hover { border-color: #334155; color: #e2e8f0; background: rgba(255,255,255,0.03); }

/* Grid Layouts */
.vm-grid {
  flex: 1; display: grid; gap: 4px;
  background: #0a0f1a;
  border: 1px solid #1e293b;
  border-radius: 8px;
  padding: 4px;
  min-height: 0;
}
.g-1 { grid-template-columns: 1fr; }
.g-4 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }
.g-9 { grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr); }

.vm-cell {
  position: relative; overflow: hidden;
  background: #080c16;
  border: 1px solid #1e293b;
  border-radius: 4px;
  cursor: pointer;
  transition: border-color 0.2s;
}
.vm-cell:hover { border-color: #334155; }
.vm-cell.selected { border-color: #3b82f6; box-shadow: 0 0 0 1px rgba(59,130,246,0.3); }

.cell-feed { width: 100%; height: 100%; object-fit: cover; display: block; filter: saturate(0.85) brightness(0.92); }

/* OSD Overlays - professional monospaced */
.cell-osd-top, .cell-osd-bottom {
  position: absolute; left: 0; right: 0;
  display: flex; justify-content: space-between; align-items: center;
  padding: 5px 8px;
  font-family: 'SF Mono', 'JetBrains Mono', 'Courier New', monospace;
  font-size: 10px; letter-spacing: 0.3px;
  pointer-events: none; z-index: 5;
}
.cell-osd-top { top: 0; background: linear-gradient(180deg, rgba(0,0,0,0.65) 0%, transparent 100%); }
.cell-osd-bottom { bottom: 0; background: linear-gradient(0deg, rgba(0,0,0,0.65) 0%, transparent 100%); }

.osd-id { color: #94a3b8; font-weight: 600; }
.osd-name { color: #e2e8f0; flex: 1; margin-left: 6px; }
.osd-rec { color: #ef4444; font-weight: 700; display: flex; align-items: center; gap: 4px; }
.rec-indicator { width: 5px; height: 5px; background: #ef4444; border-radius: 50%; animation: blink 1s infinite; }
.osd-offline { color: #64748b; font-style: italic; }
.osd-ts { color: #94a3b8; }
.osd-res { color: #64748b; }

/* Corner brackets */
.cell-corners i { position: absolute; width: 12px; height: 12px; border-color: #475569; border-style: solid; border-width: 0; }
.c-tl { top: 0; left: 0; border-top-width: 2px; border-left-width: 2px; }
.c-tr { top: 0; right: 0; border-top-width: 2px; border-right-width: 2px; }
.c-bl { bottom: 0; left: 0; border-bottom-width: 2px; border-left-width: 2px; }
.c-br { bottom: 0; right: 0; border-bottom-width: 2px; border-right-width: 2px; }

/* ===================== ALERTS ===================== */
.alert-head { position: relative; }
.alert-count {
  margin-left: auto;
  background: rgba(239,68,68,0.15); color: #ef4444;
  font-size: 11px; font-weight: 700;
  padding: 1px 8px; border-radius: 10px;
}

.vm-alert-list { flex: 1; overflow-y: auto; padding: 8px; }
.vm-alert-list::-webkit-scrollbar { width: 4px; }
.vm-alert-list::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }

.vm-alert-item {
  display: flex; gap: 10px; padding: 10px;
  background: rgba(255,255,255,0.015);
  border: 1px solid #1e293b;
  border-radius: 6px;
  margin-bottom: 8px;
  transition: background 0.2s, border-color 0.2s;
  cursor: pointer;
}
.vm-alert-item:hover { background: rgba(255,255,255,0.03); border-color: #334155; }
.vm-alert-item.level-red { border-left: 3px solid #ef4444; }
.vm-alert-item.level-orange { border-left: 3px solid #f59e0b; }
.vm-alert-item.level-yellow { border-left: 3px solid #eab308; }
.vm-alert-item.level-blue { border-left: 3px solid #3b82f6; }

.alert-img-wrap { position: relative; width: 80px; height: 56px; border-radius: 4px; overflow: hidden; flex-shrink: 0; }
.alert-img-wrap img { width: 100%; height: 100%; object-fit: cover; filter: saturate(0.8); }
.alert-level-tag {
  position: absolute; bottom: 2px; left: 2px;
  font-size: 9px; font-weight: 600; padding: 1px 5px; border-radius: 2px;
  background: rgba(0,0,0,0.7); color: #e2e8f0;
}

.alert-body { flex: 1; min-width: 0; }
.alert-title { font-size: 12px; font-weight: 600; color: #e2e8f0; margin-bottom: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.alert-meta { display: flex; gap: 10px; font-size: 10px; color: #64748b; margin-bottom: 6px; }
.alert-actions { display: flex; gap: 6px; }
.btn-sm {
  font-size: 10px; padding: 2px 10px; border-radius: 3px; cursor: pointer;
  border: 1px solid #1e293b; background: transparent; color: #94a3b8; transition: all 0.2s;
}
.btn-sm:hover { border-color: #334155; color: #e2e8f0; }
.btn-process { border-color: rgba(59,130,246,0.3); color: #3b82f6; }
.btn-process:hover { background: rgba(59,130,246,0.1); }
.btn-ignore:hover { background: rgba(255,255,255,0.03); }

/* ===================== PTZ ===================== */
.vm-ptz { flex: 0 0 auto; }
.ptz-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 4px; padding: 10px;
  justify-items: center;
}
.ptz-btn {
  width: 36px; height: 36px; border-radius: 50%;
  background: rgba(255,255,255,0.03); border: 1px solid #1e293b;
  color: #94a3b8; font-size: 12px; cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; justify-content: center;
}
.ptz-btn:hover { background: rgba(59,130,246,0.1); border-color: #3b82f6; color: #e2e8f0; }
.ptz-home { background: rgba(59,130,246,0.08); border-color: rgba(59,130,246,0.3); color: #3b82f6; }
.ptz-zoom {
  grid-column: 1 / -1;
  display: flex; align-items: center; gap: 10px;
  margin-top: 4px;
}
.ptz-zoom span { font-size: 11px; color: #64748b; }
.ptz-zoom button {
  width: 30px; height: 24px; border-radius: 4px;
  background: transparent; border: 1px solid #1e293b; color: #94a3b8;
  font-size: 14px; cursor: pointer; transition: all 0.2s;
}
.ptz-zoom button:hover { border-color: #3b82f6; color: #3b82f6; }

/* ===================== MODAL ===================== */
.vm-modal-overlay {
  position: fixed; inset: 0; z-index: 2000;
  background: rgba(0,0,0,0.7); backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
}
.vm-modal {
  width: 800px; max-width: 90vw;
  background: #0f172a; border: 1px solid #1e293b; border-radius: 10px;
  overflow: hidden;
}
.vm-modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 20px; border-bottom: 1px solid #1e293b;
}
.vm-modal-header h3 { font-size: 16px; font-weight: 600; color: #e2e8f0; margin: 0; }
.modal-close { background: none; border: none; color: #64748b; font-size: 22px; cursor: pointer; padding: 0 4px; }
.modal-close:hover { color: #e2e8f0; }

.vm-modal-body { display: grid; grid-template-columns: 360px 1fr; gap: 20px; padding: 20px; }
.modal-preview { position: relative; border-radius: 6px; overflow: hidden; border: 1px solid #1e293b; }
.modal-preview img { width: 100%; display: block; }
.preview-osd {
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: 6px 10px;
  background: rgba(0,0,0,0.7);
  font-family: 'SF Mono', monospace; font-size: 11px; color: #94a3b8;
}

.modal-form { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-content: start; }
.form-row { display: flex; flex-direction: column; gap: 4px; }
.form-row.full { grid-column: span 2; }
.form-row label { font-size: 11px; color: #64748b; }
.form-row input, .form-row select, .form-row textarea {
  background: #1e293b; border: 1px solid #334155; color: #e2e8f0;
  padding: 7px 10px; border-radius: 5px; font-size: 13px; font-family: inherit;
  outline: none; transition: border-color 0.2s;
}
.form-row input:focus, .form-row select:focus, .form-row textarea:focus { border-color: #3b82f6; }
.form-row textarea { resize: none; }
.form-btns { grid-column: span 2; display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.btn-cancel {
  background: transparent; border: 1px solid #334155; color: #94a3b8;
  padding: 7px 24px; border-radius: 5px; cursor: pointer; font-size: 13px; transition: all 0.2s;
}
.btn-cancel:hover { border-color: #475569; color: #e2e8f0; }
.btn-submit {
  background: #3b82f6; border: none; color: #fff;
  padding: 7px 28px; border-radius: 5px; font-weight: 600; cursor: pointer; font-size: 13px; transition: background 0.2s;
}
.btn-submit:hover { background: #2563eb; }

/* Modal Transition */
.modal-enter-active, .modal-leave-active { transition: opacity 0.25s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-active .vm-modal { animation: slideUp 0.3s ease-out; }
@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

/* ===================== NAV ===================== */
.vm-nav {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 4px;
  background: rgba(15,23,42,0.85); backdrop-filter: blur(12px);
  border: 1px solid #1e293b; border-radius: 8px;
  padding: 5px; z-index: 100;
}
.vm-nav-btn {
  background: transparent; border: none; color: #64748b;
  padding: 8px 22px; border-radius: 5px; font-size: 13px;
  font-weight: 500; cursor: pointer; transition: all 0.2s;
}
.vm-nav-btn:hover { color: #94a3b8; background: rgba(255,255,255,0.03); }
.vm-nav-btn.active { background: #3b82f6; color: #fff; }
</style>

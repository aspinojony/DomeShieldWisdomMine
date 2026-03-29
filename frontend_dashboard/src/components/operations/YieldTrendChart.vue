<template>
  <div>
    <div class="panel-header-cyber">
      <div style="display:flex; align-items:center;">
         <div class="title-deco"></div>
         <span class="glowing-text">实时生产折线</span>
      </div>
      <div class="panel-id">REF://PRD-004</div>
    </div>
    <div class="panel-inner">
      <div class="chart-box-enhanced" ref="trendChartRef"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { useOperationsStore } from '../../store/operations'

const store = useOperationsStore()
const trendChartRef = ref(null)
let trendChart = null
let resizeObserver = null

const updateChart = () => {
  if (!trendChart) return
  const mockTrend = Array.from({length: 12}, (_, i) => ({ 
    time: `1${i}:00`, 
    val1: 400 + Math.random()*200, 
    val2: 70 + Math.random()*30 
  }))
  const data = store.kpi.daily_trend?.length ? store.kpi.daily_trend : mockTrend
  
  trendChart.setOption({
    xAxis: { data: data.map(d => d.time || new Date(d.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})) },
    series: [
      { name: '产量', data: data.map(d => d.val1 || d.tonnage) },
      { name: '效率', data: data.map(d => d.val2 || d.efficiency) }
    ]
  })
}

onMounted(() => {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5, 12, 34, 0.95)', borderColor: '#00f0ff', textStyle: { color: '#fff', fontSize: 10 } },
      legend: { textStyle: { color: '#8892b0', fontSize: 10 }, top: 0, icon: 'circle' },
      grid: { left: '30', right: '10', bottom: '20', top: '40' },
      xAxis: { type: 'category', axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } }, axisLabel: { color: '#8892b0', fontSize: 9 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } }, axisLabel: { color: '#8892b0', fontSize: 9 } },
      series: [
        { name: '产量', type: 'line', smooth: true, itemStyle: { color: '#00f0ff' }, lineStyle: { width: 3, shadowColor: '#00f0ff', shadowBlur: 10 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: 'rgba(0, 240, 255, 0.4)'}, {offset: 1, color: 'transparent'}]) } },
        { name: '效率', type: 'line', smooth: true, itemStyle: { color: '#00ff88' }, lineStyle: { width: 3, shadowColor: '#00ff88', shadowBlur: 10 } }
      ]
    })
    
    // Add ResizeObserver for responsive chart
    resizeObserver = new ResizeObserver(() => {
      trendChart?.resize()
    })
    resizeObserver.observe(trendChartRef.value)
    
    updateChart()
  }
})

watch(() => store.kpi, () => {
  updateChart()
}, { deep: true })

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  trendChart?.dispose()
})
</script>

<style scoped>
.chart-box-enhanced { width: 100%; height: 220px; }
</style>

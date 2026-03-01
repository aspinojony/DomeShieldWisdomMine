<template>
  <div class="alert-manage">
    <div class="panel-header">
      <h2 class="title">业务告警处理</h2>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="fetchAlerts">
          <span class="icon">🔄</span> 刷新流水
        </button>
      </div>
    </div>

    <!-- 告警流水表 -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>设备 ID</th>
            <th>触发时间</th>
            <th>监控指标</th>
            <th>实测值 / 阈值</th>
            <th>警戒级别</th>
            <th>处理状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="alert in alerts" :key="alert.id" :class="{ 'row-unack': !alert.is_acknowledged }">
            <td>{{ alert.id }}</td>
            <td class="id-col">{{ alert.device_id }}</td>
            <td class="time-col">{{ formatDate(alert.triggered_at) }}</td>
            <td><span class="metric-badge">{{ alert.metric_field }}</span></td>
            <td>
              <strong class="metric-val">{{ alert.metric_value.toFixed(2) }}</strong> / 
              <span class="threshold">{{ alert.threshold.toFixed(2) }}</span>
            </td>
            <td>
              <span :class="'level-badge level-' + alert.alert_level">
                {{ formatLevel(alert.alert_level) }}
              </span>
            </td>
            <td>
              <span class="status-badge" :class="alert.is_acknowledged ? 'resolved' : 'pending'">
                {{ alert.is_acknowledged ? '以处理' : '未处理' }}
              </span>
            </td>
            <td class="action-col">
              <button 
                class="btn-icon btn-ack" 
                title="确认处理此告警" 
                v-if="!alert.is_acknowledged"
                @click="ackAlert(alert.id)">
                ✅
              </button>
              <span class="done-text" v-else>已闭环</span>
            </td>
          </tr>
          <tr v-if="alerts.length === 0">
            <td colspan="8" class="empty-state">目前没有系统告警流水</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { authState } from '../../auth'

const API_BIZ_BASE = 'http://127.0.0.1:8002/api/v1'
const alerts = ref([])

const fetchAlerts = async () => {
  try {
    const res = await axios.get(`${API_BIZ_BASE}/alert-records?limit=100`)
    alerts.value = res.data
  } catch (error) {
    console.error('获取告警流水失败:', error)
  }
}

const ackAlert = async (alertId) => {
  try {
    await axios.put(`${API_BIZ_BASE}/alert-records/${alertId}/ack`)
    // update locally without refetching the whole list if we want, or just refetch
    fetchAlerts()
  } catch (error) {
    alert(error.response?.data?.detail || '处理失败，请重试')
  }
}

const formatDate = (isoString) => {
  if (!isoString) return '-'
  return new Date(isoString).toLocaleString('zh-CN', { hour12: false })
}

const formatLevel = (level) => {
  const map = { info: '信息', warning: '警告', critical: '严重' }
  return map[level] || level
}

onMounted(() => {
  fetchAlerts()
})
</script>

<style scoped>
/* 共用大部分 admin 样式 */
.alert-manage { height: 100%; display: flex; flex-direction: column; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.title { margin: 0; color: #00f0ff; font-size: 1.4rem; letter-spacing: 1px; }

.header-actions { display: flex; gap: 10px; }

.btn { padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; transition: all 0.2s; border: none; font-family: inherit; }
.btn-secondary { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); color: #ccd6f6; }
.btn-secondary:hover { background: rgba(255, 255, 255, 0.1); }

.table-container { flex: 1; overflow: auto; border: 1px solid rgba(0, 240, 255, 0.15); border-radius: 8px; background: rgba(0, 0, 0, 0.2); }
.data-table { width: 100%; border-collapse: collapse; text-align: left; color: #ccd6f6; font-size: 0.9rem; }
.data-table th { background: rgba(0, 240, 255, 0.1); padding: 12px 16px; font-weight: 600; color: #00f0ff; position: sticky; top: 0; z-index: 10; }
.data-table td { padding: 14px 16px; border-bottom: 1px solid rgba(0, 240, 255, 0.05); }

.row-unack { background: rgba(255, 60, 60, 0.03) !important; animation: pulseRed 3s infinite alternate; }
@keyframes pulseRed { from { background: rgba(255, 60, 60, 0.03); } to { background: rgba(255, 60, 60, 0.08); } }
.data-table tbody tr:hover { background: rgba(0, 240, 255, 0.08) !important; }

.id-col { font-family: 'Courier New', Courier, monospace; color: #8892b0; }
.time-col { font-size: 0.85rem; color: #8892b0; }
.metric-badge { background: rgba(255, 255, 255, 0.1); padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; font-family: monospace; }
.metric-val { color: #ff6b6b; font-size: 1.05rem; }
.threshold { color: #8892b0; font-size: 0.9rem; }

.level-badge { padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
.level-info { background: rgba(0, 150, 255, 0.2); color: #00a8ff; border: 1px solid rgba(0, 150, 255, 0.4); }
.level-warning { background: rgba(255, 165, 0, 0.2); color: #ffa502; border: 1px solid rgba(255, 165, 0, 0.4); }
.level-critical { background: rgba(255, 0, 0, 0.2); color: #ff4757; border: 1px solid rgba(255, 0, 0, 0.4); }

.status-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; }
.status-badge.pending { background: rgba(255, 0, 0, 0.1); color: #ff4757; border: 1px solid rgba(255, 0, 0, 0.3); }
.status-badge.resolved { background: rgba(0, 255, 0, 0.1); color: #2ed573; border: 1px solid rgba(0, 255, 0, 0.3); }

.btn-icon { background: transparent; border: none; cursor: pointer; opacity: 0.8; font-size: 1.3rem; padding: 4px; border-radius: 4px; transition: auto; }
.btn-icon:hover { opacity: 1; transform: scale(1.1); }
.done-text { font-size: 0.8rem; color: #556677; }
.empty-state { text-align: center; padding: 40px !important; color: #556677; }
</style>

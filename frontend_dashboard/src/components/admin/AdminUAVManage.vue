<template>
  <div class="uav-manage">
    <div class="panel-header">
      <h2 class="title">空天无人机指控集群</h2>
      <button class="btn btn-primary" @click="openMissionModal">
        <span class="icon">✈️</span> 下发巡检任务
      </button>
    </div>

    <div class="dashboard-grid">
      <!-- 集群控制面 -->
      <div class="control-panel glass-card">
        <h3>集群一键控制 (Broadcast Command)</h3>
        <p class="desc">向所有在线无人机广播核心飞行指令</p>
        <div class="command-group">
          <button class="btn-cmd takeoff" @click="sendCommand('ALL', 'takeoff')">🚀 编队起飞 (Takeoff)</button>
          <button class="btn-cmd hover" @click="sendCommand('ALL', 'hover')">⏸️ 编队悬停 (Hover)</button>
          <button class="btn-cmd rth" @click="sendCommand('ALL', 'rth')">🏠 返航 (RTH)</button>
          <button class="btn-cmd land" @click="sendCommand('ALL', 'land')">🛬 降落 (Land)</button>
        </div>
      </div>

      <!-- 任务列表 -->
      <div class="mission-list glass-card">
        <h3>无人机任务派遣队列</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>任务ID</th>
              <th>绑定设备</th>
              <th>任务名称</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="mission in missions" :key="mission.id">
              <td>{{ mission.id }}</td>
              <td class="id-col">{{ mission.device_id }}</td>
              <td>{{ mission.mission_name }}</td>
              <td>
                <span :class="'status-badge status-' + mission.status">{{ formatStatus(mission.status) }}</span>
              </td>
            </tr>
            <tr v-if="missions.length === 0">
              <td colspan="4" class="empty-state">目前没有配置巡更任务</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 创建任务模态框 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>派遣 UAV 巡飞任务</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitMission" class="uav-form">
          <div class="form-group">
            <label>指定无人机设备 (Device ID)*</label>
            <select v-model="form.device_id" required>
              <option value="" disabled>-- 请选择 UAV 设备 --</option>
              <option v-for="dev in uavDevices" :key="dev.device_id" :value="dev.device_id">
                {{ dev.device_id }} ({{ dev.device_name }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>任务名称*</label>
            <input v-model="form.mission_name" type="text" required placeholder="如: 矿坑北坡地质巡检" />
          </div>
          <div class="form-group">
            <label>航点路线 (JSON 坐标集)*</label>
            <textarea v-model="form.waypoints" rows="4" placeholder='[{"lat":39.5, "lng":116.3}, ...]' required></textarea>
          </div>

          <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="isSaving">
              {{ isSaving ? '下发中...' : '确认派遣' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { authState } from '../../auth'

const API_BIZ_BASE = 'http://127.0.0.1:8002/api/v1'

const missions = ref([])
const uavDevices = ref([])

const showModal = ref(false)
const isSaving = ref(false)
const errorMsg = ref('')

const form = ref({
  device_id: '',
  mission_name: '',
  waypoints: '[\n  {"lat": 39.5, "lng": 116.3},\n  {"lat": 39.55, "lng": 116.35}\n]'
})

const fetchMissions = async () => {
  try {
    const res = await axios.get(`${API_BIZ_BASE}/uav/missions`)
    missions.value = res.data
  } catch (error) {
    console.error('获取任务列表失败', error)
  }
}

const fetchUavDevices = async () => {
  try {
    const res = await axios.get(`${API_BIZ_BASE}/devices?device_type=uav`)
    uavDevices.value = res.data
  } catch (error) {
    console.error('获取无人机设备失败', error)
  }
}

const formatStatus = (status) => {
  const map = { pending: '等待执行', executing: '飞行中', completed: '已完成', aborted: '已中止' }
  return map[status] || status
}

const openMissionModal = () => {
  errorMsg.value = ''
  form.value = {
    device_id: uavDevices.value.length > 0 ? uavDevices.value[0].device_id : '',
    mission_name: '日常自动巡飞',
    waypoints: '[\n  {"lat": 39.5, "lng": 116.3},\n  {"lat": 39.55, "lng": 116.35}\n]'
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const submitMission = async () => {
  errorMsg.value = ''
  isSaving.value = true
  try {
    await axios.post(`${API_BIZ_BASE}/uav/missions`, form.value)
    closeModal()
    fetchMissions()
    alert('无人机任务已成功下发至队列')
  } catch (error) {
    errorMsg.value = error.response?.data?.detail || '保存失败'
  } finally {
    isSaving.value = false
  }
}

const sendCommand = async (deviceId, command) => {
  if (!confirm(`确定要向 [${deviceId}] 发送 [${command}] 指令吗？`)) return
  try {
    await axios.post(`${API_BIZ_BASE}/uav/${deviceId}/command?command=${command}`)
    alert(`指令 ${command} 发送成功`)
  } catch (error) {
    alert(`发送失败: ${error.response?.data?.detail || error.message}`)
  }
}

onMounted(() => {
  fetchMissions()
  fetchUavDevices()
})
</script>

<style scoped>
.uav-manage { height: 100%; display: flex; flex-direction: column; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.title { margin: 0; color: #00f0ff; font-size: 1.4rem; letter-spacing: 1px; }

.btn { padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; transition: all 0.2s; border: none; font-family: inherit; }
.btn-primary { background: linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(0, 150, 255, 0.3)); border: 1px solid rgba(0, 240, 255, 0.5); color: #00f0ff; }
.btn-primary:hover:not(:disabled) { box-shadow: 0 0 15px rgba(0, 240, 255, 0.25); }

.dashboard-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
}

.glass-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(0, 240, 255, 0.15);
  border-radius: 8px;
  padding: 20px;
}

.glass-card h3 {
  margin-top: 0;
  color: #ccd6f6;
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
  padding-bottom: 10px;
  margin-bottom: 15px;
}

.desc { color: #8892b0; font-size: 0.9rem; margin-bottom: 15px; }

/* 命令按钮组 */
.command-group { display: flex; gap: 16px; flex-wrap: wrap; }
.btn-cmd { padding: 12px 24px; font-size: 1rem; font-weight: bold; border-radius: 6px; cursor: pointer; border: none; color: #fff; transition: transform 0.2s, filter 0.2s; }
.btn-cmd:hover { transform: translateY(-2px); filter: brightness(1.2); }
.btn-cmd:active { transform: translateY(0); }

.takeoff { background: linear-gradient(135deg, #00b09b, #96c93d); }
.hover { background: linear-gradient(135deg, #fceabb, #f8b500); color: #333; }
.rth { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.land { background: linear-gradient(135deg, #ff0844, #ffb199); }

/* 任务列表 */
.mission-list { flex: 1; overflow-y: auto; }
.data-table { width: 100%; border-collapse: collapse; text-align: left; color: #ccd6f6; font-size: 0.9rem; }
.data-table th { background: rgba(0, 240, 255, 0.1); padding: 12px 16px; font-weight: 600; color: #00f0ff; }
.data-table td { padding: 14px 16px; border-bottom: 1px solid rgba(0, 240, 255, 0.05); }

.id-col { font-family: monospace; color: #8892b0; }
.status-badge { padding: 4px 12px; border-radius: 4px; font-size: 0.8rem; border: 1px solid transparent; }
.status-pending { background: rgba(255, 165, 0, 0.2); color: #ffa502; border-color: rgba(255, 165, 0, 0.4); }
.status-executing { background: rgba(0, 240, 255, 0.2); color: #00f0ff; border-color: rgba(0, 240, 255, 0.4); }
.status-completed { background: rgba(0, 255, 0, 0.2); color: #2ed573; border-color: rgba(0, 255, 0, 0.4); }
.status-aborted { background: rgba(255, 0, 0, 0.2); color: #ff4757; border-color: rgba(255, 0, 0, 0.4); }

.empty-state { text-align: center; color: #556677; }

/* 模态框 */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: #0d1b2a; border: 1px solid rgba(0, 240, 255, 0.3); border-radius: 12px; width: 500px; }
.modal-header { padding: 20px; border-bottom: 1px solid rgba(0, 240, 255, 0.1); display: flex; justify-content: space-between; align-items: center; }
.modal-header h3 { margin: 0; color: #00f0ff; }
.close-btn { background: none; border: none; color: #8892b0; font-size: 1.5rem; cursor: pointer; }
.close-btn:hover { color: #fff; }

.uav-form { padding: 24px; }
.form-group { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.form-group label { color: #ccd6f6; font-size: 0.9rem; }
.form-group input, .form-group select, .form-group textarea { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; padding: 10px; color: #fff; font-family: inherit; }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { outline: none; border-color: #00f0ff; }

.error-msg { color: #ff4757; font-size: 0.85rem; background: rgba(255,0,0,0.1); padding: 10px; border-radius: 6px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
.btn-secondary { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); color: #ccd6f6; }
</style>

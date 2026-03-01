<template>
  <div class="device-manage">
    <div class="panel-header">
      <h2 class="title">设备台账管理</h2>
      <button class="btn btn-primary" @click="openAddModal">
        <span class="icon">➕</span> 注册新设备
      </button>
    </div>

    <!-- 设备列表表格 -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>设备ID (MAC/SN)</th>
            <th>设备名称</th>
            <th>设备类型</th>
            <th>位置 (经度, 纬度)</th>
            <th>状态</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="dev in devices" :key="dev.device_id">
            <td class="id-col">{{ dev.device_id }}</td>
            <td>{{ dev.device_name }}</td>
            <td><span class="type-badge">{{ dev.device_type }}</span></td>
            <td class="pos-col">{{ dev.longitude }}, {{ dev.latitude }}</td>
            <td>
              <span class="status-dot" :class="dev.status"></span>
              {{ dev.status === 'online' ? '在线' : (dev.status === 'offline' ? '离线' : '故障') }}
            </td>
            <td class="time-col">{{ formatDate(dev.created_at) }}</td>
            <td class="action-col">
              <button class="btn-icon btn-edit" title="编辑" @click="openEditModal(dev)">✏️</button>
              <button class="btn-icon btn-delete" title="删除" @click="deleteDevice(dev.device_id)" v-if="authState.isAdmin">🗑️</button>
            </td>
          </tr>
          <tr v-if="devices.length === 0">
            <td colspan="7" class="empty-state">暂无设备注册</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 新增/编辑模态框 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ isEdit ? '编辑设备信息' : '注册新设备' }}</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitForm" class="device-form">
          <div class="form-group">
            <label>设备ID (需唯一)*</label>
            <input v-model="form.device_id" type="text" required :disabled="isEdit" placeholder="例如: SENSOR-MV-999" />
          </div>
          <div class="form-group">
            <label>设备名称*</label>
            <input v-model="form.device_name" type="text" required placeholder="例如: 9号微震仪" />
          </div>
          <div class="form-group">
            <label>设备类型*</label>
            <select v-model="form.device_type" required>
              <option value="micro_seismic">微震仪 (micro_seismic)</option>
              <option value="crack_meter">裂缝计 (crack_meter)</option>
              <option value="inclinometer">倾角计 (inclinometer)</option>
              <option value="settlement">沉降计 (settlement)</option>
              <option value="water_pressure">孔隙水压计 (water_pressure)</option>
              <option value="gnss">GNSS 基站 (gnss)</option>
              <option value="uav">无人机 (uav)</option>
            </select>
          </div>
          
          <div class="form-row">
            <div class="form-group half">
              <label>经度 (Longitude)*</label>
              <input v-model.number="form.longitude" type="number" step="0.000001" required />
            </div>
            <div class="form-group half">
              <label>纬度 (Latitude)*</label>
              <input v-model.number="form.latitude" type="number" step="0.000001" required />
            </div>
          </div>

          <div class="form-group" v-if="isEdit">
            <label>当前状态</label>
            <select v-model="form.status">
              <option value="online">在线</option>
              <option value="offline">离线</option>
              <option value="error">故障</option>
            </select>
          </div>

          <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="isSaving">
              {{ isSaving ? '保存中...' : '提交保存' }}
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
const devices = ref([])

// 模态框状态
const showModal = ref(false)
const isEdit = ref(false)
const isSaving = ref(false)
const errorMsg = ref('')

// 表单数据绑定
const form = ref({
  device_id: '',
  device_name: '',
  device_type: 'displacement',
  longitude: 116.397128,
  latitude: 39.916527,
  status: 'offline'
})

const fetchDevices = async () => {
  try {
    const res = await axios.get(`${API_BIZ_BASE}/devices`)
    devices.value = res.data
  } catch (error) {
    console.error('获取设备列表失败:', error)
  }
}

const formatDate = (isoString) => {
  if (!isoString) return '-'
  return new Date(isoString).toLocaleString('zh-CN', { hour12: false })
}

const openAddModal = () => {
  isEdit.value = false
  errorMsg.value = ''
  form.value = {
    device_id: '',
    device_name: '',
    device_type: 'displacement',
    longitude: 110.123456,
    latitude: 35.123456,
    status: 'offline'
  }
  showModal.value = true
}

const openEditModal = (device) => {
  isEdit.value = true
  errorMsg.value = ''
  // 填充数据
  form.value = { ...device }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const submitForm = async () => {
  errorMsg.value = ''
  isSaving.value = true
  try {
    if (isEdit.value) {
      // 排除不允许修改的字段
      const updateData = {
        device_name: form.value.device_name,
        device_type: form.value.device_type,
        longitude: form.value.longitude,
        latitude: form.value.latitude,
        status: form.value.status
      }
      await axios.put(`${API_BIZ_BASE}/devices/${form.value.device_id}`, updateData)
    } else {
      await axios.post(`${API_BIZ_BASE}/devices`, form.value)
    }
    closeModal()
    fetchDevices() // 刷新列表
  } catch (error) {
    errorMsg.value = error.response?.data?.detail || '保存失败，请检查输入'
  } finally {
    isSaving.value = false
  }
}

const deleteDevice = async (deviceId) => {
  if (!confirm(`确定要删除设备 ${deviceId} 吗？此操作不可恢复。`)) return
  try {
    await axios.delete(`${API_BIZ_BASE}/devices/${deviceId}`)
    fetchDevices()
  } catch (error) {
    alert(error.response?.data?.detail || '删除失败，请重试')
  }
}

onMounted(() => {
  fetchDevices()
})
</script>

<style scoped>
.device-manage {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.title {
  margin: 0;
  color: #00f0ff;
  font-size: 1.4rem;
  letter-spacing: 1px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
  border: none;
  font-family: inherit;
}

.btn-primary {
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(0, 150, 255, 0.3));
  border: 1px solid rgba(0, 240, 255, 0.5);
  color: #00f0ff;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.3), rgba(0, 150, 255, 0.5));
  box-shadow: 0 0 15px rgba(0, 240, 255, 0.25);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #ccd6f6;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.table-container {
  flex: 1;
  overflow: auto;
  border: 1px solid rgba(0, 240, 255, 0.15);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.2);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  color: #ccd6f6;
  font-size: 0.9rem;
}

.data-table th {
  background: rgba(0, 240, 255, 0.1);
  padding: 12px 16px;
  font-weight: 600;
  color: #00f0ff;
  position: sticky;
  top: 0;
  z-index: 10;
}

.data-table td {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.05);
  vertical-align: middle;
}

.data-table tbody tr:hover {
  background: rgba(0, 240, 255, 0.05);
}

.id-col {
  font-family: 'Courier New', Courier, monospace;
  color: #8892b0;
}

.type-badge {
  background: rgba(255, 255, 255, 0.1);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
}

.pos-col {
  font-size: 0.85rem;
  color: #8892b0;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.status-dot.online { background: #00ff00; box-shadow: 0 0 8px #00ff00; }
.status-dot.offline { background: #8892b0; }
.status-dot.error { background: #ff4444; box-shadow: 0 0 8px #ff4444; }

.time-col {
  font-size: 0.85rem;
  color: #8892b0;
}

.action-col {
  display: flex;
  gap: 8px;
}

.btn-icon {
  background: transparent;
  border: none;
  cursor: pointer;
  opacity: 0.7;
  transition: auto;
  font-size: 1.1rem;
  padding: 4px;
  border-radius: 4px;
}

.btn-icon:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.1);
}

.empty-state {
  text-align: center;
  padding: 40px !important;
  color: #556677;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #0d1b2a;
  border: 1px solid rgba(0, 240, 255, 0.3);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 240, 255, 0.1);
  border-radius: 12px;
  width: 500px;
  max-width: 90vw;
  animation: modalIn 0.3s ease-out;
}

@keyframes modalIn {
  from { opacity: 0; transform: scale(0.95) translateY(-10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.modal-header h3 {
  margin: 0;
  color: #00f0ff;
  font-size: 1.2rem;
}

.close-btn {
  background: none;
  border: none;
  color: #8892b0;
  font-size: 1.5rem;
  cursor: pointer;
  transition: color 0.2s;
}
.close-btn:hover { color: #fff; }

.device-form {
  padding: 24px;
}

.form-group {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-group.half {
  flex: 1;
}

.form-group label {
  color: #ccd6f6;
  font-size: 0.9rem;
}

.form-group input, .form-group select {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 10px 12px;
  color: #fff;
  font-family: inherit;
  font-size: 0.95rem;
}

.form-group input:focus, .form-group select:focus {
  outline: none;
  border-color: #00f0ff;
  box-shadow: 0 0 8px rgba(0, 240, 255, 0.2);
}

.form-group input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-msg {
  color: #ff4444;
  font-size: 0.85rem;
  background: rgba(255, 0, 0, 0.1);
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
</style>

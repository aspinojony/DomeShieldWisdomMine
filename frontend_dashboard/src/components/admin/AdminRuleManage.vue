<template>
  <div class="rule-manage">
    <div class="panel-header">
      <h2 class="title">告警规则设置</h2>
      <button class="btn btn-primary" @click="openAddModal">
        <span class="icon">➕</span> 新增规则
      </button>
    </div>

    <!-- 规则列表表格 -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>规则ID</th>
            <th>绑定设备 ID</th>
            <th>监控指标</th>
            <th>触发条件</th>
            <th>级别</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rule in rules" :key="rule.id">
            <td>{{ rule.id }}</td>
            <td class="id-col">{{ rule.device_id }}</td>
            <td><span class="metric-badge">{{ rule.metric_field }}</span></td>
            <td class="condition-col">
              当值 <strong class="operator">{{ rule.operator }}</strong>
              <strong class="threshold">{{ rule.threshold }}</strong>
            </td>
            <td>
              <span :class="'level-badge level-' + rule.alert_level">
                {{ formatLevel(rule.alert_level) }}
              </span>
            </td>
            <td>
              <span class="status-badge" :class="rule.is_enabled ? 'enabled' : 'disabled'">
                {{ rule.is_enabled ? '启用' : '停用' }}
              </span>
            </td>
            <td class="action-col">
              <button class="btn-icon btn-delete" title="删除" @click="deleteRule(rule.id)" v-if="authState.isAdmin">🗑️</button>
            </td>
          </tr>
          <tr v-if="rules.length === 0">
            <td colspan="7" class="empty-state">暂无规则，请添加</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 新增模态框 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>新建告警规则</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitForm" class="rule-form">
          <div class="form-group">
            <label>绑定设备 (Device ID)*</label>
            <select v-model="form.device_id" required>
              <option value="" disabled>-- 请选择设备 --</option>
              <option v-for="dev in devices" :key="dev.device_id" :value="dev.device_id">
                {{ dev.device_id }} ({{ dev.device_name }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>监控指标 (Metric Field)*</label>
            <input v-model="form.metric_field" type="text" required placeholder="例如: crack_width_mm, max_amplitude" />
          </div>
          <div class="form-row">
            <div class="form-group half">
              <label>比较运算符*</label>
              <select v-model="form.operator" required>
                <option value=">">大于 (>)</option>
                <option value="<">小于 (<)</option>
                <option value=">=">大于等于 (>=)</option>
                <option value="<=">小于等于 (<=)</option>
                <option value="==">等于 (==)</option>
              </select>
            </div>
            <div class="form-group half">
              <label>阈值 (Threshold)*</label>
              <input v-model.number="form.threshold" type="number" step="0.01" required />
            </div>
          </div>
          <div class="form-group">
            <label>告警级别*</label>
            <select v-model="form.alert_level" required>
              <option value="info">信息 (Info)</option>
              <option value="warning">警告 (Warning)</option>
              <option value="critical">严重 (Critical)</option>
            </select>
          </div>
          <div class="form-group">
            <label>启用规则</label>
            <input type="checkbox" v-model="form.is_enabled" class="checkbox" />
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
const rules = ref([])
const devices = ref([])

const showModal = ref(false)
const isSaving = ref(false)
const errorMsg = ref('')

const form = ref({
  device_id: '',
  metric_field: 'crack_width_mm',
  operator: '>',
  threshold: 10.0,
  alert_level: 'warning',
  description: '',
  is_enabled: true
})

const fetchRules = async () => {
  try {
    const res = await axios.get(`${API_BIZ_BASE}/alert-rules`)
    rules.value = res.data
  } catch (error) {
    console.error('获取规则列表失败:', error)
  }
}

const fetchDevices = async () => {
  try {
    const res = await axios.get(`${API_BIZ_BASE}/devices`)
    devices.value = res.data
  } catch (error) {
    console.error('获取设备列表失败:', error)
  }
}

const formatLevel = (level) => {
  const map = { info: '信息', warning: '警告', critical: '严重' }
  return map[level] || level
}

const openAddModal = () => {
  errorMsg.value = ''
  form.value = {
    device_id: devices.value.length > 0 ? devices.value[0].device_id : '',
    metric_field: 'crack_width_mm',
    operator: '>',
    threshold: 10.0,
    alert_level: 'warning',
    description: '',
    is_enabled: true
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const submitForm = async () => {
  errorMsg.value = ''
  isSaving.value = true
  try {
    await axios.post(`${API_BIZ_BASE}/alert-rules`, form.value)
    closeModal()
    fetchRules()
  } catch (error) {
    errorMsg.value = error.response?.data?.detail || '保存失败，请检查输入'
  } finally {
    isSaving.value = false
  }
}

const deleteRule = async (ruleId) => {
  if (!confirm(`确定要删除规则 ID ${ruleId} 吗？此操作不可恢复。`)) return
  try {
    await axios.delete(`${API_BIZ_BASE}/alert-rules/${ruleId}`)
    fetchRules()
  } catch (error) {
    alert(error.response?.data?.detail || '删除失败，请重试')
  }
}

onMounted(() => {
  fetchRules()
  fetchDevices()
})
</script>

<style scoped>
/* 共用 AdminDeviceManage 的很多样式 */
.rule-manage { height: 100%; display: flex; flex-direction: column; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.title { margin: 0; color: #00f0ff; font-size: 1.4rem; letter-spacing: 1px; }

.btn { padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; transition: all 0.2s; border: none; font-family: inherit; }
.btn-primary { background: linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(0, 150, 255, 0.3)); border: 1px solid rgba(0, 240, 255, 0.5); color: #00f0ff; }
.btn-primary:hover:not(:disabled) { background: linear-gradient(135deg, rgba(0, 240, 255, 0.3), rgba(0, 150, 255, 0.5)); box-shadow: 0 0 15px rgba(0, 240, 255, 0.25); }
.btn-secondary { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); color: #ccd6f6; }
.btn-secondary:hover { background: rgba(255, 255, 255, 0.1); }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }

.table-container { flex: 1; overflow: auto; border: 1px solid rgba(0, 240, 255, 0.15); border-radius: 8px; background: rgba(0, 0, 0, 0.2); }
.data-table { width: 100%; border-collapse: collapse; text-align: left; color: #ccd6f6; font-size: 0.9rem; }
.data-table th { background: rgba(0, 240, 255, 0.1); padding: 12px 16px; font-weight: 600; color: #00f0ff; position: sticky; top: 0; z-index: 10; }
.data-table td { padding: 14px 16px; border-bottom: 1px solid rgba(0, 240, 255, 0.05); vertical-align: middle; }
.data-table tbody tr:hover { background: rgba(0, 240, 255, 0.05); }

.id-col { font-family: 'Courier New', Courier, monospace; color: #8892b0; }
.metric-badge { background: rgba(255, 255, 255, 0.1); padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; font-family: monospace; }
.condition-col { font-size: 0.95rem; }
.operator { color: #ffeb3b; padding: 0 6px; }
.threshold { color: #ff6b6b; font-weight: bold; }

.level-badge { padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
.level-info { background: rgba(0, 150, 255, 0.2); color: #00a8ff; border: 1px solid rgba(0, 150, 255, 0.4); }
.level-warning { background: rgba(255, 165, 0, 0.2); color: #ffa502; border: 1px solid rgba(255, 165, 0, 0.4); }
.level-critical { background: rgba(255, 0, 0, 0.2); color: #ff4757; border: 1px solid rgba(255, 0, 0, 0.4); }

.status-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; }
.status-badge.enabled { background: rgba(0, 255, 0, 0.1); color: #2ed573; }
.status-badge.disabled { background: rgba(255, 255, 255, 0.1); color: #a4b0be; }

.btn-icon { background: transparent; border: none; cursor: pointer; opacity: 0.7; font-size: 1.1rem; padding: 4px; border-radius: 4px; transition: auto; }
.btn-icon:hover { opacity: 1; background: rgba(255, 255, 255, 0.1); }
.empty-state { text-align: center; padding: 40px !important; color: #556677; }

/* Modal Styles */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: #0d1b2a; border: 1px solid rgba(0, 240, 255, 0.3); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 240, 255, 0.1); border-radius: 12px; width: 500px; max-width: 90vw; animation: modalIn 0.3s ease-out; }
@keyframes modalIn { from { opacity: 0; transform: scale(0.95) translateY(-10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid rgba(0, 240, 255, 0.1); }
.modal-header h3 { margin: 0; color: #00f0ff; font-size: 1.2rem; }
.close-btn { background: none; border: none; color: #8892b0; font-size: 1.5rem; cursor: pointer; transition: color 0.2s; }
.close-btn:hover { color: #fff; }

.rule-form { padding: 24px; }
.form-group { margin-bottom: 16px; display: flex; flex-direction: column; gap: 8px; }
.form-row { display: flex; gap: 16px; }
.form-group.half { flex: 1; }
.form-group label { color: #ccd6f6; font-size: 0.9rem; }
.form-group input[type="text"], .form-group input[type="number"], .form-group select { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; padding: 10px 12px; color: #fff; font-family: inherit; font-size: 0.95rem; }
.form-group input:focus, .form-group select:focus { outline: none; border-color: #00f0ff; box-shadow: 0 0 8px rgba(0, 240, 255, 0.2); }
.checkbox { width: 18px; height: 18px; accent-color: #00f0ff; cursor: pointer; }
.error-msg { color: #ff4444; font-size: 0.85rem; background: rgba(255, 0, 0, 0.1); padding: 10px; border-radius: 6px; margin-bottom: 16px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
</style>

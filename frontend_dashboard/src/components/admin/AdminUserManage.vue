<template>
  <div class="user-manage">
    <div class="panel-header">
      <h2 class="title">用户权限管理</h2>
      <button class="btn btn-primary" @click="openAddModal">
        <span class="icon">👤</span> 添加新用户
      </button>
    </div>

    <!-- 用户列表 -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>全名</th>
            <th>角色权限</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          <!-- 演示数据，后台因为目前没有提供查询所有 /users 接口，这里我们做一个前端mock和拦截演示注册 -->
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td class="username-col">{{ user.username }}</td>
            <td>{{ user.full_name }}</td>
            <td><span :class="'role-badge role-' + user.role">{{ roleMap[user.role] }}</span></td>
            <td>{{ user.created_at }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 注册模态框 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>注册新账户</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitForm" class="user-form">
          <div class="form-group">
            <label>用户名 (登录名)*</label>
            <input v-model="form.username" type="text" required placeholder="如: zhangsan" />
          </div>
          <div class="form-group">
            <label>登录密码*</label>
            <input v-model="form.password" type="text" required placeholder="不少于6位" />
          </div>
          <div class="form-group">
            <label>全名</label>
            <input v-model="form.full_name" type="text" placeholder="如: 张三" />
          </div>
          <div class="form-group">
            <label>角色权限*</label>
            <select v-model="form.role" required>
              <option value="admin">管理员 (Admin) - 全部权限</option>
              <option value="engineer">工程师 (Engineer) - 仅操作设备规则</option>
              <option value="viewer">观察员 (Viewer) - 仅查看数据</option>
            </select>
          </div>

          <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
          <div v-if="successMsg" class="success-msg">{{ successMsg }}</div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">关闭</button>
            <button type="submit" class="btn btn-primary" :disabled="isSaving">
              {{ isSaving ? '提交注册中...' : '注册用户' }}
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

const roleMap = {
  admin: '系统管理员',
  engineer: '工程师',
  viewer: '观察员'
}

// 因为后端未实现 GET /users，我们填充一些伪装的数据供展示
const users = ref([
  { id: 1, username: 'admin', full_name: '系统超级管理员', role: 'admin', created_at: '2023-01-01 08:00:00' },
  { id: 2, username: 'test_eng', full_name: '测试工程师', role: 'engineer', created_at: '2023-10-15 14:30:22' },
])

const showModal = ref(false)
const isSaving = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const form = ref({
  username: '',
  password: '',
  full_name: '',
  role: 'viewer'
})

const openAddModal = () => {
  errorMsg.value = ''
  successMsg.value = ''
  form.value = {
    username: '',
    password: '',
    full_name: '',
    role: 'viewer'
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  successMsg.value = ''
}

const submitForm = async () => {
  errorMsg.value = ''
  successMsg.value = ''
  isSaving.value = true
  try {
    // 调用实际后端的注册接口
    await axios.post(`${API_BIZ_BASE}/auth/register`, form.value)
    successMsg.value = `用户 ${form.value.username} 注册成功！`
    // Mock update list
    users.value.push({
      id: Math.floor(Math.random() * 1000) + 10,
      username: form.value.username,
      full_name: form.value.full_name,
      role: form.value.role,
      created_at: new Date().toLocaleString('zh-CN', { hour12: false })
    })
    form.value.password = '' // clear password
  } catch (error) {
    errorMsg.value = error.response?.data?.detail || '注册失败，可能用户名已存在'
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
/* 共用 AdminDeviceManage 样式 */
.user-manage { height: 100%; display: flex; flex-direction: column; }
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
.data-table td { padding: 14px 16px; border-bottom: 1px solid rgba(0, 240, 255, 0.05); }
.username-col { font-weight: bold; color: #fff; letter-spacing: 1px; }

.role-badge { padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
.role-admin { background: rgba(255, 0, 0, 0.2); color: #ff4757; border: 1px solid rgba(255, 0, 0, 0.4); }
.role-engineer { background: rgba(255, 165, 0, 0.2); color: #ffa502; border: 1px solid rgba(255, 165, 0, 0.4); }
.role-viewer { background: rgba(0, 150, 255, 0.2); color: #00a8ff; border: 1px solid rgba(0, 150, 255, 0.4); }

/* Modal Styles */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: #0d1b2a; border: 1px solid rgba(0, 240, 255, 0.3); border-radius: 12px; width: 450px; animation: modalIn 0.3s ease-out; }
@keyframes modalIn { from { opacity: 0; transform: scale(0.95) translateY(-10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid rgba(0, 240, 255, 0.1); }
.modal-header h3 { margin: 0; color: #00f0ff; font-size: 1.2rem; }
.close-btn { background: none; border: none; color: #8892b0; font-size: 1.5rem; cursor: pointer; }
.close-btn:hover { color: #fff; }

.user-form { padding: 24px; }
.form-group { margin-bottom: 16px; display: flex; flex-direction: column; gap: 8px; }
.form-group label { color: #ccd6f6; font-size: 0.9rem; }
.form-group input, .form-group select { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; padding: 10px 12px; color: #fff; font-size: 0.95rem; }
.form-group input:focus, .form-group select:focus { outline: none; border-color: #00f0ff; box-shadow: 0 0 8px rgba(0, 240, 255, 0.2); }

.error-msg { color: #ff4444; font-size: 0.85rem; background: rgba(255, 0, 0, 0.1); padding: 10px; border-radius: 6px; margin-bottom: 16px; }
.success-msg { color: #00ff00; font-size: 0.85rem; background: rgba(0, 255, 0, 0.1); padding: 10px; border-radius: 6px; margin-bottom: 16px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
</style>

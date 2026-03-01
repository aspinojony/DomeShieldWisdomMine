<template>
  <div class="app-container" v-if="authState.isLoggedIn">
    <header class="header">
      <div class="logo-area">
        <h1 class="glowing-text">穹盾智矿</h1>
        <span class="subtitle">露井联采空天地一体化智能预警中枢</span>
      </div>
      <div class="header-right">
        <div class="time-panel glowing-text">
          {{ currentTime }}
        </div>
        <div class="user-panel">
          <button v-if="authState.isEngineer" class="admin-btn" @click="toggleAdmin">
            <span class="icon">{{ isAdminPage ? '📊' : '⚙️' }}</span>
            {{ isAdminPage ? '返回大屏' : '管理中心' }}
          </button>
          <span class="divider" v-if="authState.isEngineer"></span>
          <span class="user-role-badge">{{ roleLabel }}</span>
          <span class="user-name">{{ authState.user?.full_name || authState.user?.username }}</span>
          <button class="logout-btn" @click="handleLogout">退出</button>
        </div>
      </div>
    </header>
    
    <main class="main-content">
      <router-view />
    </main>
  </div>

  <!-- 未登录时直接渲染登录页 -->
  <router-view v-else />
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authState, logout } from './auth'

const router = useRouter()
const route = useRoute()
const currentTime = ref('')
let timer = null

const roleLabel = computed(() => {
  const map = { admin: '管理员', engineer: '工程师', viewer: '观察员' }
  return map[authState.user?.role] || '未知'
})

const isAdminPage = computed(() => route.path.startsWith('/admin'))

const toggleAdmin = () => {
  if (isAdminPage.value) {
    router.push('/')
  } else {
    router.push('/admin')
  }
}

const handleLogout = () => {
  logout()
  router.push('/login')
}

onMounted(() => {
  timer = setInterval(() => {
    const now = new Date()
    currentTime.value = now.toLocaleTimeString('zh-CN', { hour12: false }) 
                        + ' ' + now.toLocaleDateString('zh-CN')
  }, 1000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 1rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1rem 2rem;
  background: linear-gradient(90deg, transparent, rgba(0, 240, 255, 0.1), transparent);
  border-bottom: 1px solid var(--border-neon);
  box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

.logo-area h1 {
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: 2px;
}

.subtitle {
  font-size: 0.9rem;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.time-panel {
  font-size: 1.2rem;
  letter-spacing: 2px;
}

.user-panel {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 14px;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.15);
  border-radius: 8px;
}

.admin-btn {
  background: transparent;
  border: 1px solid rgba(0, 240, 255, 0.3);
  color: #00f0ff;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  font-family: inherit;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}
.admin-btn:hover {
  background: rgba(0, 240, 255, 0.1);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
}

.divider {
  width: 1px;
  height: 16px;
  background: rgba(0, 240, 255, 0.3);
  margin: 0 4px;
}

.user-role-badge {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(0, 240, 255, 0.15);
  color: #00f0ff;
  font-weight: 600;
}

.user-name {
  color: #ccd6f6;
  font-size: 0.85rem;
}

.logout-btn {
  background: rgba(255, 60, 60, 0.15);
  border: 1px solid rgba(255, 60, 60, 0.3);
  color: #ff6b6b;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  font-family: inherit;
  transition: all 0.2s;
}
.logout-btn:hover {
  background: rgba(255, 60, 60, 0.3);
  box-shadow: 0 0 10px rgba(255, 60, 60, 0.2);
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}
</style>

<template>
  <div class="app-container" v-if="authState.isLoggedIn">
    <header class="cyber-header">
      <div class="header-left">
        <div class="title-bg"></div>
        <h1 class="glowing-text cyber-title">数字孪生矿山</h1>
      </div>
      
      <div class="header-center">
        <nav class="top-nav">
          <button 
            class="nav-btn" 
            :class="{ active: route.path === '/' }" 
            @click="router.push('/')"
          >
            <span>矿山总览</span>
          </button>
          <button 
            class="nav-btn" 
            :class="{ active: route.path === '/production' }" 
            @click="router.push('/production')"
          >
            <span>生产运营</span>
          </button>
          <button 
            class="nav-btn" 
            :class="{ active: route.path === '/intelligence' }" 
            @click="router.push('/intelligence')"
          >
            <span>智能识别</span>
          </button>
          <button 
            class="nav-btn" 
            :class="{ active: route.path === '/video' }" 
            @click="router.push('/video')"
          >
            <span>视频监控</span>
          </button>
        </nav>
      </div>

      <div class="header-right">
        <div class="time-panel glowing-text">
          {{ currentTime }}
        </div>
        <div class="user-panel">
          <button v-if="authState.isEngineer" class="admin-btn" @click="toggleAdmin">
            {{ isAdminPage ? '返回大屏' : '管理中心' }}
          </button>
          <span class="user-role-badge">{{ roleLabel }}</span>
          <span class="user-name">{{ authState.user?.full_name || authState.user?.username }}</span>
          <button class="logout-btn" @click="handleLogout">退出</button>
        </div>
      </div>
    </header>
    
    <!-- 全屏显示主视图 -->
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
                        + ' ' + now.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '.')
                        + ' 星期' + '日一二三四五六'.charAt(now.getDay())
  }, 1000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.app-container {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  overflow: hidden;
}

.cyber-header {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 60px;
  z-index: 1000;
  pointer-events: none; /* 让地图允许点击 */
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: linear-gradient(180deg, rgba(0, 16, 30, 0.9) 0%, rgba(0, 16, 30, 0) 100%);
}

.cyber-header > * {
  pointer-events: auto; /* 子元素可点击 */
}

.header-left {
  width: 320px;
  height: 50px;
  display: flex;
  align-items: center;
  padding-left: 20px;
  background: linear-gradient(90deg, rgba(0, 240, 255, 0.25) 0%, transparent 100%);
  clip-path: polygon(0 0, 100% 0, 90% 100%, 0 100%);
  border-bottom: 2px solid var(--primary-color);
  position: relative;
}

.cyber-title {
  font-size: 1.6rem;
  font-weight: bold;
  letter-spacing: 4px;
  margin: 0;
  color: #fff;
  text-shadow: 0 0 15px rgba(0, 240, 255, 0.8), 2px 2px 4px rgba(0, 0, 0, 0.8);
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
  padding-top: 10px;
}

.top-nav {
  display: flex;
  gap: 15px;
}

.nav-btn {
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.3);
  color: #fff;
  padding: 8px 22px;
  font-size: 0.95rem;
  font-family: inherit;
  font-weight: bold;
  cursor: pointer;
  transform: skewX(-25deg);
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
  white-space: nowrap;
}

.nav-btn span {
  display: block;
  transform: skewX(25deg); /* 文字扳正 */
}

.nav-btn.active, .nav-btn:hover {
  background: rgba(0, 240, 255, 0.2);
  box-shadow: 0 0 15px rgba(0, 240, 255, 0.4) inset;
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 15px;
  height: 50px;
  padding-right: 20px;
  padding-top: 10px;
}

.time-panel {
  font-size: 1.1rem;
  font-family: 'Orbitron', monospace;
  letter-spacing: 1px;
}

.user-panel {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 10px;
}

.user-role-badge {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(0, 240, 255, 0.15);
  color: #00f0ff;
}

.user-name {
  color: #ccd6f6;
  font-size: 0.9rem;
}

.admin-btn, .logout-btn {
  background: transparent;
  border: 1px solid rgba(0, 240, 255, 0.4);
  color: #00f0ff;
  padding: 3px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.logout-btn {
  border-color: rgba(255, 60, 60, 0.4);
  color: #ff6b6b;
}

.admin-btn:hover { background: rgba(0, 240, 255, 0.2); }
.logout-btn:hover { background: rgba(255, 60, 60, 0.3); }

.main-content {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 1; /* 底层显示，地图铺满 */
}
</style>

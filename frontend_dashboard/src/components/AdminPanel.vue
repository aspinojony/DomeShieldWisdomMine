<template>
  <div class="admin-layout">
    <!-- 左侧导航 -->
    <aside class="admin-sidebar">
      <div class="sidebar-header">
        <h2>系统管理</h2>
      </div>
      <nav class="admin-nav">
        <router-link to="/admin/devices" class="nav-item">
          <span class="icon">💻</span> 设备台账
        </router-link>
        <router-link to="/admin/rules" class="nav-item">
          <span class="icon">📐</span> 告警规则
        </router-link>
        <router-link to="/admin/records" class="nav-item">
          <span class="icon">🚨</span> 告警事件
        </router-link>
        <router-link to="/admin/uav" class="nav-item">
          <span class="icon">🛰️</span> UAV指控集群
        </router-link>
        <router-link to="/admin/users" class="nav-item" v-if="authState.isAdmin">
          <span class="icon">👥</span> 用户管理
        </router-link>
      </nav>
    </aside>

    <!-- 右侧内容区 -->
    <main class="admin-content">
      <div class="content-wrapper glass-panel">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { authState } from '../auth'
</script>

<style scoped>
.admin-layout {
  display: flex;
  width: 100%;
  height: 100%;
  gap: 20px;
}

.admin-sidebar {
  width: 240px;
  background: rgba(13, 27, 42, 0.6);
  border: 1px solid rgba(0, 240, 255, 0.15);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.2rem;
  color: #00f0ff;
  letter-spacing: 2px;
}

.admin-nav {
  padding: 15px 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: #ccd6f6;
  text-decoration: none;
  font-size: 0.95rem;
  border-radius: 8px;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.nav-item:hover {
  background: rgba(0, 240, 255, 0.05);
  border-color: rgba(0, 240, 255, 0.1);
  color: #fff;
}

.nav-item.router-link-active {
  background: linear-gradient(90deg, rgba(0, 240, 255, 0.15), transparent);
  border-left: 3px solid #00f0ff;
  border-right: 1px solid rgba(0, 240, 255, 0.1);
  border-top: 1px solid rgba(0, 240, 255, 0.1);
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
  color: #00f0ff;
  font-weight: 600;
}

.nav-item .icon {
  font-size: 1.2rem;
}

.admin-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0; 
}

.content-wrapper {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: rgba(13, 27, 42, 0.6);
  border: 1px solid rgba(0, 240, 255, 0.15);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}
</style>

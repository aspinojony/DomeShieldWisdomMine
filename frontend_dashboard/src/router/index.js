/**
 * 穹盾智矿 - 前端路由配置
 * 包含路由守卫：未登录自动跳转登录页
 */
import { createRouter, createWebHistory } from 'vue-router'
import { authState } from '../auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../components/LoginPage.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../components/MiningDashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/production',
    name: 'Production',
    component: () => import('../components/operations/OperationsDashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/intelligence',
    name: 'Intelligence',
    component: () => import('../components/IntelligentDetection.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/video',
    name: 'Video',
    component: () => import('../components/VideoMonitoring.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../components/AdminPanel.vue'),
    meta: { requiresAuth: true, requiresEngineer: true },
    redirect: '/admin/devices',
    children: [
      {
        path: 'devices',
        name: 'AdminDevices',
        component: () => import('../components/admin/AdminDeviceManage.vue')
      },
      {
        path: 'rules',
        name: 'AdminRules',
        component: () => import('../components/admin/AdminRuleManage.vue')
      },
      {
        path: 'records',
        name: 'AdminRecords',
        component: () => import('../components/admin/AdminAlertManage.vue')
      },
      {
        path: 'uav',
        name: 'AdminUAV',
        component: () => import('../components/admin/AdminUAVManage.vue')
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('../components/admin/AdminUserManage.vue'),
        meta: { requiresAdmin: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !authState.isLoggedIn) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && authState.isLoggedIn) {
    next({ name: 'Dashboard' })
  } else if (to.meta.requiresEngineer && !authState.isEngineer) {
    next({ name: 'Dashboard' }) // 非工程师强制返回大屏
  } else if (to.meta.requiresAdmin && !authState.isAdmin) {
    next({ name: 'AdminDevices' }) // 非管理员试图访问用户管理页时重定向
  } else {
    next()
  }
})

export default router

/**
 * 穹盾智矿 - 认证状态管理
 * 管理 JWT Token、当前用户信息、角色权限
 */
import { reactive } from 'vue'
import axios from 'axios'

import { API_ENDPOINTS } from './config/api'

const API_BIZ_BASE = API_ENDPOINTS.biz

// 全局认证状态
export const authState = reactive({
  token: localStorage.getItem('msm_token') || '',
  user: JSON.parse(localStorage.getItem('msm_user') || 'null'),
  get isLoggedIn() {
    return !!this.token
  },
  get isAdmin() {
    return this.user?.role === 'admin'
  },
  get isEngineer() {
    return this.user?.role === 'engineer' || this.user?.role === 'admin'
  }
})

/**
 * 用户登录
 */
export async function login(username, password) {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)

  const res = await axios.post(`${API_BIZ_BASE}/auth/login`, formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })

  const { access_token, user } = res.data
  authState.token = access_token
  authState.user = user

  localStorage.setItem('msm_token', access_token)
  localStorage.setItem('msm_user', JSON.stringify(user))

  // 设置 axios 全局默认 header
  axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

  return user
}

/**
 * 退出登录
 */
export function logout() {
  authState.token = ''
  authState.user = null
  localStorage.removeItem('msm_token')
  localStorage.removeItem('msm_user')
  delete axios.defaults.headers.common['Authorization']
}

/**
 * 初始化：页面刷新后从 localStorage 恢复 Token
 */
export function initAuth() {
  if (authState.token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${authState.token}`
  }
}

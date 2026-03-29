import axios from 'axios'
import router from '../router'
import { authState, logout } from '../auth'

export const http = axios.create({
  timeout: 10000,
})

http.interceptors.request.use((config) => {
  const token = authState.token || localStorage.getItem('msm_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    if (status === 401) {
      logout()
      if (router.currentRoute.value?.name !== 'Login') {
        router.push({ name: 'Login' })
      }
    }
    return Promise.reject(error)
  }
)

export const get = (url, config) => http.get(url, config)
export const post = (url, data, config) => http.post(url, data, config)
export const put = (url, data, config) => http.put(url, data, config)
export const del = (url, config) => http.delete(url, config)

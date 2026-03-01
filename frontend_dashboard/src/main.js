import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { initAuth } from './auth'

// 恢复登录状态
initAuth()

createApp(App).use(router).mount('#app')

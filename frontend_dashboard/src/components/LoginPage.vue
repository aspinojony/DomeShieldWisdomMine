<template>
  <div class="login-wrapper">
    <!-- 动态粒子背景 -->
    <canvas ref="particleCanvas" class="particle-bg"></canvas>

    <div class="login-card">
      <!-- Logo 与标题 -->
      <div class="login-header">
        <div class="logo-icon"></div>
        <h1 class="sys-name">穹盾智矿</h1>
        <p class="sys-desc">露井联采空天地一体化智能预警中枢</p>
      </div>

      <!-- 登录表单 -->
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="input-group" :class="{ focused: userFocused }">
          <span class="input-icon"></span>
          <input
            v-model="username"
            type="text"
            placeholder="用户名"
            autocomplete="username"
            @focus="userFocused = true"
            @blur="userFocused = false"
          />
        </div>

        <div class="input-group" :class="{ focused: passFocused }">
          <span class="input-icon"></span>
          <input
            v-model="password"
            :type="showPwd ? 'text' : 'password'"
            placeholder="密码"
            autocomplete="current-password"
            @focus="passFocused = true"
            @blur="passFocused = false"
          />
          <span class="pwd-toggle" @click="showPwd = !showPwd">
            {{ showPwd ? '' : '' }}
          </span>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

        <button type="submit" class="login-btn" :disabled="isLoading">
          <span v-if="!isLoading">进 入 系 统</span>
          <span v-else class="loading-spinner">认证中...</span>
        </button>
      </form>

      <!-- 底部信息 -->
      <div class="login-footer">
        <p>默认管理员: admin / admin123</p>
        <p class="copyright">© 2026 穹盾智矿 · 矿山安全生产智能管控平台</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../auth'

const router = useRouter()

const username = ref('')
const password = ref('')
const showPwd = ref(false)
const errorMsg = ref('')
const isLoading = ref(false)
const userFocused = ref(false)
const passFocused = ref(false)
const particleCanvas = ref(null)

let animFrameId = null

const handleLogin = async () => {
  errorMsg.value = ''
  if (!username.value || !password.value) {
    errorMsg.value = '请输入用户名和密码'
    return
  }
  isLoading.value = true
  try {
    await login(username.value, password.value)
    router.push('/')
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || '登录失败，请重试'
  } finally {
    isLoading.value = false
  }
}

// 粒子动画
const initParticles = () => {
  const canvas = particleCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  let particles = []
  const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight }
  resize()
  window.addEventListener('resize', resize)

  for (let i = 0; i < 80; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      r: Math.random() * 2 + 1
    })
  }

  const draw = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    particles.forEach((p, i) => {
      p.x += p.vx; p.y += p.vy
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1

      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, 2 * Math.PI)
      ctx.fillStyle = 'rgba(0, 240, 255, 0.5)'
      ctx.fill()

      // 连接线
      for (let j = i + 1; j < particles.length; j++) {
        const dx = p.x - particles[j].x
        const dy = p.y - particles[j].y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 120) {
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(particles[j].x, particles[j].y)
          ctx.strokeStyle = `rgba(0, 240, 255, ${0.15 * (1 - dist / 120)})`
          ctx.stroke()
        }
      }
    })
    animFrameId = requestAnimationFrame(draw)
  }
  draw()
}

onMounted(initParticles)
onUnmounted(() => { if (animFrameId) cancelAnimationFrame(animFrameId) })
</script>

<style scoped>
.login-wrapper {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a0e17 0%, #0d1b2a 40%, #1b2838 100%);
  position: relative;
  overflow: hidden;
}

.particle-bg {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  z-index: 0;
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: 45px 40px;
  background: rgba(13, 27, 42, 0.85);
  border: 1px solid rgba(0, 240, 255, 0.2);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  box-shadow:
    0 0 40px rgba(0, 240, 255, 0.08),
    0 25px 50px rgba(0, 0, 0, 0.5),
    inset 0 0 80px rgba(0, 240, 255, 0.02);
  animation: cardEntry 0.6s ease-out;
}

@keyframes cardEntry {
  from { opacity: 0; transform: translateY(30px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.login-header {
  text-align: center;
  margin-bottom: 35px;
}

.logo-icon {
  font-size: 3rem;
  margin-bottom: 10px;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { filter: drop-shadow(0 0 8px rgba(0, 240, 255, 0.5)); }
  50% { filter: drop-shadow(0 0 20px rgba(0, 240, 255, 0.9)); }
}

.sys-name {
  font-family: 'Orbitron', 'Inter', sans-serif;
  font-size: 2rem;
  color: #00f0ff;
  text-shadow: 0 0 20px rgba(0, 240, 255, 0.5);
  margin: 0;
  letter-spacing: 4px;
}

.sys-desc {
  color: #8892b0;
  font-size: 0.85rem;
  margin-top: 8px;
  letter-spacing: 1px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.input-group {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 0 15px;
  transition: all 0.3s;
}

.input-group.focused {
  border-color: rgba(0, 240, 255, 0.5);
  box-shadow: 0 0 15px rgba(0, 240, 255, 0.1);
  background: rgba(0, 240, 255, 0.02);
}

.input-icon {
  font-size: 1.1rem;
  margin-right: 12px;
  opacity: 0.7;
}

.input-group input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #e6f1ff;
  font-size: 0.95rem;
  padding: 14px 0;
  font-family: 'Inter', sans-serif;
}

.input-group input::placeholder {
  color: #556677;
}

.pwd-toggle {
  cursor: pointer;
  font-size: 1.1rem;
  opacity: 0.6;
  transition: opacity 0.2s;
}
.pwd-toggle:hover { opacity: 1; }

.error-msg {
  color: #ff4444;
  font-size: 0.85rem;
  text-align: center;
  padding: 8px;
  background: rgba(255, 0, 0, 0.08);
  border-radius: 6px;
  border: 1px solid rgba(255, 0, 0, 0.2);
}

.login-btn {
  margin-top: 8px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.15), rgba(0, 150, 255, 0.25));
  border: 1px solid rgba(0, 240, 255, 0.4);
  border-radius: 10px;
  color: #00f0ff;
  font-size: 1rem;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  cursor: pointer;
  letter-spacing: 4px;
  transition: all 0.3s;
}

.login-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.25), rgba(0, 150, 255, 0.4));
  box-shadow: 0 0 25px rgba(0, 240, 255, 0.3);
  transform: translateY(-1px);
}

.login-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

.loading-spinner {
  animation: blink 1s infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.login-footer {
  text-align: center;
  margin-top: 30px;
  color: #556677;
  font-size: 0.75rem;
  line-height: 1.8;
}
.login-footer p { margin: 0; }
.copyright { margin-top: 8px !important; opacity: 0.6; }
</style>

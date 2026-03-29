const host = window.location.hostname

export const API_ENDPOINTS = {
  sensor: import.meta.env.VITE_API_SENSOR_BASE || `http://${host}:8000/api/v1`,
  ai: import.meta.env.VITE_API_AI_BASE || `http://${host}:8001/api/v1`,
  biz: import.meta.env.VITE_API_BIZ_BASE || `http://${host}:8002/api/v1`,
  vision: import.meta.env.VITE_API_VISION_BASE || `http://${host}:8003/api/v1`,
}

export const API_ORIGIN = {
  sensor: API_ENDPOINTS.sensor.replace(/\/api\/v1$/, ''),
  ai: API_ENDPOINTS.ai.replace(/\/api\/v1$/, ''),
  biz: API_ENDPOINTS.biz.replace(/\/api\/v1$/, ''),
  vision: API_ENDPOINTS.vision.replace(/\/api\/v1$/, ''),
}

export const DEMO_MODE = (import.meta.env.VITE_DEMO_MODE || 'false') === 'true'

export function withDemoFlag(payload, fallback = false) {
  return {
    ...payload,
    _demo: DEMO_MODE || fallback,
  }
}

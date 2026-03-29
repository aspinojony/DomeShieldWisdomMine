export const demoSensorLatest = {
  status: 'success',
  message: '演示模式数据',
  data: [
    { device_id: 'CM-001', device_type: 'crack_meter', crack_width_mm: 6.8, last_update: '2026-03-29 11:00:00' },
    { device_id: 'MS-001', device_type: 'micro_seismic', energy_level: 42.5, last_update: '2026-03-29 11:00:10' },
    { device_id: 'IN-001', device_type: 'inclinometer', angle_x: 1.2, last_update: '2026-03-29 11:00:20' },
    { device_id: 'ST-001', device_type: 'settlement', settlement_mm: 4.6, last_update: '2026-03-29 11:00:30' }
  ]
}

export const demoSensorHistory = (deviceId) => ({
  status: 'success',
  device_id: deviceId,
  data: Array.from({ length: 12 }, (_, i) => ({
    field: 'value',
    value: Number((Math.random() * 10 + 2).toFixed(2)),
    time: `${String(i * 5).padStart(2, '0')}:00`
  }))
})

export const demoVisionHistory = [
  {
    id: 'VISION-001',
    image_url: '/results/crack_demo_1.jpg',
    timestamp: '2026-03-29 10:58:00',
    max_width_mm: 8.4,
    anomalies_found: 3,
    alert_level: '二级预警'
  },
  {
    id: 'VISION-002',
    image_url: '/results/crack_demo_2.jpg',
    timestamp: '2026-03-29 10:49:00',
    max_width_mm: 5.2,
    anomalies_found: 2,
    alert_level: '一级监控'
  }
]

import { defineStore } from 'pinia'
import axios from 'axios'
import { authState } from '../auth'

const API_BIZ_BASE = `http://${window.location.hostname}:8002/api/v1`

const mockFleet = [
  { device_id: 'TRK-001', device_name: '卡车 TRK-01', location: { lng: 110.122, lat: 35.122 }, telemetry: { speed: 42.5 }, status: 'online' },
  { device_id: 'TRK-002', device_name: '卡车 TRK-02', location: { lng: 110.125, lat: 35.126 }, telemetry: { speed: 12.0 }, status: 'online' },
  { device_id: 'EXC-001', device_name: '挖机 EXC-01', location: { lng: 110.118, lat: 35.118 }, telemetry: { speed: 2.5 }, status: 'online' }
]

const mockTasks = [
  { id: 1, task_id: '1024', load_zone: 'PIT-01', unload_zone: 'CRS-02', vehicle_id: 'AUT-001', weight_tons: 85, status: 'hauling' },
  { id: 2, task_id: '1025', load_zone: 'PIT-03', unload_zone: 'CRS-01', vehicle_id: 'AUT-005', weight_tons: 72, status: 'loading' },
  { id: 3, task_id: '1026', load_zone: 'CRS-01', unload_zone: 'PIT-01', vehicle_id: 'AUT-002', weight_tons: 0, status: 'returning' }
]

const mockLeaderboard = [
  { vehicle_id: 'AUT-001', total_tonnage: 1250 },
  { vehicle_id: 'AUT-004', total_tonnage: 1180 },
  { vehicle_id: 'AUT-003', total_tonnage: 1020 },
  { vehicle_id: 'AUT-002', total_tonnage: 940 },
  { vehicle_id: 'AUT-005', total_tonnage: 810 }
]

export const useOperationsStore = defineStore('operations', {
  state: () => ({
    kpi: { total_tonnage: 830.7, avg_efficiency: 81.85, total_fuel: 2250, active_vehicle_count: 10, daily_trend: [] },
    fleet: [],
    activeTasks: [],
    leaderboard: [],
    loadingError: false
  }),
  getters: {
    displayFleet: (state) => state.fleet.length ? state.fleet : mockFleet,
    displayTasks: (state) => state.activeTasks.length ? state.activeTasks : mockTasks,
    displayLeaderboard: (state) => state.leaderboard.length ? state.leaderboard : mockLeaderboard,
    kpiSummary: (state) => ({
      '当日产量': state.kpi.total_tonnage + ' T',
      '作业效率': state.kpi.avg_efficiency + ' T/H',
      '燃料消耗': state.kpi.total_fuel + ' L',
      '在线载具': state.kpi.active_vehicle_count + ' UNIT'
    })
  },
  actions: {
    async fetchAllData() {
      try {
        const config = { headers: { Authorization: `Bearer ${authState.token}` } }
        const [resKpi, resFleet, resTasks, resLeader] = await Promise.all([
          axios.get(`${API_BIZ_BASE}/ops/production-kpi`, config),
          axios.get(`${API_BIZ_BASE}/ops/fleet/status`, config),
          axios.get(`${API_BIZ_BASE}/ops/tasks/active`, config),
          axios.get(`${API_BIZ_BASE}/ops/stats/efficiency-leaderboard`, config)
        ])
        
        this.kpi = resKpi.data
        this.fleet = resFleet.data
        this.activeTasks = resTasks.data
        this.leaderboard = resLeader.data.slice(0, 5)
        this.loadingError = false
      } catch (err) {
        console.warn('Backend unavailable, using mock data baseline.', err)
        this.loadingError = true
      }
    }
  }
})

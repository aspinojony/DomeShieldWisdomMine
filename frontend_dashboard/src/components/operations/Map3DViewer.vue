<template>
  <div class="map-immersive-background" ref="mapContainer"></div>

  <!-- HUD Markers overlay synchronized with 3D map -->
  <div 
    v-for="v in store.displayFleet" 
    :key="v.device_id"
    class="vehicle-hud-marker"
    :style="getMarkerStyle(v.device_id)"
    v-show="isMarkerVisible(v.device_id)"
  >
    <div class="marker-base">
      <div class="pulse-ring"></div>
      <div class="crosshair"></div>
    </div>
    <div class="hud-lead-line"></div>
    <div class="hud-tag premium-tag">
      <div class="tag-header">
        <span class="v-id">{{ v.device_name }}</span>
        <span class="status-dot green"></span>
      </div>
      <div class="tag-body">
        <div class="data-group">
          <span class="label">速度</span>
          <span class="val">{{ v.telemetry.speed }}<small>KM/H</small></span>
        </div>
        <div class="data-group">
          <span class="label">标高</span>
          <span class="val">420<small>M</small></span>
        </div>
      </div>
    </div>
  </div>

  <!-- Center HUD Reticle (New) -->
  <div class="center-hud-reticle">
    <div class="reticle-circle outer"></div>
    <div class="reticle-circle inner"></div>
    <div class="reticle-crosshair horizontal"></div>
    <div class="reticle-crosshair vertical"></div>
    <div class="reticle-coords">
      <div>LAT: 39.6358 N</div>
      <div>LNG: 109.8402 E</div>
      <div>ALT: 1,420 M</div>
    </div>
    <div class="reticle-status">MAP / ACTIVE</div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useOperationsStore } from '../../store/operations'
import * as Cesium from 'cesium'

const store = useOperationsStore()
const mapContainer = ref(null)
let viewer = null
const markerPositions = ref({})
let renderLoop = null

const initCesium = () => {
  if (!mapContainer.value) return
  
  Cesium.Ion.defaultAccessToken = '' // Local/Custom maps don't need Ion token by default if using offline tiles

  viewer = new Cesium.Viewer(mapContainer.value, {
    animation: false,
    baseLayerPicker: false,
    fullscreenButton: false,
    geocoder: false,
    homeButton: false,
    infoBox: false,
    sceneModePicker: false,
    selectionIndicator: false,
    timeline: false,
    navigationHelpButton: false,
    scene3DOnly: true,
    requestRenderMode: true, // Performance optimization
    maximumRenderTimeChange: Infinity
  })

  // Disable default UI classes
  viewer.cesiumWidget.creditContainer.style.display = 'none'

  // Set dark cyber theme background
  viewer.scene.backgroundColor = Cesium.Color.fromCssColorString('#02060c')
  viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString('#0f172a')
  
  // Set initial camera to look at the mock mining area (lng 110.12, lat 35.12)
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(110.12, 35.11, 4000),
    orientation: {
      heading: Cesium.Math.toRadians(0),
      pitch: Cesium.Math.toRadians(-45),
      roll: 0.0
    },
    duration: 0 // instantly jump there
  })

  // Start tracking screen positions for HTML overlays
  renderLoop = () => {
    updateMarkerPositions()
    requestAnimationFrame(renderLoop)
  }
  requestAnimationFrame(renderLoop)
}

const updateMarkerPositions = () => {
  if (!viewer) return
  const newPositions = {}
  store.displayFleet.forEach(vehicle => {
    const position = Cesium.Cartesian3.fromDegrees(vehicle.location.lng, vehicle.location.lat, 420)
    const canvasPosition = Cesium.SceneTransforms.wgs84ToWindowCoordinates(viewer.scene, position)
    if (Cesium.defined(canvasPosition)) {
      newPositions[vehicle.device_id] = { x: canvasPosition.x, y: canvasPosition.y }
    }
  })
  markerPositions.value = newPositions
}

const getMarkerStyle = (id) => {
  const pos = markerPositions.value[id]
  if (!pos) return { display: 'none' }
  return { left: `${pos.x}px`, top: `${pos.y}px` }
}

const isMarkerVisible = (id) => {
  return markerPositions.value[id] !== undefined
}

watch(() => store.displayFleet, () => {
  if (viewer) viewer.scene.requestRender()
}, { deep: true })

onMounted(() => {
  initCesium()
})

onUnmounted(() => {
  if (renderLoop) cancelAnimationFrame(renderLoop)
  if (viewer) viewer.destroy()
})
</script>

<style scoped>
.map-immersive-background {
  position: absolute; inset: 0; z-index: 1;
}

/* Vehicle OSD Premium Style Overlay */
.vehicle-hud-marker {
  position: absolute; z-index: 100;
  transform: translate(-50%, -100%);
  pointer-events: none; /* Let clicks pass through to 3D map */
  filter: drop-shadow(0 0 10px rgba(0, 240, 255, 0.4));
}
.marker-base { position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); display:flex; justify-content:center; align-items:center; }
.pulse-ring {
  position: absolute;
  width: 50px; height: 50px; border-radius: 50%;
  border: 1px solid rgba(0, 240, 255, 0.6);
  transform: scale(0.5) rotateX(75deg); animation: sonar 2s infinite cubic-bezier(0.1, 0.8, 0.3, 1);
}
.crosshair {
  width: 20px; height: 20px;
  border-top: 1px solid #00f0ff; border-left: 1px solid #00f0ff;
  transform: rotateX(75deg) rotateZ(45deg);
  position: absolute;
}

@keyframes sonar { from { transform: scale(0.5) rotateX(75deg); opacity: 1; } to { transform: scale(2) rotateX(75deg); opacity: 0; } }

.hud-lead-line {
  width: 1px; height: 80px;
  background: linear-gradient(to top, rgba(0, 240, 255, 0.8) 10%, transparent);
  margin: 0 auto;
}

.premium-tag {
  background: rgba(10, 25, 47, 0.8);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(0, 240, 255, 0.3);
  border-left: 3px solid #00f0ff;
  padding: 8px 12px; border-radius: 2px; width: 140px;
  box-shadow: inset 0 0 10px rgba(0, 240, 255, 0.1), 0 5px 15px rgba(0,0,0,0.8);
  pointer-events: auto; /* Allow interaction on the tag itself if needed */
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%);
}
.tag-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; border-bottom: 1px dashed rgba(0,240,255,0.2); padding-bottom: 4px; }
.v-id { font-family: 'Orbitron', monospace; font-size: 11px; font-weight: 800; color: #fff; letter-spacing: 1px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; }
.status-dot.green { background-color: #00ff88; box-shadow: 0 0 8px #00ff88; }
.tag-body { display: flex; justify-content: space-between; }
.data-group { display: flex; flex-direction: column; }
.data-group .label { font-size: 8px; color: #8892b0; letter-spacing: 1px; }
.data-group .val { font-family: 'Orbitron', monospace; font-size: 13px; color: #00f0ff; font-weight: 800; text-shadow: 0 0 5px rgba(0,240,255,0.5); }
.data-group small { font-size: 8px; margin-left: 2px; opacity:0.8;}

/* Center HUD Reticle */
.center-hud-reticle {
  position: absolute; top: 50%; left: 50%; width: 400px; height: 400px;
  transform: translate(-50%, -50%); pointer-events: none; z-index: 50;
  display: flex; justify-content: center; align-items: center;
  opacity: 0.4;
}
.reticle-circle { position: absolute; border-radius: 50%; border: 1px dashed #00f0ff; }
.reticle-circle.outer { width: 300px; height: 300px; animation: spin 20s linear infinite; }
.reticle-circle.inner { width: 260px; height: 260px; border-style: dotted; animation: spin-reverse 15s linear infinite; opacity: 0.6; }
.reticle-crosshair { position: absolute; background: rgba(0, 240, 255, 0.4); }
.reticle-crosshair.horizontal { width: 320px; height: 1px; }
.reticle-crosshair.vertical { width: 1px; height: 320px; }

.reticle-coords {
  position: absolute; top: 50%; left: 50%; transform: translate(160px, -20px);
  font-family: 'Orbitron', monospace; font-size: 10px; color: #00f0ff;
  display: flex; flex-direction: column; gap: 4px; text-shadow: 0 0 5px rgba(0,240,255,0.8);
}
.reticle-status {
  position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
  font-family: 'Orbitron', monospace; font-size: 10px; color: #00f0ff; letter-spacing: 2px;
}

@keyframes spin { 100% { transform: rotate(360deg); } }
@keyframes spin-reverse { 100% { transform: rotate(-360deg); } }
</style>

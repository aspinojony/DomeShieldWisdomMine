<template>
  <div class="ht-detail-overlay" v-if="equipment">
    <div class="ht-container-header">
      <h3>设备精细化模型: {{ equipment.name }}</h3>
      <button @click="$emit('close')" class="close-btn">×</button>
    </div>
    <div ref="htContainer" class="ht-canvas-container">
      <!-- HT Graph3dView will be mounted here -->
    </div>
    <div class="ht-side-info">
      <div class="info-card">
        <h4>实时状态监测</h4>
        <div class="status-row"><span>转速:</span> <span class="text-cyan">23.5 HZ</span></div>
        <div class="status-row"><span>负载:</span> <span class="text-blue">82%</span></div>
        <div class="status-row"><span>振动:</span> <span class="text-green">正常</span></div>
      </div>
      <div class="action-buttons">
        <button class="action-btn">视角复位</button>
        <button class="action-btn danger">紧急停机</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch, onBeforeUnmount } from 'vue';

const props = defineProps({
  equipment: Object
});

const emit = defineEmits(['close']);
const htContainer = ref(null);
let g3d = null;
let dataModel = null;

const initHT = () => {
  if (!window.ht) {
    console.warn("HT for Web library not found. Please ensure ht.js is loaded.");
    // Mocking the container for demo if HT is missing
    htContainer.value.innerHTML = `
      <div class="ht-mock-view">
        <div class="cube-placeholder">3D HT MODEL MOCK</div>
        <p>正在加载 ${props.equipment?.name} 的高精度交互模型...</p>
      </div>
    `;
    return;
  }

  // 1. 初始化 HT 核心组件
  dataModel = new ht.DataModel();
  g3d = new ht.graph3d.Graph3dView(dataModel);
  
  // 2. 将视图添加到容器
  const view = g3d.getView();
  view.style.width = '100%';
  view.style.height = '100%';
  htContainer.value.appendChild(view);

  // 3. 模拟创建一个 3D 设备节点
  const node = new ht.Node();
  node.setName(props.equipment.name);
  node.setTag('MAIN_EQUIP');
  node.s({
    'shape3d': 'box',
    'shape3d.color': '#00f0ff',
    'label.visible': true,
    'label.background': 'rgba(0,0,0,0.5)',
    'label.position': 17
  });
  node.p3(0, 50, 0);
  node.s3(100, 100, 200);
  dataModel.add(node);

  // 4. 设置交互监听
  g3d.addInteractorListener((e) => {
    if (e.kind === 'clickData') {
      console.log('点击了设备组件:', e.data.getName());
    }
  });

  // 5. 视角自动定位
  g3d.flyTo(node, { animation: true, distance: 800 });
};

onMounted(() => {
  initHT();
});

onBeforeUnmount(() => {
  if (g3d) {
    g3d.dm().clear();
    g3d.dispose();
  }
});

watch(() => props.equipment, () => {
  if (dataModel) {
    dataModel.clear();
    initHT();
  }
});
</script>

<style scoped>
.ht-detail-overlay {
  position: fixed;
  top: 10%;
  left: 10%;
  width: 80%;
  height: 80%;
  background: rgba(13, 27, 42, 0.95);
  border: 1px solid #00f0ff;
  border-radius: 12px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  box-shadow: 0 0 50px rgba(0, 0, 0, 0.8);
  animation: scale-up 0.3s ease-out;
}

.ht-container-header {
  padding: 15px 20px;
  background: rgba(0, 240, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(0, 240, 255, 0.3);
}

.ht-container-header h3 {
  margin: 0;
  color: #00f0ff;
  font-family: 'Orbitron', sans-serif;
  letter-spacing: 1px;
}

.close-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 2rem;
  cursor: pointer;
  line-height: 1;
}

.ht-canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.ht-side-info {
  position: absolute;
  top: 80px;
  right: 20px;
  width: 260px;
  background: rgba(0, 15, 30, 0.8);
  border: 1px solid rgba(0, 240, 255, 0.2);
  border-radius: 8px;
  padding: 15px;
  pointer-events: auto;
}

.info-card h4 {
  margin-top: 0;
  color: #ccd6f6;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-bottom: 8px;
}

.status-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action-btn {
  padding: 8px;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid #00f0ff;
  color: #00f0ff;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #00f0ff;
  color: #111;
}

.action-btn.danger {
  border-color: #ff003c;
  color: #ff003c;
}

.action-btn.danger:hover {
  background: #ff003c;
  color: #fff;
}

.ht-mock-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #555;
}

.cube-placeholder {
  width: 200px;
  height: 200px;
  border: 4px dashed #00f0ff;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #00f0ff;
  font-weight: bold;
  animation: rotate-3d 5s linear infinite;
}

@keyframes rotate-3d {
  from { transform: perspective(500px) rotateY(0deg); }
  to { transform: perspective(500px) rotateY(360deg); }
}

@keyframes scale-up {
  from { transform: scale(0.8); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>

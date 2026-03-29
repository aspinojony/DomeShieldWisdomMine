<template>
  <div>
    <div class="panel-header-cyber sub-header">
      <div style="display:flex; align-items:center;">
         <div class="title-deco"></div>
         <span class="glowing-text">矿区微气象与环境感知</span>
      </div>
    </div>
    <div class="panel-inner environment-grid">
      <div class="env-item">
        <span class="label">空气质量</span>
        <span class="val green">32</span>
      </div>
      <div class="env-item">
        <span class="label">风速</span>
        <span class="val">4.2 m/s</span>
      </div>
      <div class="env-item">
        <span class="label">湿度</span>
        <span class="val">45%</span>
      </div>
      <div class="env-item">
        <span class="label">温度</span>
        <span class="val">18.5°C</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.environment-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 5px; }
.env-item {
  background: rgba(0, 240, 255, 0.03); padding: 12px; border-radius: 4px;
  display: flex; flex-direction: column; gap: 5px; 
  border: 1px solid rgba(0, 240, 255, 0.1);
  box-shadow: inset 0 0 10px rgba(0, 240, 255, 0.05);
  transition: all 0.3s;
}
.env-item:hover { background: rgba(0, 240, 255, 0.1); border-color: rgba(0, 240, 255, 0.4); }
.env-item .label { font-size: 10px; font-weight: 800; color: #8892b0; letter-spacing: 1px; }
.env-item .val { font-size: 16px; font-weight: 900; color: #cdd6f4; font-family: 'Orbitron', monospace; text-shadow: 0 0 8px rgba(255, 255, 255, 0.3); }
.env-item .val.green { color: #00ff88; text-shadow: 0 0 8px rgba(0,255,136,0.4); }
</style>

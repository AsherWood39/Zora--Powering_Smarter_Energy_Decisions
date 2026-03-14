<template>
  <div class="detail-container">
    <!-- Header / Back button -->
    <div class="detail-header">
      <button class="back-btn" @click="$emit('go-back')">
        <span class="material-icons-round">arrow_back</span> Fleet
      </button>
      <div class="battery-title">
        <span class="material-icons-round title-icon">battery_charging_full</span>
        <h2>{{ batteryId }}</h2>
        <span class="status-pill" :class="data?.status">{{ data?.regime }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="skeleton tall"></div>
      <div class="skeleton short"></div>
    </div>

    <template v-else-if="data">
      <!-- KPI strip -->
      <div class="kpi-strip">
        <div class="kpi-item">
          <div class="kpi-label">State of Health</div>
          <div class="kpi-value" :class="data.status">{{ data.soh.toFixed(1) }}%</div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item">
          <div class="kpi-label">RUL</div>
          <div class="kpi-value">{{ simulatedRul }} <span class="kpi-unit">cycles</span></div>
          <div class="kpi-sub">~{{ simulatedMonths }} months</div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item">
          <div class="kpi-label">Total Cycles</div>
          <div class="kpi-value">{{ data.total_cycles }}</div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item">
          <div class="kpi-label">Temperature</div>
          <div class="kpi-value">{{ data.temperature }}°C</div>
        </div>
      </div>

      <!-- SoH Curve Chart -->
      <div class="card chart-card">
        <div class="card-header">
          <h3>SoH Degradation Curve</h3>
          <span class="chart-sub">Last 50 cycles</span>
        </div>
        <div class="chart-wrap">
          <canvas :id="`soh-chart-${batteryId}`"></canvas>
        </div>
      </div>

      <!-- Regime Timeline -->
      <div class="card">
        <div class="card-header">
          <h3>Regime Timeline</h3>
          <div class="regime-legend">
            <span class="leg normal">🟢 Normal</span>
            <span class="leg accelerated">🟡 Accelerated</span>
            <span class="leg anomalous">🔴 Anomalous</span>
          </div>
        </div>
        <div class="regime-bar">
          <div
            v-for="(regime, i) in data.regime_history"
            :key="i"
            class="regime-segment"
            :class="regime.toLowerCase()"
            :title="`Cycle ${data.cycle_labels[i]}: ${regime}`"
          ></div>
        </div>
        <div class="regime-labels">
          <span>{{ data.cycle_labels[0] }}</span>
          <span>{{ data.cycle_labels[data.cycle_labels.length - 1] }}</span>
        </div>
      </div>

      <!-- Temperature Slider -->
      <div class="card temp-card">
        <div class="card-header">
          <h3>🌡️ Temperature Scenario</h3>
          <span class="chart-sub">Drag to see RUL impact</span>
        </div>

        <div class="slider-section">
          <div class="slider-labels">
            <span>-10°C</span>
            <span class="current-temp">{{ sliderTemp }}°C</span>
            <span>45°C</span>
          </div>
          <input
            type="range"
            min="-10"
            max="45"
            step="1"
            v-model.number="sliderTemp"
            class="temp-slider"
            @input="onTempChange"
          />
        </div>

        <div class="temp-result" v-if="simResult">
          <div class="temp-result-row">
            <div class="result-box">
              <div class="result-label">Base RUL</div>
              <div class="result-value">{{ simResult.base_rul }} cycles</div>
            </div>
            <div class="result-arrow">
              <span class="material-icons-round">arrow_forward</span>
            </div>
            <div class="result-box adjusted">
              <div class="result-label">At {{ sliderTemp }}°C</div>
              <div class="result-value" :class="{'warn': simResult.temp_impact_pct > 20}">
                {{ simResult.adjusted_rul }} cycles
              </div>
              <div class="result-sub" v-if="simResult.temp_impact_pct > 0">
                ↓ {{ simResult.temp_impact_pct }}% reduction
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="error-state">Battery not found.</div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
import axios from 'axios';
import Chart from 'chart.js/auto';

const props = defineProps({ batteryId: String });
const emit  = defineEmits(['go-back']);

const data      = ref(null);
const loading   = ref(true);
const sliderTemp = ref(24);
const simResult  = ref(null);
const simulatedRul    = ref(null);
const simulatedMonths = ref(null);

let chartInstance = null;

// Fetch battery health on mount
onMounted(async () => {
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/battery/${props.batteryId}/health`);
    data.value = res.data;
    sliderTemp.value = res.data.temperature;
    simulatedRul.value = res.data.rul;
    simulatedMonths.value = res.data.rul_months;

    await nextTick();
    renderChart();
    await fetchSimulation(sliderTemp.value);
  } catch (e) {
    console.error('Battery detail fetch error:', e);
  } finally {
    loading.value = false;
  }
});

// Debounce slider
let debounceTimer = null;
const onTempChange = () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => fetchSimulation(sliderTemp.value), 300);
};

const fetchSimulation = async (temp) => {
  try {
    const res = await axios.get(
      `http://127.0.0.1:5000/api/battery/${props.batteryId}/simulate?temp=${temp}`
    );
    simResult.value = res.data;
    simulatedRul.value = res.data.adjusted_rul;
    simulatedMonths.value = res.data.adjusted_rul_months;
  } catch (e) {
    console.error('Simulation error:', e);
  }
};

const renderChart = () => {
  const canvas = document.getElementById(`soh-chart-${props.batteryId}`);
  if (!canvas || !data.value || !data.value.chart_data) return;

  if (chartInstance) chartInstance.destroy();

  const ctx = canvas.getContext('2d');
  
  // Historical Gradient
  const histGradient = ctx.createLinearGradient(0, 0, 0, 250);
  histGradient.addColorStop(0, 'rgba(16, 185, 129, 0.2)');
  histGradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

  // Predicted Gradient
  const predGradient = ctx.createLinearGradient(0, 0, 0, 250);
  predGradient.addColorStop(0, 'rgba(245, 158, 11, 0.15)');
  predGradient.addColorStop(1, 'rgba(245, 158, 11, 0.0)');

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.value.chart_data.labels,
      datasets: [
        {
          label: 'Historical Capacity',
          data: data.value.chart_data.datasets[0].data,
          borderColor: '#10b981',
          backgroundColor: histGradient,
          borderWidth: 2.5,
          fill: true,
          pointRadius: 0,
          tension: 0.4,
        },
        {
          label: 'Predicted Degradation',
          data: data.value.chart_data.datasets[1].data,
          borderColor: '#f59e0b',
          backgroundColor: predGradient,
          borderWidth: 2.5,
          borderDash: [5, 5],
          fill: true,
          pointRadius: 0,
          tension: 0.4,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          mode: 'index', intersect: false,
          backgroundColor: '#1e293b',
          titleColor: '#f8fafc',
          bodyColor: '#cbd5e1',
          borderColor: '#334155',
          borderWidth: 1,
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#64748b', maxTicksLimit: 8 } },
        y: {
          grid: { color: '#334155', borderDash: [2, 4] },
          ticks: { color: '#64748b', callback: v => v + '%' },
          // Smarter Y axis scaling
          suggestedMin: 60,
          suggestedMax: 100
        }
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
      }
    }
  });
};
</script>

<style scoped>
.detail-container { padding: 0; }

/* Header */
.detail-header {
  display: flex; align-items: center; gap: 1.2rem;
  margin-bottom: 1.4rem;
}
.back-btn {
  display: flex; align-items: center; gap: 0.3rem;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  color: #94a3b8; border-radius: 8px;
  padding: 0.4rem 0.8rem; cursor: pointer;
  font-size: 0.82rem; font-weight: 600;
  transition: all 0.2s;
}
.back-btn:hover { background: rgba(255,255,255,0.1); color: #e2e8f0; }
.back-btn .material-icons-round { font-size: 1rem !important; }

.battery-title {
  display: flex; align-items: center; gap: 0.6rem;
}
.battery-title h2 {
  font-size: 1.3rem; font-weight: 800;
  color: #f1f5f9; margin: 0; font-family: monospace;
}
.title-icon { color: #818cf8; font-size: 1.4rem !important; }

.status-pill {
  font-size: 0.7rem; font-weight: 700;
  padding: 0.2rem 0.6rem; border-radius: 20px;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.status-pill.critical { background: rgba(239,68,68,0.2); color: #f87171; }
.status-pill.warning  { background: rgba(245,158,11,0.2); color: #fbbf24; }
.status-pill.good     { background: rgba(16,185,129,0.2); color: #34d399; }

/* KPI Strip */
.kpi-strip {
  display: flex; align-items: center;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px;
  padding: 1rem 1.5rem;
  margin-bottom: 1rem;
  gap: 1.5rem;
}
.kpi-divider { width: 1px; height: 36px; background: rgba(255,255,255,0.08); }
.kpi-item    { flex: 1; text-align: center; }
.kpi-label   { font-size: 0.72rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-value   { font-size: 1.3rem; font-weight: 800; color: #e2e8f0; margin-top: 0.2rem; }
.kpi-value.critical { color: #f87171; }
.kpi-value.warning  { color: #fbbf24; }
.kpi-value.good     { color: #34d399; }
.kpi-unit    { font-size: 0.75rem; font-weight: 500; color: #64748b; }
.kpi-sub     { font-size: 0.7rem; color: #64748b; margin-top: 0.1rem; }

/* Cards */
.card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px; padding: 1.1rem 1.3rem;
  margin-bottom: 1rem;
}
.card-header {
  display: flex; align-items: center;
  justify-content: space-between; margin-bottom: 0.9rem;
}
.card-header h3 { font-size: 0.95rem; font-weight: 700; color: #f1f5f9; margin: 0; }
.chart-sub { font-size: 0.72rem; color: #64748b; }

/* Chart */
.chart-wrap { position: relative; height: 200px; width: 100%; }

/* Regime Timeline */
.regime-bar {
  display: flex; height: 18px; border-radius: 8px;
  overflow: hidden; gap: 1px;
}
.regime-segment {
  flex: 1;
  transition: opacity 0.2s;
}
.regime-segment:hover { opacity: 0.7; }
.regime-segment.normal      { background: #10b981; }
.regime-segment.accelerated { background: #f59e0b; }
.regime-segment.anomalous   { background: #ef4444; }

.regime-labels {
  display: flex; justify-content: space-between;
  margin-top: 0.4rem;
  font-size: 0.68rem; color: #475569;
}
.regime-legend {
  display: flex; gap: 0.8rem;
}
.leg { font-size: 0.7rem; color: #64748b; }

/* Temperature Slider */
.slider-section { margin-bottom: 1rem; }
.slider-labels {
  display: flex; justify-content: space-between;
  font-size: 0.75rem; color: #64748b;
  margin-bottom: 0.4rem;
}
.current-temp {
  font-weight: 800; font-size: 1rem; color: #e2e8f0;
}
.temp-slider {
  width: 100%; -webkit-appearance: none;
  height: 6px; border-radius: 4px;
  background: linear-gradient(90deg, #3b82f6, #818cf8, #f59e0b, #ef4444);
  outline: none; cursor: pointer;
}
.temp-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px; height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4);
  cursor: pointer;
  transition: transform 0.15s;
}
.temp-slider::-webkit-slider-thumb:hover { transform: scale(1.2); }

.temp-result-row {
  display: flex; align-items: center; gap: 1rem;
}
.result-box {
  flex: 1; text-align: center;
  background: rgba(255,255,255,0.04);
  border-radius: 10px; padding: 0.8rem;
}
.result-box.adjusted { border: 1px solid rgba(99,102,241,0.3); }
.result-label { font-size: 0.7rem; color: #64748b; font-weight: 600; text-transform: uppercase; }
.result-value { font-size: 1.3rem; font-weight: 800; color: #e2e8f0; margin-top: 0.3rem; }
.result-value.warn { color: #f87171; }
.result-sub { font-size: 0.7rem; color: #f87171; margin-top: 0.2rem; }
.result-arrow .material-icons-round { color: #475569; }

/* Skeleton */
.loading-state { display: flex; flex-direction: column; gap: 1rem; }
.skeleton {
  border-radius: 14px;
  background: linear-gradient(90deg, #1e293b 25%, #273548 50%, #1e293b 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
.skeleton.tall  { height: 280px; }
.skeleton.short { height: 120px; }
@keyframes shimmer {
  0% { background-position: 200% 0; } 100% { background-position: -200% 0; }
}
</style>

<template>
  <div class="detail-container">
    <!-- Header / Back button -->
    <div class="detail-header">
      <div class="header-left">
        <button class="back-btn" @click="$emit('go-back')">
          <span class="material-icons-round">arrow_back</span> Fleet
        </button>
        <div class="battery-title">
          <span class="material-icons-round title-icon">battery_charging_full</span>
          <h2>{{ batteryId }}</h2>
          <span class="status-pill" :class="data?.status">
            {{ data?.soh < 70 ? 'CRITICAL' : (data?.soh < 80 ? 'WARNING' : 'NORMAL') }}
          </span>
        </div>
      </div>
      <button v-if="data" class="export-btn" @click="handleExport">
        <span class="material-icons-round">download</span>
        Export Report
      </button>
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
            <span class="leg warning">🟡 Warning</span>
            <span class="leg critical">🔴 Critical</span>
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
          <h3>🌡️ Scenario Simulator</h3>
          <div class="header-actions">
            <span class="chart-sub">Diagnostic "What-If" Analysis</span>
            <button class="reset-btn" @click="resetSimulation" title="Reset to Defaults">
              <span class="material-icons-round">restart_alt</span>
            </button>
          </div>
        </div>

        <div class="slider-section">
          <div class="slider-labels">
            <span>🌡️ Ambient Temp</span>
            <span class="current-val">{{ sliderTemp }}°C</span>
          </div>
          <input
            type="range"
            min="-10"
            max="45"
            step="1"
            v-model.number="sliderTemp"
            class="temp-slider"
            @input="onSimParamChange"
          />
        </div>

        <div class="slider-section">
          <div class="slider-labels">
            <span>🔌 Discharge Load</span>
            <span class="current-val">{{ sliderLoad }}A</span>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            step="0.5"
            v-model.number="sliderLoad"
            class="load-slider"
            @input="onSimParamChange"
          />
        </div>

        <div class="slider-section">
          <div class="slider-labels">
            <span>⚡ Usage Intensity</span>
            <span class="current-val">{{ sliderIntensity }}x</span>
          </div>
          <input
            type="range"
            min="0.5"
            max="2.5"
            step="0.1"
            v-model.number="sliderIntensity"
            class="intensity-slider"
            @input="onSimParamChange"
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
              <div class="result-value" :class="{'warn': simResult.impact_pct < 0, 'success': simResult.impact_pct > 0}">
                {{ simResult.adjusted_rul }} cycles
              </div>
              <div class="result-sub" v-if="Math.abs(simResult.impact_pct) > 0.1">
                <template v-if="simResult.impact_pct > 0">
                  <span class="success-text">↑ {{ Math.abs(simResult.impact_pct) }}% increase</span>
                </template>
                <template v-else>
                  <span class="warn-text">↓ {{ Math.abs(simResult.impact_pct) }}% reduction</span>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Recommendations -->
      <div v-if="data.recommendations" class="card reco-card">
        <div class="card-header">
          <div class="header-main">
            <h3>Smart Maintenance Directives</h3>
            <p class="chart-sub">AI-prioritized actions for unit {{ batteryId }}</p>
          </div>
          <div class="strategy-badge">
             <span class="material-icons-round">psychology</span>
             Expert Intelligence
          </div>
        </div>
        <div class="reco-list">
          <div 
            v-for="(reco, index) in data.recommendations" 
            :key="index"
            class="reco-item" 
            :class="`priority-${reco.severity}`"
          >
            <div class="reco-icon">
              <span class="material-icons-round">
                {{ getIcon(reco.severity) }}
              </span>
            </div>
            <div class="reco-content">
              <h4>{{ reco.title }}</h4>
              <p>{{ reco.description }}</p>
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
import annotationPlugin from 'chartjs-plugin-annotation';

Chart.register(annotationPlugin);

const getIcon = (severity) => {
  if (severity === 'high') return 'error';
  if (severity === 'medium') return 'warning';
  return 'check_circle';
};

const props = defineProps({ batteryId: String });
const emit  = defineEmits(['go-back']);

const data      = ref(null);
const loading   = ref(true);
const sliderTemp = ref(24);
const sliderLoad = ref(2.0);
const sliderIntensity = ref(1.0);

const simResult  = ref(null);
const simulatedRul    = ref(null);
const simulatedMonths = ref(null);

let chartInstance = null;

// Fetch battery health on mount
onMounted(async () => {
  try {
    const res = await axios.get(`/api/battery/${props.batteryId}/health`);
    data.value = res.data;
    sliderTemp.value = res.data.temperature;
    simulatedRul.value = res.data.rul;
    simulatedMonths.value = res.data.rul_months;

    loading.value = false;
    await nextTick();
    renderChart();
    await fetchSimulation(sliderTemp.value);
  } catch (e) {
    console.error('Battery detail fetch error:', e);
    loading.value = false;
  }
});

// Watch for battery change if component is kept alive
watch(() => props.batteryId, async () => {
  loading.value = true;
  try {
    const res = await axios.get(`/api/battery/${props.batteryId}/health`);
    data.value = res.data;
    sliderTemp.value = res.data.temperature;
    simulatedRul.value = res.data.rul;
    simulatedMonths.value = res.data.rul_months;
    
    loading.value = false;
    await nextTick();
    renderChart();
    await fetchSimulation(sliderTemp.value);
  } catch (e) {
    console.error('Battery detail update error:', e);
    loading.value = false;
  }
});

// Debounce slider
let debounceTimer = null;
const onSimParamChange = () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => fetchSimulation(), 100);
};

const resetSimulation = () => {
  if (!data.value) return;
  sliderTemp.value = data.value.temperature;
  sliderLoad.value = 2.0;
  sliderIntensity.value = 1.0;
  fetchSimulation();
};

const fetchSimulation = async () => {
  try {
    const res = await axios.get(
      `/api/battery/${props.batteryId}/simulate?temp=${sliderTemp.value}&load=${sliderLoad.value}&intensity=${sliderIntensity.value}`
    );
    simResult.value = res.data;
    simulatedRul.value = res.data.adjusted_rul;
    simulatedMonths.value = res.data.adjusted_rul_months;

    // Real-time chart update
    if (chartInstance && res.data.predicted_curve) {
      const predDataset = chartInstance.data.datasets[1];
      const startIdx = predDataset.data.findIndex(v => v !== null);
      if (startIdx !== -1) {
        // Map simulation curve to chart labels
        const labelsToFill = chartInstance.data.labels.length - startIdx;
        const curve = res.data.predicted_curve;
        
        const newData = [...predDataset.data];
        // Ensure the projection aligns with the X-axis labels
        for (let i = 0; i < labelsToFill; i++) {
          const curveIdx = Math.min(i, curve.length - 1);
          newData[startIdx + i] = curve[curveIdx];
        }
        predDataset.data = newData;
        chartInstance.update('none'); 
      }
    }
  } catch (e) {
    console.error('Simulation error:', e);
  }
};

const handleExport = () => {
  window.open(`/api/export/report?battery_id=${props.batteryId}`, '_blank');
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
        },
        // EOL Threshold Line
        annotation: {
          annotations: {
            eolLine: {
              type: 'line',
              yMin: 70,
              yMax: 70,
              borderColor: 'rgba(239, 68, 68, 0.4)',
              borderWidth: 2,
              borderDash: [5, 5],
              label: {
                display: true,
                content: 'Critical (70%)',
                position: 'end',
                backgroundColor: 'rgba(239, 68, 68, 0.8)',
                color: '#fff',
                font: { size: 10, weight: 'bold' }
              }
            },
            warningLine: {
              type: 'line',
              yMin: 80,
              yMax: 80,
              borderColor: 'rgba(245, 158, 11, 0.3)',
              borderWidth: 1,
              borderDash: [5, 5],
              label: {
                display: true,
                content: 'Warning (80%)',
                position: 'start',
                backgroundColor: 'rgba(245, 158, 11, 0.6)',
                color: '#fff',
                font: { size: 9 }
              }
            },
            experimentalLine: {
              type: 'line',
              yMin: data.value?.dataset_threshold || 70,
              yMax: data.value?.dataset_threshold || 70,
              borderColor: 'rgba(139, 92, 246, 0.5)',
              borderWidth: 2,
              label: {
                display: true,
                content: 'Experimental Cutoff',
                position: 'center',
                backgroundColor: 'rgba(139, 92, 246, 0.8)',
                color: '#fff',
                font: { size: 9, weight: 'bold' }
              }
            }
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#64748b', maxTicksLimit: 8 } },
        y: {
          grid: { color: '#334155', borderDash: [2, 4] },
          ticks: { color: '#64748b', callback: v => v + '%' },
          min: 0,
          max: 100,
          stepSize: 20
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
  display: flex; align-items: center; justify-content: space-between; gap: 1.2rem;
  margin-bottom: 1.4rem;
}
.header-left {
  display: flex; align-items: center; gap: 1.2rem;
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

.export-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--accent-primary);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.export-btn:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}
.export-btn:active {
  transform: translateY(0);
}
.export-btn .material-icons-round {
  font-size: 1.1rem;
}

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
.status-pill.critical { background: rgba(239,68,68,0.2); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
.status-pill.warning  { background: rgba(245,158,11,0.2); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
.status-pill.good     { background: rgba(16,185,129,0.2); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }

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
.regime-segment.warning { background: #f59e0b; }
.regime-segment.critical   { background: #ef4444; }

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
.temp-slider, .load-slider, .intensity-slider {
  width: 100%; -webkit-appearance: none; appearance: none;
  height: 6px; border-radius: 4px;
  outline: none; cursor: pointer;
}
.temp-slider {
  background: linear-gradient(90deg, #3b82f6, #818cf8, #f59e0b, #ef4444);
}
.load-slider {
  background: linear-gradient(90deg, #10b981, #f59e0b, #ef4444);
}
.intensity-slider {
  background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
}
.temp-slider::-webkit-slider-thumb, 
.load-slider::-webkit-slider-thumb, 
.intensity-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px; height: 16px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4);
  cursor: pointer;
  transition: transform 0.15s;
}
.temp-slider::-webkit-slider-thumb:hover,
.load-slider::-webkit-slider-thumb:hover,
.intensity-slider::-webkit-slider-thumb:hover { transform: scale(1.2); }

.current-val { font-weight: 800; font-size: 0.9rem; color: #e2e8f0; }

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
.result-value.success { color: #10b981; }
.result-sub .success-text { color: #10b981; font-weight: 600; }
.result-sub .warn-text    { color: #f87171; font-weight: 600; }

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.reset-btn {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  color: #94a3b8;
  border-radius: 6px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.reset-btn:hover {
  background: rgba(99,102,241,0.2);
  color: #818cf8;
  border-color: rgba(99,102,241,0.4);
}
.reset-btn .material-icons-round { font-size: 1.1rem; }

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

/* Recommendations */
.reco-card { border: 1px solid rgba(99,102,241,0.2); }
.strategy-badge {
    display: flex; align-items: center; gap: 0.4rem;
    font-size: 0.7rem; text-transform: uppercase; font-weight: 800;
    color: #10b981; background: rgba(16, 185, 129, 0.1);
    padding: 0.3rem 0.6rem; border-radius: 20px;
}
.reco-list { display: flex; flex-direction: column; gap: 0.8rem; margin-top: 0.5rem; }
.reco-item {
  display: flex; align-items: flex-start; gap: 1rem;
  background: rgba(255,255,255,0.03); border-radius: 12px;
  padding: 1rem; border: 1px solid transparent; transition: all 0.2s;
}
.reco-item:hover { background: rgba(255,255,255,0.06); transform: translateX(4px); }
.reco-item.priority-high { border-left: 4px solid #ef4444; background: rgba(239, 68, 68, 0.05); }
.reco-item.priority-medium { border-left: 4px solid #f59e0b; background: rgba(245, 158, 11, 0.05); }
.reco-item.priority-low { border-left: 4px solid #10b981; background: rgba(16, 185, 129, 0.05); }

.reco-icon { flex-shrink: 0; margin-top: 0.1rem; }
.priority-high .reco-icon { color: #f87171; }
.priority-medium .reco-icon { color: #fbbf24; }
.priority-low .reco-icon { color: #34d399; }

.reco-content { flex: 1; }
.reco-content h4 { font-size: 0.95rem; font-weight: 700; color: #f1f5f9; margin: 0 0 0.2rem 0; }
.reco-content p { font-size: 0.82rem; color: #94a3b8; line-height: 1.5; margin: 0; }

@keyframes shimmer {
  0% { background-position: 200% 0; } 100% { background-position: -200% 0; }
}
</style>

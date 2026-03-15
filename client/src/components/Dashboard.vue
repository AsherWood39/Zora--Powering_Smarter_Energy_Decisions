<template>
  <div class="dashboard-grid" v-if="stats">
    <!-- KPI Cards -->
    <div class="card kpi-card">
      <div class="icon-box warning">
        <span class="material-icons-round">battery_alert</span>
      </div>
      <div class="kpi-info">
        <h3>Health Score</h3>
        <div class="value">{{ stats.health_score }}%</div>
        <span class="status warning">Needs Attention</span>
      </div>
      <div class="progress-ring" :style="`--value:${stats.health_score}`"></div>
    </div>

    <div class="card kpi-card">
      <div class="icon-box primary">
        <span class="material-icons-round">hourglass_bottom</span>
      </div>
      <div class="kpi-info">
        <h3>RUL Estimate</h3>
        <div class="value">{{ stats.remaining_useful_life }}</div>
        <span class="status good">On Track</span>
      </div>
    </div>

    <div class="card kpi-card">
      <div class="icon-box success">
        <span class="material-icons-round">electric_bolt</span>
      </div>
      <div class="kpi-info">
        <h3>Efficiency</h3>
        <div class="value">{{ stats.efficiency }}%</div>
        <span class="status good">+2% this week</span>
      </div>
    </div>

    <!-- Main Chart & Analysis -->
    <div class="card chart-card">
      <div class="card-header">
        <div class="header-main">
          <h2>Degradation Forecast</h2>
          <p class="analysis-description">
            <span class="material-icons-round">analytics</span>
            Performing deep-cycle analysis on <strong>Battery Unit {{ stats.battery_id }}</strong>
          </p>
        </div>
        <div class="legend">
          <span class="dot actual"></span> Actual
          <span class="dot predicted"></span> Predicted
        </div>
      </div>
      <div class="chart-container" style="position: relative; height: 300px; width: 100%;">
        <canvas id="degradationChart"></canvas>
      </div>
    </div>

    <!-- Recommendations (Now Stacked Below) -->
    <div class="card reco-card">
      <div class="card-header">
        <div class="header-main">
          <h2>Smart Maintenance Directives</h2>
          <p class="analysis-description">AI-generated prioritized actions for unit {{ stats.battery_id }}</p>
        </div>
        <div class="strategy-badge">
           <span class="material-icons-round">psychology</span>
           Expert Intelligence
        </div>
      </div>
      <div class="reco-list">
        <div 
          v-for="(reco, index) in recommendations" 
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
  </div>
  <div v-else>Loading...</div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import Chart from 'chart.js/auto';
import annotationPlugin from 'chartjs-plugin-annotation';

Chart.register(annotationPlugin);

const stats = ref(null);
const recommendations = ref([]);

const getIcon = (severity) => {
  if (severity === 'high') return 'error';
  if (severity === 'medium') return 'warning';
  return 'check_circle';
};

const renderChart = async () => {
  try {
    const response = await axios.get('/api/data');
    const data = response.data;
    
    const ctx = document.getElementById('degradationChart').getContext('2d');
    
    // Gradient for predicted area
    let gradientPredict = ctx.createLinearGradient(0, 0, 0, 400);
    gradientPredict.addColorStop(0, 'rgba(245, 158, 11, 0.2)');
    gradientPredict.addColorStop(1, 'rgba(245, 158, 11, 0.0)');

    new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.labels,
        datasets: [
          {
            label: 'Historical Capacity',
            data: data.datasets[0].data,
            borderColor: '#10b981',
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.4
          },
          {
            label: 'Predicted Degradation',
            data: data.datasets[1].data,
            borderColor: '#f59e0b',
            backgroundColor: gradientPredict,
            borderWidth: 2,
            borderDash: [5, 5],
            fill: true,
            pointRadius: 0,
            tension: 0.4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: '#1e293b',
            titleColor: '#f8fafc',
            bodyColor: '#cbd5e1',
            borderColor: '#334155',
            borderWidth: 1
          },
          annotation: {
            annotations: {
              eolLine: {
                type: 'line',
                yMin: 70, yMax: 70,
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
                yMin: 80, yMax: 80,
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
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#64748b', maxTicksLimit: 8 }
          },
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

  } catch (err) {
    console.error("Error loading chart:", err);
  }
};

const fetchRecommendations = async () => {
    try {
        const response = await axios.get('/api/dashboard');
        recommendations.value = response.data.recommendations;
        stats.value = response.data.stats;
    } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
    }
};

onMounted(async () => {
  try {
    // 1. Get dashboard data
    await fetchRecommendations();
    
    // 2. Wait for DOM update then render chart
    setTimeout(renderChart, 100); 
  } catch (err) {
    console.error("Initialization error:", err);
  }
});
</script>

<style scoped>
.reco-content p {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.chart-card, .reco-card {
  grid-column: span 3;
}

.header-main {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.analysis-description {
  font-size: 0.85rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.analysis-description strong {
  color: #818cf8;
}

.analysis-description .material-icons-round {
  font-size: 1.1rem;
  color: #818cf8;
}

.strategy-badge {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.7rem;
    text-transform: uppercase;
    font-weight: 800;
    color: #10b981;
    background: rgba(16, 185, 129, 0.1);
    padding: 0.3rem 0.6rem;
    border-radius: 20px;
}
</style>

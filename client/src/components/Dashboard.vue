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

    <!-- Main Chart -->
    <div class="card chart-card">
      <div class="card-header">
        <h2>Degradation Forecast</h2>
        <div class="legend">
          <span class="dot actual"></span> Actual
          <span class="dot predicted"></span> Predicted
        </div>
      </div>
      <div class="chart-container" style="position: relative; height: 300px; width: 100%;">
        <canvas id="degradationChart"></canvas>
      </div>
    </div>

    <!-- Recommendations -->
    <div class="card reco-card">
      <div class="card-header">
        <h2>Smart Recommendations</h2>
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
          <button class="action-btn">Action</button>
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

const stats = ref(null);
const recommendations = ref([]);

const getIcon = (severity) => {
  if (severity === 'high') return 'error';
  if (severity === 'medium') return 'warning';
  return 'check_circle';
};

const renderChart = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/api/data');
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
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#64748b', maxTicksLimit: 8 }
          },
          y: {
            grid: { color: '#334155', borderDash: [2, 4] },
            ticks: { color: '#64748b' }
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

onMounted(async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/api/dashboard');
    stats.value = response.data.stats;
    recommendations.value = response.data.recommendations;
    
    // Wait for DOM update then render chart
    setTimeout(renderChart, 100); 
  } catch (err) {
    console.error("Failed to fetch dashboard data:", err);
  }
});
</script>

<template>
  <div class="analytics-container">
    <div class="analytics-header">
      <h2>📊 Fleet-Wide Analytics</h2>
      <p class="subtitle">Real-time health distribution and predictive risk assessment across all active battery units.</p>
    </div>

    <!-- Top Stats Row -->
    <div class="stats-grid">
      <div class="stat-card">
        <span class="label">Avg. Fleet Health (SoH)</span>
        <div class="value-container">
          <span class="value">{{ avgSoH }}%</span>
          <span class="trend up" v-if="avgSoH > 85">Excellent</span>
          <span class="trend warning" v-else>Monitoring Required</span>
        </div>
      </div>
      <div class="stat-card">
        <span class="label">Total Active Units</span>
        <div class="value-container">
          <span class="value">{{ analytics.active_batteries || fleet.length }}</span>
          <span class="unit">Batteries</span>
        </div>
      </div>
      <div class="stat-card">
        <span class="label">Total Fleet Cycles</span>
        <div class="value-container">
          <span class="value">{{ analytics.total_fleet_cycles?.toLocaleString() || '---' }}</span>
          <span class="tag">Exp. Hours</span>
        </div>
      </div>
    </div>

    <div class="charts-layout">
      <!-- Left: Health Distribution -->
      <div class="chart-section card">
        <h3>Health Distribution</h3>
        <div class="distribution-summary">
          <div class="dist-item">
            <span class="dot good"></span>
            <span class="label">Good (>85%)</span>
            <span class="count">{{ counts.good }}</span>
          </div>
          <div class="dist-item">
            <span class="dot warning"></span>
            <span class="label">Warning (75-85%)</span>
            <span class="count">{{ counts.warning }}</span>
          </div>
          <div class="dist-item">
            <span class="dot critical"></span>
            <span class="label">Critical (<75%)</span>
            <span class="count">{{ counts.critical }}</span>
          </div>
        </div>
        <div class="distribution-bar">
          <div class="bar good" :style="{ width: (counts.good / fleet.length * 100) + '%' }"></div>
          <div class="bar warning" :style="{ width: (counts.warning / fleet.length * 100) + '%' }"></div>
          <div class="bar critical" :style="{ width: (counts.critical / fleet.length * 100) + '%' }"></div>
        </div>
        
        <div class="env-distribution">
           <h4>Environment Exposure</h4>
           <div class="env-list">
              <div v-for="(count, type) in analytics.temperature_distribution" :key="type" class="env-item">
                 <span class="env-label">{{ type }}</span>
                 <span class="env-count">{{ count }} Units</span>
              </div>
           </div>
        </div>
      </div>

      <!-- Right: Risk Assessment -->
      <div class="risk-section card">
        <h3>Top Predictive Risks</h3>
        <p class="section-desc">Batteries predicted to reach EOL (End-of-Life) the soonest.</p>
        <div class="risk-list">
          <div v-for="b in risks" :key="b.battery_id" class="risk-item">
            <div class="risk-info">
              <span class="risk-id">{{ b.battery_id }}</span>
              <span class="risk-regime">{{ b.regime }}</span>
            </div>
            <div class="risk-val">
              <span class="val">{{ b.rul }}</span>
              <span class="lbl">Cycles Left</span>
            </div>
          </div>
        </div>
        <div class="fleet-aging">
           <p>Avg. Internal Resistance (Re): <strong>{{ analytics.avg_resistance_ohm }} Ω</strong></p>
        </div>
      </div>
    </div>
    
    <footer class="methodology-footer card">
       <h3><span class="material-icons-round">verified</span> Model Performance (LOBO Validation)</h3>
       <div class="perf-stats">
          <div class="perf-item">
            <strong>SoH Error (MAE)</strong>
            <span>{{ analytics.model_performance?.soh_mae }}% Accuracy Gap</span>
          </div>
          <div class="perf-item">
             <strong>RUL Error (MAE)</strong>
             <span>{{ analytics.model_performance?.rul_mae }} Cycles Deviation</span>
          </div>
          <div class="perf-item">
            <strong>Inference Speed</strong>
            <span>~{{ analytics.model_performance?.inference_ms }}ms per cycle</span>
          </div>
       </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

const fleet = ref([]);
const analytics = ref({});
const loading = ref(true);

const fetchAnalytics = async () => {
  try {
    const [fleetRes, analyticsRes] = await Promise.all([
      axios.get('/api/fleet/triage'),
      axios.get('/api/analytics/summary')
    ]);
    
    console.log('[DEBUG] Fleet API Response:', fleetRes.data);
    console.log('[DEBUG] Analytics API Response:', analyticsRes.data);
    
    // Safety check: ensure fleetRes.data is an array
    if (Array.isArray(fleetRes.data)) {
        fleet.value = fleetRes.data;
    } else {
        console.warn('[DEBUG] Fleet API returned non-array:', fleetRes.data);
        fleet.value = [];
    }
    
    analytics.value = analyticsRes.data || {};
  } catch (err) {
    console.error('Failed to fetch analytics:', err);
  } finally {
    loading.value = false;
  }
};

const counts = computed(() => {
  const c = { good: 0, warning: 0, critical: 0 };
  if (!Array.isArray(fleet.value)) return c;
  
  fleet.value.forEach(b => {
    if (b.status === 'good') c.good++;
    else if (b.status === 'warning') c.warning++;
    else if (b.status === 'critical') c.critical++;
  });
  return c;
});

const avgSoH = computed(() => {
  if (!Array.isArray(fleet.value) || fleet.value.length === 0) return 0;
  try {
    const total = fleet.value.reduce((acc, b) => acc + (b.soh || 0), 0);
    return Math.round(total / fleet.value.length);
  } catch (e) {
    console.error("Scale error in avgSoH:", e);
    return 0;
  }
});

const risks = computed(() => {
  if (!Array.isArray(fleet.value)) return [];
  // Return top 3 batteries with lowest RUL
  return [...fleet.value]
    .filter(b => b.rul !== undefined)
    .sort((a, b) => a.rul - b.rul)
    .slice(0, 3);
});

onMounted(fetchAnalytics);
</script>

<style scoped>
.analytics-container {
  max-width: 1100px;
  margin: 0 auto;
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.analytics-header { margin-bottom: 2rem; }
.analytics-header h2 { font-size: 1.8rem; color: #f1f5f9; margin-bottom: 0.5rem; }
.subtitle { color: #64748b; font-size: 0.95rem; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 1.5rem;
}

.stat-card .label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  margin-bottom: 1rem;
}

.value-container {
  display: flex;
  align-items: baseline;
  gap: 1rem;
}

.stat-card .value { font-size: 2.2rem; font-weight: 800; color: #f1f5f9; }
.unit { color: #64748b; font-weight: 600; }
.tag { background: rgba(99, 102, 241, 0.15); color: #818cf8; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }

.trend { font-size: 0.8rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 6px; }
.trend.up { background: rgba(52, 211, 153, 0.1); color: #34d399; }
.trend.warning { background: rgba(251, 191, 36, 0.1); color: #fbbf24; }

.charts-layout {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 1.5rem;
}

.card h3 { font-size: 1.1rem; color: #e2e8f0; margin-bottom: 1.5rem; }

.distribution-summary {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.dist-item { display: flex; align-items: center; gap: 0.5rem; }
.dot { width: 10px; height: 10px; border-radius: 50%; }
.dot.good { background: #34d399; }
.dot.warning { background: #fbbf24; }
.dot.critical { background: #ef4444; }
.dist-item .label { color: #94a3b8; font-size: 0.85rem; }
.dist-item .count { color: #f1f5f9; font-weight: 700; }

.distribution-bar {
  display: flex;
  height: 24px;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255,255,255,0.05);
}
.bar.good { background: #34d399; }
.bar.warning { background: #fbbf24; }
.bar.critical { background: #ef4444; }

.env-distribution { margin-top: 2rem; }
.env-distribution h4 { font-size: 0.9rem; color: #94a3b8; margin-bottom: 1rem; }
.env-list { display: flex; flex-direction: column; gap: 0.8rem; }
.env-item { display: flex; justify-content: space-between; font-size: 0.85rem; color: #cbd5e1; }
.env-count { font-weight: 700; color: #818cf8; }

.section-desc { color: #64748b; font-size: 0.85rem; margin-bottom: 1.5rem; }

.risk-list { display: flex; flex-direction: column; gap: 1rem; }
.risk-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255,255,255,0.02);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.05);
}

.risk-info { display: flex; flex-direction: column; }
.risk-id { color: #f1f5f9; font-weight: 700; font-size: 1rem; }
.risk-regime { color: #818cf8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }

.risk-val { text-align: right; }
.risk-val .val { display: block; color: #ef4444; font-size: 1.2rem; font-weight: 800; }
.risk-val .lbl { color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }

.fleet-aging { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.05); }
.fleet-aging p { color: #64748b; font-size: 0.85rem; }
.fleet-aging strong { color: #34d399; }

.performance-footer h3 {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #818cf8;
}

.perf-stats {
  display: flex;
  justify-content: space-between;
  gap: 2rem;
}

.perf-item { display: flex; flex-direction: column; gap: 0.2rem; }
.perf-item strong { color: #e2e8f0; font-size: 0.85rem; }
.perf-item span { color: #64748b; font-size: 0.75rem; }
</style>

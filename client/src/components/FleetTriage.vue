<template>
  <div class="fleet-container">
    <div class="fleet-header">
      <h2>⚡ Fleet Triage</h2>
      <div class="fleet-summary">
        <span class="badge healthy">🟢 {{ healthyCount }} Healthy</span>
        <span class="badge warning">🟡 {{ warningCount }} Warning</span>
        <span class="badge critical">🔴 {{ criticalCount }} Critical</span>
        <span class="badge eol">💀 {{ eolCount }} EOL</span>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="skeleton" v-for="n in 6" :key="n"></div>
    </div>

    <div v-else class="battery-groups">
      <div v-for="(groupBatteries, groupName) in groupedFleet" :key="groupName" class="fleet-group">
        <div class="group-header">
          <span class="material-icons-round">science</span>
          <h3>{{ groupName }}</h3>
          <span class="group-count">{{ groupBatteries.length }} units</span>
        </div>
        
        <div class="battery-list">
          <div
            v-for="battery in groupBatteries"
            :key="battery.battery_id"
            class="battery-row"
            :class="`status-${battery.status}`"
            @click="$emit('select-battery', battery.battery_id)"
          >
            <!-- Status indicator -->
            <div class="status-dot" :class="battery.status"></div>

            <!-- Battery ID -->
            <div class="battery-id">
              <span class="id-label">{{ battery.battery_id }}</span>
              <span class="regime-tag" :class="`regime-${battery.regime.toLowerCase()}`">
                {{ battery.regime }}
              </span>
            </div>

            <!-- SoH bar -->
            <div class="soh-section">
              <div class="soh-label">SoH</div>
              <div class="soh-bar-wrap">
                <div
                  class="soh-bar"
                  :class="battery.status"
                  :style="`width: ${battery.soh}%`"
                ></div>
              </div>
              <div class="soh-value">{{ battery.soh.toFixed(1) }}%</div>
            </div>

            <!-- RUL -->
            <div class="rul-section">
              <div class="rul-value">{{ battery.rul }} cycles</div>
              <div class="rul-months">~{{ battery.rul_months }} months</div>
            </div>

            <!-- Temp -->
            <div class="temp-section">
              <span class="material-icons-round temp-icon">thermostat</span>
              {{ battery.temperature }}°C
            </div>

            <!-- Arrow -->
            <div class="arrow">
              <span class="material-icons-round">chevron_right</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const emit = defineEmits(['select-battery']);

const fleet = ref([]);
const loading = ref(true);

const eolCount      = computed(() => fleet.value.filter(b => (b.status || '').toLowerCase() === 'eol').length);
const criticalCount = computed(() => fleet.value.filter(b => (b.status || '').toLowerCase() === 'critical').length);
const warningCount  = computed(() => fleet.value.filter(b => {
    const s = (b.status || '').toLowerCase();
    return s === 'warning' || s === 'risk';
}).length);
const healthyCount  = computed(() => fleet.value.filter(b => {
    const s = (b.status || '').toLowerCase();
    return s === 'healthy' || s === 'good';
}).length);

const groupedFleet = computed(() => {
  const groups = {};
  fleet.value.forEach(battery => {
    const name = battery.group_name || 'General';
    if (!groups[name]) groups[name] = [];
    groups[name].push(battery);
  });
  return groups;
});

onMounted(async () => {
  try {
    const res = await axios.get('/api/fleet/triage');
    fleet.value = res.data;
  } catch (e) {
    console.error('Fleet triage fetch error:', e);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.fleet-container {
  padding: 0;
  max-width: calc(100% - 80px); /* Leave room for FAB */
}

.fleet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.2rem;
}

.fleet-header h2 {
  font-size: 1.2rem;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
}

.fleet-summary {
  display: flex;
  gap: 0.6rem;
}

.badge {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.25rem 0.65rem;
  border-radius: 20px;
  letter-spacing: 0.02em;
}
.badge.eol { background: rgba(71, 85, 105, 0.15); color: #94a3b8; border: 1px solid rgba(71, 85, 105, 0.3); }
.badge.critical { background: rgba(239,68,68,0.15); color: #f87171; }
.badge.warning, .badge.risk { background: rgba(245,158,11,0.15); color: #fbbf24; }
.badge.healthy, .badge.good { background: rgba(16,185,129,0.15);  color: #34d399; }

/* Skeleton loading */
.loading-state { display: flex; flex-direction: column; gap: 0.7rem; }
.skeleton {
  height: 60px;
  border-radius: 12px;
  background: linear-gradient(90deg, #1e293b 25%, #273548 50%, #1e293b 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Grouping styles */
.fleet-group {
  margin-bottom: 2rem;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.group-header h3 {
  font-size: 0.85rem;
  font-weight: 700;
  color: #94a3b8;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.group-header .material-icons-round {
  font-size: 1.1rem;
  color: #6366f1;
}

.group-count {
  font-size: 0.7rem;
  color: #475569;
  margin-left: auto;
  font-weight: 600;
}

/* Battery rows */
.battery-list { display: flex; flex-direction: column; gap: 0.55rem; }

.battery-row {
  display: grid;
  grid-template-columns: 12px 140px 1fr 110px 80px 24px;
  align-items: center;
  gap: 1rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}
.battery-row:hover {
  background: rgba(255,255,255,0.08);
  border-color: rgba(99,102,241,0.4);
  transform: translateX(3px);
}
.battery-row.status-eol      { border-left: 3px solid #64748b; filter: grayscale(0.5); }
.battery-row.status-critical { border-left: 3px solid #ef4444; }
.battery-row.status-warning,
.battery-row.status-risk     { border-left: 3px solid #f59e0b; }
.battery-row.status-healthy,
.battery-row.status-good     { border-left: 3px solid #10b981; }

.status-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-dot.eol      { background: #64748b; box-shadow: none; }
.status-dot.critical { background: #ef4444; box-shadow: 0 0 6px #ef4444; }
.status-dot.warning,
.status-dot.risk     { background: #f59e0b; box-shadow: 0 0 6px #f59e0b; }
.status-dot.healthy,
.status-dot.good     { background: #10b981; box-shadow: 0 0 6px #10b981; }

.battery-id { display: flex; flex-direction: column; gap: 0.2rem; }
.id-label   { font-size: 0.95rem; font-weight: 700; color: #e2e8f0; font-family: monospace; }
.regime-tag {
  font-size: 0.65rem; font-weight: 600;
  padding: 0.1rem 0.45rem;
  border-radius: 6px;
  width: fit-content;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.regime-normal      { background: rgba(16,185,129,0.15); color: #34d399; }
.regime-warning { background: rgba(245,158,11,0.15); color: #f59e0b; }
.regime-critical,
.regime-anomalous   { background: rgba(239,68,68,0.15);  color: #f87171; }

.soh-section { display: flex; align-items: center; gap: 0.6rem; }
.soh-label   { font-size: 0.7rem; color: #64748b; width: 24px; flex-shrink: 0; }
.soh-bar-wrap {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.08);
  border-radius: 4px;
  overflow: hidden;
}
.soh-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}
.soh-bar.eol      { background: #475569; }
.soh-bar.critical { background: linear-gradient(90deg, #ef4444, #f87171); }
.soh-bar.warning,
.soh-bar.risk     { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.soh-bar.healthy,
.soh-bar.good     { background: linear-gradient(90deg, #10b981, #34d399); }
.soh-value { font-size: 0.82rem; font-weight: 700; color: #cbd5e1; width: 42px; text-align: right; }

.rul-section  { text-align: center; }
.rul-value    { font-size: 0.88rem; font-weight: 700; color: #e2e8f0; }
.rul-months   { font-size: 0.7rem; color: #64748b; }

.temp-section {
  display: flex; align-items: center; gap: 0.3rem;
  font-size: 0.82rem; color: #94a3b8;
}
.temp-icon { font-size: 0.9rem !important; }

.arrow { color: #475569; }
</style>

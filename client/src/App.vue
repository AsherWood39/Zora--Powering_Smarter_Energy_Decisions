<template>
  <div class="app-container">
    <aside class="sidebar">
      <div class="brand">
        <span class="material-icons-round logo-icon">bolt</span>
        <h1>Zora</h1>
      </div>
      <nav>
        <a href="#" :class="{ active: currentView === 'dashboard' }" @click.prevent="currentView = 'dashboard'; selectedBattery = null">
          <span class="material-icons-round">dashboard</span>
          Dashboard
        </a>
        <a href="#" :class="{ active: currentView === 'fleet' || currentView === 'detail' }" @click.prevent="currentView = 'fleet'; selectedBattery = null">
          <span class="material-icons-round">directions_car</span>
          Fleet
        </a>
        <a href="#" :class="{ active: currentView === 'analytics' }" @click.prevent="currentView = 'analytics'; selectedBattery = null">
          <span class="material-icons-round">analytics</span>
          Analytics
        </a>
        <a href="#" :class="{ active: currentView === 'model-info' }" @click.prevent="currentView = 'model-info'; selectedBattery = null">
          <span class="material-icons-round">psychology</span>
          About Model
        </a>
      </nav>
      <div class="user-profile">
        <div class="avatar">ME</div>
        <div class="info">
          <p>Engineer</p>
          <span>Fleet Manager</span>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <header class="top-bar">
        <div class="breadcrumbs">
          <span>Dashboards</span>
          <template v-if="currentView === 'dashboard'"> / <span class="current">Battery Health Overview</span></template>
          <template v-else-if="currentView === 'fleet'"> / <span class="current">Fleet Triage</span></template>
          <template v-else-if="currentView === 'analytics'"> / <span class="current">Fleet Analytics</span></template>
          <template v-else-if="currentView === 'model-info'"> / <span class="current">About the Model</span></template>
          <template v-else-if="currentView === 'detail'"> / <span @click="currentView='fleet'; selectedBattery=null" class="breadcrumb-link">Fleet Triage</span> / <span class="current">{{ selectedBattery }}</span></template>
        </div>
        <div class="actions">
          <button class="icon-btn"><span class="material-icons-round">notifications</span></button>
          <button class="primary-btn">Export Report</button>
        </div>
      </header>

      <div class="content-wrapper">
        <Transition name="fade" mode="out-in">
          <!-- Dashboard view -->
          <Dashboard v-if="currentView === 'dashboard'" key="dashboard" />

          <!-- Fleet Triage view -->
          <div v-else-if="currentView === 'fleet'" key="fleet" class="view-card">
            <FleetTriage @select-battery="openBattery" />
          </div>

          <!-- Analytics view -->
          <div v-else-if="currentView === 'analytics'" key="analytics" class="view-card">
            <Analytics />
          </div>

          <!-- Model Info view -->
          <div v-else-if="currentView === 'model-info'" key="model-info" class="view-card">
            <ModelInfo />
          </div>

          <!-- Battery Detail view -->
          <div v-else-if="currentView === 'detail' && selectedBattery" key="detail" class="view-card">
            <BatteryDetail
              :battery-id="selectedBattery"
              @go-back="currentView = 'fleet'"
            />
          </div>
        </Transition>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Dashboard    from './components/Dashboard.vue';
import FleetTriage  from './components/FleetTriage.vue';
import BatteryDetail from './components/BatteryDetail.vue';
import ModelInfo     from './components/ModelInfo.vue';
import Analytics     from './components/Analytics.vue';

const currentView    = ref('dashboard');
const selectedBattery = ref(null);

const openBattery = (batteryId) => {
  selectedBattery.value = batteryId;
  currentView.value = 'detail';
};
</script>

<style scoped>
.breadcrumb-link {
  cursor: pointer;
  color: #64748b;
  transition: color 0.2s;
}
.breadcrumb-link:hover { color: #e2e8f0; }

.view-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 18px;
  padding: 1.5rem;
}

/* Page transition */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

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
          <button class="primary-btn">Export Report</button>
        </div>
      </header>

      <div class="content-wrapper" ref="scrollContainer" @scroll="handleScroll">
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

        <!-- Floating Scroll Toggle Button -->
        <Transition name="fab-fade">
          <button 
            v-if="isScrollable && currentView !== 'model-info'"
            class="fab-scroll-toggle"
            @click="toggleScroll"
            :title="isAtBottom ? 'Scroll to Top' : 'Scroll to Bottom'"
          >
            <span class="material-icons-round">
              {{ isAtBottom ? 'keyboard_double_arrow_up' : 'keyboard_double_arrow_down' }}
            </span>
          </button>
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
const scrollContainer = ref(null);
const isAtBottom      = ref(false);
const isScrollable    = ref(false);

const openBattery = (batteryId) => {
  selectedBattery.value = batteryId;
  currentView.value = 'detail';
};

const checkScrollability = () => {
  if (scrollContainer.value) {
    const { scrollHeight, clientHeight } = scrollContainer.value;
    isScrollable.value = scrollHeight > clientHeight + 50; // Add small buffer
  }
};

const handleScroll = (event) => {
  const { scrollTop, scrollHeight, clientHeight } = event.target;
  isAtBottom.value = scrollTop > (scrollHeight - clientHeight) / 2;
  checkScrollability();
};

const toggleScroll = () => {
  if (scrollContainer.value) {
    const { scrollHeight, clientHeight } = scrollContainer.value;
    const target = isAtBottom.value ? 0 : scrollHeight - clientHeight;
    
    scrollContainer.value.scrollTo({
      top: target,
      behavior: 'smooth'
    });
  }
};

// Re-check scrollability when view changes or components mount
import { watch, onMounted, nextTick } from 'vue';
watch(currentView, () => {
  isAtBottom.value = false;
  isScrollable.value = false;
  nextTick(checkScrollability);
});

onMounted(() => {
  setTimeout(checkScrollability, 500); // Wait for animations/data
});
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

/* Interactive Floating Action Button */
.fab-scroll-toggle {
  position: fixed;
  bottom: 2.5rem;
  right: 2.5rem;
  width: 60px;
  height: 60px;
  border-radius: 18px; /* Matching card radius better */
  background: linear-gradient(135deg, var(--accent-success), #059669);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.fab-scroll-toggle:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(16, 185, 129, 0.6);
  filter: brightness(1.1);
}

.fab-scroll-toggle:active {
  transform: scale(0.95);
}

.fab-scroll-toggle span {
  font-size: 2rem;
  transition: transform 0.4s ease;
}

/* FAB Animation */
.fab-fade-enter-active, .fab-fade-leave-active {
  transition: all 0.3s ease;
}

.fab-fade-enter-from, .fab-fade-leave-to {
  opacity: 0;
  transform: scale(0.5) translateY(20px);
}

</style>

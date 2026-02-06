<template>
  <div class="app-container">
    <aside class="sidebar">
      <div class="brand">
        <span class="material-icons-round logo-icon">bolt</span>
        <h1>Zora</h1>
      </div>
      <nav>
        <a href="#" class="active">
          <span class="material-icons-round">dashboard</span>
          Dashboard
        </a>
        <a href="#">
          <span class="material-icons-round">analytics</span>
          Analytics
        </a>
        <a href="#">
          <span class="material-icons-round">directions_car</span>
          Fleet
        </a>
        <a href="#">
          <span class="material-icons-round">settings</span>
          Settings
        </a>
      </nav>
      <div class="user-profile">
        <div class="avatar">JM</div>
        <div class="info">
          <p>John Musk</p>
          <span>Fleet Manager</span>
        </div>
      </div>
    </aside>
    
    <main class="main-content">
      <header class="top-bar">
        <div class="breadcrumbs">
          <span>Dashboards</span> / <span class="current">Battery Health Overview</span>
        </div>
        <div class="actions">
          <button class="icon-btn"><span class="material-icons-round">notifications</span></button>
          <button class="primary-btn">Export Report</button>
        </div>
      </header>
      
      <div class="content-wrapper">
        <Dashboard />
      </div>
    </main>
  </div>
</template>

<script setup>
import Dashboard from './components/Dashboard.vue'
</script>

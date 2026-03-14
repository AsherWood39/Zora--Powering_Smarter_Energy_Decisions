<template>
  <div class="model-info-container">
    <div class="info-header">
      <h2>🧠 About the Zora ML Model</h2>
      <p class="subtitle">A brief overview of the science powering your fleet intelligence.</p>
    </div>

    <div class="grid-layout">
      <!-- Left Column: Methodology -->
      <div class="column">
        <section class="info-card">
          <div class="card-title">
            <span class="material-icons-round">source</span>
            <h3>Data Source</h3>
          </div>
          <p>
            Zora is powered by the <strong>NASA Prognostics Data Repository</strong>. We utilize 
            experimental discharge data from Li-ion batteries cycled under varying 
            stress conditions (Charge/Discharge rates and Ambient Temperatures).
          </p>
          <div class="tag-list">
            <span class="tag">B0005</span>
            <span class="tag">B0006</span>
            <span class="tag">B0007</span>
            <span class="tag">B0018</span>
            <span class="tag">B0045-48</span>
          </div>
        </section>

        <section class="info-card">
          <div class="card-title">
            <span class="material-icons-round">psychology</span>
            <h3>Core Algorithms</h3>
          </div>
          <p>
            We use <strong>Gradient Boosted Trees (XGBoost)</strong> for both State of Health (SoH) 
            regression and Remaining Useful Life (RUL) estimation.
          </p>
          <ul>
            <li><strong>SoH Model</strong>: Predicts capacity fade based on internal resistance and voltage drop.</li>
            <li><strong>RUL Model</strong>: Forecasts the number of remaining cycles until a safety threshold (80% SoH) is reached.</li>
          </ul>
        </section>
      </div>

      <!-- Right Column: Features & Validation -->
      <div class="column">
        <section class="info-card">
          <div class="card-title">
            <span class="material-icons-round">analytics</span>
            <h3>Feature Engineering</h3>
          </div>
          <p>The model doesn't just look at capacity. it analyzes high-fidelity signals including:</p>
          <div class="feature-grid">
            <div class="feature-item">
              <strong>Ohmic Drop</strong>
              <span>Voltage drop at t=0</span>
            </div>
            <div class="feature-item">
              <strong>Internal Resistance</strong>
              <span>Real-time DC Resistance (Re)</span>
            </div>
            <div class="feature-item">
              <strong>Thermal Delta</strong>
              <span>Ambient vs Operating temp</span>
            </div>
            <div class="feature-item">
              <strong>Fade Rate</strong>
              <span>Rolling capacity deviation</span>
            </div>
          </div>
        </section>

        <section class="info-card highlight">
          <div class="card-title">
            <span class="material-icons-round">verified_user</span>
            <h3>Validation Strategy</h3>
          </div>
          <p>
            To ensure the model works on batteries it has <strong>never seen before</strong>, we use 
            <strong>Leave-One-Battery-Out (LOBO)</strong> cross-validation.
          </p>
          <div class="stats-mini">
            <div class="stat">
              <span class="val">~3%</span>
              <span class="lbl">SoH MAE</span>
            </div>
            <div class="stat">
              <span class="val">~4</span>
              <span class="lbl">RUL MAE (Cycles)</span>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Methodology Footer -->
    <footer class="methodology-footer">
      <div class="method-item">
        <span class="material-icons-round">science</span>
        <div>
          <strong>Hybrid Approach</strong>
          <p>Combining physical degradation physics with modern ML residuals.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.model-info-container {
  max-width: 1000px;
  margin: 0 auto;
  animation: slideUp 0.4s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.info-header {
  margin-bottom: 2rem;
  text-align: left;
}

.info-header h2 {
  font-size: 1.8rem;
  font-weight: 800;
  color: #f1f5f9;
  letter-spacing: -0.02em;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #64748b;
  font-size: 1rem;
}

.grid-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.info-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  transition: transform 0.2s;
}

.info-card:hover {
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(255, 255, 255, 0.05);
}

.info-card.highlight {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.05));
  border-color: rgba(99, 102, 241, 0.2);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1rem;
  color: #818cf8;
}

.card-title h3 {
  font-size: 1rem;
  font-weight: 700;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.card-title .material-icons-round {
  font-size: 1.4rem;
}

.info-card p {
  color: #94a3b8;
  line-height: 1.6;
  font-size: 0.92rem;
  margin-bottom: 1rem;
}

.info-card ul {
  padding-left: 1.2rem;
  color: #94a3b8;
  font-size: 0.9rem;
}

.info-card li { margin-bottom: 0.6rem; }

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag {
  background: rgba(255, 255, 255, 0.06);
  color: #cbd5e1;
  padding: 0.2rem 0.6rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.feature-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.8rem;
}

.feature-item {
  background: rgba(255, 255, 255, 0.03);
  padding: 0.6rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.feature-item strong {
  display: block;
  font-size: 0.8rem;
  color: #e2e8f0;
  margin-bottom: 0.2rem;
}

.feature-item span {
  font-size: 0.7rem;
  color: #64748b;
}

.stats-mini {
  display: flex;
  gap: 2rem;
  margin-top: 1rem;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat .val {
  font-size: 1.5rem;
  font-weight: 800;
  color: #34d399;
}

.stat .lbl {
  font-size: 0.7rem;
  color: #64748b;
  text-transform: uppercase;
  font-weight: 700;
}

.methodology-footer {
  margin-top: 1rem;
  padding: 1.2rem;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.method-item {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.method-item .material-icons-round { color: #818cf8; }

.method-item strong { color: #e2e8f0; font-size: 0.9rem; }
.method-item p { color: #64748b; font-size: 0.8rem; margin: 0.2rem 0 0 0; }
</style>

<template>
  <div id="app">
    <NavBar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import NavBar from "./components/NavBar.vue";
</script>

<style>
:root {
  --primary: #4f46e5;
  --primary-hover: #4338ca;
  --success: #10b981;
  --danger: #ef4444;
  --warning: #f59e0b;
  --bg: #f8fafc;
  --card-bg: #ffffff;
  --text: #1e293b;
  --text-secondary: #64748b;
  --border: #e2e8f0;
  --radius: 12px;
}

body {
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
}

.main-content {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px;
}

.card {
  background: var(--card-bg);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  padding: 24px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--primary);
  color: white;
}
.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-success {
  background: var(--success);
  color: white;
}

.btn-danger {
  background: var(--danger);
  color: white;
}

.input-field {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.input-field:focus {
  border-color: var(--primary);
}

.alert {
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}
.alert-success {
  background: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}
.alert-error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}
.alert-info {
  background: #eff6ff;
  color: #1e40af;
  border: 1px solid #bfdbfe;
}
</style>

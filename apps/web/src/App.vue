<template>
  <main class="app-shell">
    <section class="app-card">
      <h1 data-testid="app-header">Task Manager App</h1>
      <router-view />
    </section>
  </main>
</template>

<style scoped>
main {
  min-height: 100vh;
  margin: 0;
  font-family: Inter, Arial, sans-serif;
}

.app-shell {
  display: grid;
  place-items: center;
  background: linear-gradient(160deg, #eef2ff, #ecfeff);
  padding: 2rem 1rem;
}

.app-card {
  width: min(100%, 560px);
  border-radius: 16px;
  background: #ffffff;
  padding: 1.5rem;
  box-shadow: 0 20px 45px rgba(18, 36, 64, 0.14);
}

h1 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #0f172a;
}
</style>

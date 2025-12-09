<template>
  <router-view></router-view>
</template>

<script setup lang="ts">
// Root component solely for routing views
</script>

<style>
/* Global styles can go here */
:root {
  --primary-color: #2c3e50;
  --secondary-color: #3498db;
  --border-radius: 8px;
  --box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  --transition-time: 0.3s;
}

body {
  margin: 0;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: #f8f9fb;
  color: #2c3e50;
  line-height: 1.6;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  background: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 30px;
}
</style> 
<script setup>
// 应用外壳：全局背景光斑 + 路由视图
</script>

<template>
  <div class="app-shell">
    <!-- 背景装饰：柔和渐变光斑（全局共享） -->
    <div class="bg-blob bg-blob--indigo" aria-hidden="true"></div>
    <div class="bg-blob bg-blob--sky" aria-hidden="true"></div>
    <div class="bg-blob bg-blob--rose" aria-hidden="true"></div>

    <router-view />
  </div>
</template>

<style scoped>
.app-shell {
  position: relative;
  height: 100vh;
  overflow: hidden;
}

/* ---------- 背景装饰光斑 ---------- */
.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.55;
  pointer-events: none;
  animation: blob-float 14s ease-in-out infinite;
}

.bg-blob--indigo {
  top: -12%;
  left: -8%;
  width: 34rem;
  height: 34rem;
  background: radial-gradient(circle at center, #c7d2fe 0%, transparent 70%);
}

.bg-blob--sky {
  top: 20%;
  right: -10%;
  width: 28rem;
  height: 28rem;
  background: radial-gradient(circle at center, #bae6fd 0%, transparent 70%);
  animation-delay: -5s;
}

.bg-blob--rose {
  bottom: -14%;
  left: 16%;
  width: 26rem;
  height: 26rem;
  background: radial-gradient(circle at center, #fbcfe8 0%, transparent 70%);
  animation-delay: -9s;
}

@keyframes blob-float {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(2.5rem, -2rem, 0) scale(1.06);
  }
}
</style>

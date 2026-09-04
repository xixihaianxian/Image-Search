<script setup>
// 应用外壳：奶油纸感背景 + 柔和淡彩 + 路由视图
</script>

<template>
  <div class="app-shell">
    <!-- 背景装饰：柔和淡彩晕染 + 手绘斑点 -->
    <div class="bg-blob bg-blob--pink" aria-hidden="true"></div>
    <div class="bg-blob bg-blob--blue" aria-hidden="true"></div>
    <div class="bg-blob bg-blob--peach" aria-hidden="true"></div>
    <div class="bg-doodle bg-doodle--1" aria-hidden="true">✿</div>
    <div class="bg-doodle bg-doodle--2" aria-hidden="true">〜</div>

    <router-view />
  </div>
</template>

<style scoped>
.app-shell {
  position: relative;
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(160deg, #fdf8f0 0%, #f8f0e6 50%, #f6ede2 100%);
}

/* ---------- 柔和淡彩晕染 ---------- */
.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.5;
  pointer-events: none;
  animation: blob-float 16s ease-in-out infinite;
}

.bg-blob--pink {
  top: -12%;
  left: -8%;
  width: 32rem;
  height: 32rem;
  background: radial-gradient(circle at center, #f9cbd8 0%, transparent 70%);
}

.bg-blob--blue {
  top: 20%;
  right: -10%;
  width: 30rem;
  height: 30rem;
  background: radial-gradient(circle at center, #cfe3f4 0%, transparent 70%);
  animation-delay: -5s;
}

.bg-blob--peach {
  bottom: -14%;
  left: 18%;
  width: 28rem;
  height: 28rem;
  background: radial-gradient(circle at center, #f8dcc4 0%, transparent 70%);
  animation-delay: -10s;
}

@keyframes blob-float {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(2rem, -1.5rem, 0) scale(1.06);
  }
}

/* ---------- 手绘小点缀 ---------- */
.bg-doodle {
  position: absolute;
  pointer-events: none;
  color: var(--color-border);
  opacity: 0.5;
  user-select: none;
}

.bg-doodle--1 {
  top: 14%;
  right: 18%;
  font-size: 2rem;
  transform: rotate(12deg);
}

.bg-doodle--2 {
  bottom: 16%;
  left: 10%;
  font-size: 2.4rem;
  transform: rotate(-8deg);
}
</style>

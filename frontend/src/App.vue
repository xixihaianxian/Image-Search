<script setup>
import { computed, onMounted, ref } from 'vue'

// 后端接口地址
const API_URL = 'http://127.0.0.1:8000/ImageSearch'

// 后端连接状态：checking(检测中) / online(已连接) / offline(未响应)
const backendStatus = ref('checking')

const statusText = computed(() => {
  const texts = {
    checking: '正在连接后端…',
    online: '后端已连接',
    offline: '后端未响应',
  }
  return texts[backendStatus.value]
})

// 进入界面时向 /ImageSearch 发起请求，静默降级，不弹错误
async function checkBackend() {
  try {
    const response = await fetch(API_URL)
    backendStatus.value = response.ok ? 'online' : 'offline'
  } catch {
    backendStatus.value = 'offline'
  }
}

// TODO: 跳转到图片搜索功能页
function handleEnter() {}

onMounted(checkBackend)
</script>

<template>
  <div class="page">
    <!-- 背景装饰：柔和渐变光斑 -->
    <div class="bg-blob bg-blob--indigo" aria-hidden="true"></div>
    <div class="bg-blob bg-blob--sky" aria-hidden="true"></div>
    <div class="bg-blob bg-blob--rose" aria-hidden="true"></div>

    <!-- 中央内容 -->
    <main class="hero">
      <p class="hero__eyebrow">AI · IMAGE RETRIEVAL</p>
      <h1 class="hero__title">
        Image<span class="hero__title-accent">Search</span>
      </h1>
      <p class="hero__subtitle">基于深度学习的图片检索</p>
      <button class="enter-btn" type="button" @click="handleEnter">
        <span class="enter-btn__text">进 入</span>
        <span class="enter-btn__arrow" aria-hidden="true">→</span>
      </button>
    </main>

    <!-- 底部后端状态指示（非按钮） -->
    <footer class="status" :class="`status--${backendStatus}`">
      <span class="status__dot" aria-hidden="true"></span>
      <span class="status__text">{{ statusText }}</span>
    </footer>
  </div>
</template>

<style scoped>
.page {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 100vh;
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

/* ---------- 中央内容 ---------- */
.hero {
  position: relative;
  z-index: 1;
  padding: 0 1.5rem;
  text-align: center;
}

.hero__eyebrow {
  margin-bottom: 1.25rem;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.4em;
  color: var(--color-text-muted);
  animation: fade-up 0.8s ease both;
}

.hero__title {
  font-size: clamp(3rem, 9vw, 5.25rem);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.1;
  color: var(--color-text);
  animation: fade-up 0.8s ease 0.1s both;
}

.hero__title-accent {
  background: linear-gradient(120deg, var(--color-accent) 0%, var(--color-sky) 100%);
  background-clip: text;
  -webkit-background-clip: text;
  color: transparent;
}

.hero__subtitle {
  margin-top: 1rem;
  font-size: clamp(0.95rem, 2.5vw, 1.15rem);
  letter-spacing: 0.25em;
  color: var(--color-text-secondary);
  animation: fade-up 0.8s ease 0.2s both;
}

/* ---------- 进入按钮 ---------- */
.enter-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 3.5rem;
  padding: 0.95rem 3.2rem;
  border: 1px solid var(--color-border);
  border-radius: 9999px;
  background: var(--color-card);
  color: var(--color-text);
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: 0.3em;
  text-indent: 0.3em; /* 抵消最后一个字的字距，保持视觉居中 */
  box-shadow:
    0 4px 14px rgba(100, 116, 139, 0.08),
    0 12px 32px rgba(99, 102, 241, 0.1);
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease,
    border-color 0.25s ease;
  animation: fade-up 0.8s ease 0.35s both;
}

.enter-btn__arrow {
  letter-spacing: 0;
  text-indent: 0;
  font-weight: 400;
  color: var(--color-accent);
  transition: transform 0.25s ease;
}

.enter-btn:hover {
  transform: translateY(-3px);
  border-color: var(--color-accent-light);
  box-shadow:
    0 6px 18px rgba(100, 116, 139, 0.1),
    0 18px 44px rgba(99, 102, 241, 0.18);
}

.enter-btn:hover .enter-btn__arrow {
  transform: translateX(4px);
}

.enter-btn:active {
  transform: translateY(-1px);
  box-shadow:
    0 3px 10px rgba(100, 116, 139, 0.08),
    0 8px 20px rgba(99, 102, 241, 0.12);
}

.enter-btn:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 3px;
}

/* ---------- 底部状态指示 ---------- */
.status {
  position: absolute;
  bottom: 1.75rem;
  left: 0;
  right: 0;
  margin-inline: auto;
  width: fit-content;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.9rem;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
  border: 1px solid var(--color-border);
  font-size: 0.78rem;
  color: var(--color-text-muted);
  animation: fade-up 0.8s ease 0.5s both;
}

.status__dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: #fbbf24;
}

.status--checking .status__dot {
  animation: dot-pulse 1.2s ease-in-out infinite;
}

.status--online .status__dot {
  background: #34d399;
}

.status--offline .status__dot {
  background: #cbd5e1;
}

@keyframes dot-pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.45;
    transform: scale(0.8);
  }
}

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(1.25rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

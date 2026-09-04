<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

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

// 进入图搜图页面
function handleEnter() {
  router.push({ name: 'search' })
}

onMounted(checkBackend)
</script>

<template>
  <main class="hero">
    <div class="hero__stamp" aria-hidden="true">EST. 2024</div>
    <div class="hero__orbit hero__orbit--left" aria-hidden="true"></div>
    <div class="hero__orbit hero__orbit--right" aria-hidden="true"></div>

    <section class="hero__content" aria-labelledby="home-title">
      <p class="hero__eyebrow"><span class="eyebrow-line"></span> AI · IMAGE RETRIEVAL <span class="eyebrow-line"></span></p>
      <h1 id="home-title" class="hero__title">
        Image<span class="hero__title-accent">Search</span>
      </h1>
      <p class="hero__subtitle">把灵感放进相册，让相似图片自己浮现</p>
      <div class="hero__rule" aria-hidden="true"><span></span><i>✦</i><span></span></div>
      <p class="hero__hint">选择图片 · 连接图库 · 开始探索</p>
      <button class="enter-btn" type="button" @click="handleEnter">
        <span class="enter-btn__text">进 入 工 作 台</span>
        <span class="enter-btn__arrow" aria-hidden="true">↗</span>
      </button>
    </section>

    <div class="hero__notes" aria-hidden="true">
      <span>visual notes</span>
      <span>find your mood</span>
    </div>
  </main>

  <!-- 底部后端状态指示（非按钮） -->
  <footer class="status" :class="`status--${backendStatus}`">
    <span class="status__dot" aria-hidden="true"></span>
    <span class="status__text">{{ statusText }}</span>
  </footer>
</template>

<style scoped>
/* ---------- 中央内容 ---------- */
.hero {
  position: relative;
  z-index: 1;
  display: grid;
  place-items: center;
  height: 100vh;
  padding: 2rem;
  overflow: hidden;
  text-align: center;
}

.hero__content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 42rem;
  padding: 3.5rem 4.5rem;
  border: 1px solid rgba(216, 201, 181, 0.78);
  border-radius: 44% 12% 42% 10% / 12% 42% 10% 44%;
  background: rgba(255, 253, 248, 0.66);
  box-shadow: 0 24px 70px rgba(132, 103, 83, 0.12), inset 0 0 0 8px rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(5px);
  animation: fade-up 0.8s ease both;
}

.hero__stamp {
  position: absolute;
  top: 12%;
  left: 9%;
  padding: 0.45rem 0.8rem;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-family: 'Patrick Hand', cursive;
  font-size: 0.8rem;
  letter-spacing: 0.18em;
  transform: rotate(-12deg);
}

.hero__notes {
  position: absolute;
  right: 9%;
  bottom: 13%;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  color: var(--color-text-muted);
  font-family: 'Patrick Hand', cursive;
  font-size: 0.9rem;
  text-align: left;
  transform: rotate(8deg);
}

.hero__eyebrow {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 1.5rem;
  color: var(--color-accent-deep);
  font-size: 0.82rem;
  letter-spacing: 0.22em;
}

.eyebrow-line { width: 2.2rem; height: 1px; background: var(--color-accent); }

.hero__title {
  font-size: clamp(3rem, 8vw, 5.8rem);
  line-height: 1;
  letter-spacing: -0.04em;
  color: var(--color-text);
}

.hero__title-accent { color: var(--color-accent-deep); }

.hero__subtitle {
  margin-top: 1.4rem;
  color: var(--color-text-secondary);
  font-size: 1.08rem;
  letter-spacing: 0.08em;
}

.hero__rule { display: flex; align-items: center; gap: 0.7rem; width: 100%; margin-top: 1.8rem; color: var(--color-accent); }
.hero__rule span { flex: 1; height: 1px; background: var(--color-border); }
.hero__rule i { font-size: 0.9rem; font-style: normal; }
.hero__hint { margin-top: 0.9rem; color: var(--color-text-muted); font-size: 0.78rem; letter-spacing: 0.12em; }

/* ---------- 进入按钮 ---------- */
.enter-btn {
  display: inline-flex;
  align-items: center;
  gap: 1rem;
  margin-top: 2.2rem;
  padding: 0.9rem 1.4rem 0.9rem 1.8rem;
  border: 1px solid var(--color-text);
  border-radius: 999px;
  background: var(--color-text);
  color: #fffdf8;
  font-size: 0.95rem;
  letter-spacing: 0.16em;
  box-shadow: 5px 5px 0 var(--color-accent-light);
  transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}

.enter-btn__arrow { display: grid; place-items: center; width: 2rem; height: 2rem; border-radius: 50%; background: var(--color-accent); color: var(--color-text); font-size: 1.15rem; letter-spacing: 0; transition: transform 0.2s ease; }
.enter-btn:hover { transform: translate(-2px, -2px); background: var(--color-accent-deep); box-shadow: 7px 7px 0 var(--color-accent-light); }
.enter-btn:hover .enter-btn__arrow { transform: rotate(45deg); }
.enter-btn:active { transform: translate(2px, 2px); box-shadow: 2px 2px 0 var(--color-accent-light); }
.enter-btn:focus-visible { outline: 2px dashed var(--color-accent-deep); outline-offset: 4px; }

/* ---------- 底部状态指示 ---------- */
.status { position: absolute; bottom: 1.75rem; left: 0; right: 0; z-index: 1; display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem; width: fit-content; margin-inline: auto; padding: 0.45rem 0.9rem; border: 1px solid var(--color-border); border-radius: 999px; background: rgba(255, 253, 248, 0.72); color: var(--color-text-secondary); font-size: 0.8rem; backdrop-filter: blur(8px); animation: fade-up 0.8s ease 0.5s both; }
.status__dot { width: 0.48rem; height: 0.48rem; border-radius: 50%; background: #f4c28a; }
.status--checking .status__dot { animation: dot-pulse 1.2s ease-in-out infinite; }
.status--online .status__dot { background: var(--color-success); }
.status--offline .status__dot { background: var(--color-text-muted); }

@media (max-width: 700px) {
  .hero { padding: 1rem; }
  .hero__content { width: 100%; padding: 3rem 1.5rem; }
  .hero__stamp, .hero__notes { display: none; }
  .hero__eyebrow { font-size: 0.68rem; gap: 0.45rem; }
  .eyebrow-line { width: 1.2rem; }
}

@keyframes dot-pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.4;
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

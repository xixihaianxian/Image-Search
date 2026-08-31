<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { loadLocalGallery, resolveImageUrl } from '../api'

// ---------- 工具栏收起/展开 ----------
const toolbarCollapsed = ref(false)

function toggleToolbar() {
  toolbarCollapsed.value = !toolbarCollapsed.value
}

// ---------- 查询图片 ----------
const fileInput = ref(null)
const queryImage = ref(null) // { url, name }
let queryObjectUrl = null

function triggerPickImage() {
  fileInput.value?.click()
}

function onFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (queryObjectUrl) URL.revokeObjectURL(queryObjectUrl)
  queryObjectUrl = URL.createObjectURL(file)
  queryImage.value = { url: queryObjectUrl, name: file.name }
  // 清空 value，允许重复选择同一文件
  event.target.value = ''
}

// 移除已选查询图片
function clearQueryImage() {
  if (queryObjectUrl) URL.revokeObjectURL(queryObjectUrl)
  queryObjectUrl = null
  queryImage.value = null
}

// ---------- 查询图片右键菜单 ----------
const ctxMenu = ref({ visible: false, x: 0, y: 0 })
const lightboxVisible = ref(false)

function openCtxMenu(event) {
  event.preventDefault()
  if (!queryImage.value) return
  // 视口边缘防溢出
  const x = Math.min(event.clientX, window.innerWidth - 170)
  const y = Math.min(event.clientY, window.innerHeight - 150)
  ctxMenu.value = { visible: true, x, y }
}

function closeCtxMenu() {
  ctxMenu.value.visible = false
}

function ctxZoom() {
  closeCtxMenu()
  lightboxVisible.value = true
}

async function ctxCopyPath() {
  closeCtxMenu()
  try {
    await navigator.clipboard.writeText(queryImage.value?.name ?? '')
    showToast('已复制文件名（浏览器无法获取完整本地路径）')
  } catch {
    showToast('复制失败')
  }
}

function ctxDownload() {
  closeCtxMenu()
  if (!queryImage.value) return
  const link = document.createElement('a')
  link.href = queryImage.value.url
  link.download = queryImage.value.name
  link.click()
}

// ---------- 开始搜索 ----------
function startSearch() {
  if (!queryImage.value) return
  // TODO: 待后端提供以图搜图接口后，在此上传查询图片并渲染检索结果
  showToast('后端检索接口尚未接入，敬请期待')
}

// ---------- 轻提示 ----------
const toastMessage = ref('')
const toastVisible = ref(false)
let toastTimer = null

function showToast(message) {
  toastMessage.value = message
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastVisible.value = false
  }, 2600)
}

onBeforeUnmount(() => {
  if (queryObjectUrl) URL.revokeObjectURL(queryObjectUrl)
  clearTimeout(toastTimer)
})

// ---------- 本地图库（原生目录选择） ----------
const galleryImages = ref([]) // [{ name, url }]
const galleryFolder = ref('') // 选中目录的绝对路径
const galleryLoading = ref(false)
const galleryError = ref('')

// 点击「目录」：弹出原生目录选择框，拿绝对路径后请求后端扫盘
async function selectDirectory() {
  if (!window.api?.selectDirectory) {
    showToast('目录选择需在 Electron 桌面端使用')
    return
  }
  const folderPath = await window.api.selectDirectory()
  if (!folderPath) return // 用户取消
  galleryLoading.value = true
  galleryError.value = ''
  try {
    const images = await loadLocalGallery(folderPath)
    galleryFolder.value = folderPath
    galleryImages.value = images.map(item => ({
      name: item.name,
      url: resolveImageUrl(item.imageUrl),
    }))
  } catch (error) {
    galleryError.value = error instanceof Error ? error.message : String(error)
  } finally {
    galleryLoading.value = false
  }
}
</script>

<template>
  <div class="search-page">
    <!-- 左侧工具栏 -->
    <aside class="toolbar" :class="{ 'toolbar--collapsed': toolbarCollapsed }">
      <button
        class="toolbar__back"
        type="button"
        :title="toolbarCollapsed ? '展开工具栏' : '收起工具栏'"
        @click="toggleToolbar"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
          <path d="M15 5l-7 7 7 7" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <span v-show="!toolbarCollapsed" class="toolbar__label">工具栏</span>
    </aside>

    <!-- 主体两栏 -->
    <div class="content">
      <!-- 左：查询图片 -->
      <section class="panel-col">
        <div class="card query-card">
          <template v-if="queryImage">
            <img
              class="query-card__img"
              :src="queryImage.url"
              :alt="queryImage.name"
              @contextmenu="openCtxMenu"
            />
            <button
              class="query-card__remove"
              type="button"
              title="移除图片"
              @click="clearQueryImage"
            >
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" aria-hidden="true">
                <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" />
              </svg>
            </button>
            <span class="query-card__name">{{ queryImage.name }}</span>
          </template>
          <div v-else class="card-empty">
            <svg class="card-empty__icon" viewBox="0 0 48 48" fill="none" aria-hidden="true">
              <rect x="5" y="9" width="38" height="30" rx="4" stroke="currentColor" stroke-width="2.6" />
              <circle cx="17" cy="19" r="3.4" fill="currentColor" />
              <path d="M9 34l10-10 7 7 5-5 8 8" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <p>点击下方「选择图片」<br />上传要检索的图片</p>
          </div>
        </div>
        <input
          ref="fileInput"
          class="visually-hidden"
          type="file"
          accept="image/*"
          @change="onFileChange"
        />
        <div class="query-actions">
          <button class="pill-btn" type="button" @click="triggerPickImage">
            选 择 图 片
          </button>
          <button
            class="pill-btn pill-btn--primary"
            type="button"
            title="上传查询图片后开始检索"
            :disabled="!queryImage"
            @click="startSearch"
          >
            开 始 搜 索
          </button>
        </div>
      </section>

      <!-- 右：检索结果 -->
      <section class="panel-col panel-col--results">
        <div class="card result-card">
          <span v-if="galleryImages.length" class="result-card__count">
            共 {{ galleryImages.length }} 张
          </span>

          <!-- 加载中 -->
          <div v-if="galleryLoading" class="card-empty">
            <span class="spinner" aria-hidden="true"></span>
            <p>正在扫描目录…</p>
          </div>

          <!-- 出错 -->
          <div v-else-if="galleryError" class="result-error">{{ galleryError }}</div>

          <!-- 图库网格 -->
          <div v-else-if="galleryImages.length" class="result-grid">
            <figure v-for="item in galleryImages" :key="item.url" class="result-item">
              <img :src="item.url" :alt="item.name" :title="item.name" loading="lazy" />
              <figcaption>{{ item.name }}</figcaption>
            </figure>
          </div>

          <!-- 空状态 -->
          <div v-else class="card-empty">
            <svg class="card-empty__icon" viewBox="0 0 48 48" fill="none" aria-hidden="true">
              <path d="M6 14a4 4 0 0 1 4-4h8l4 5h16a4 4 0 0 1 4 4v17a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4V14z" stroke="currentColor" stroke-width="2.6" stroke-linejoin="round" />
              <path d="M18 27l6-6 5 5 3-3 6 6" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <p>点击右下角「目录」<br />加载本地图片库</p>
          </div>
        </div>
        <!-- 本地目录选择：展示框与按钮拼接为一体 -->
        <div class="dir-group">
          <div class="dir-display" :title="galleryFolder">
            <span class="dir-display__text">{{ galleryFolder || '未选择目录' }}</span>
          </div>
          <button class="dir-group__btn" type="button" @click="selectDirectory">目 录</button>
        </div>
      </section>
    </div>

    <!-- 轻提示 -->
    <Teleport to="body">
      <Transition name="toast-fade">
        <div v-if="toastVisible" class="toast" role="status">{{ toastMessage }}</div>
      </Transition>
    </Teleport>

    <!-- 图片右键菜单 -->
    <Teleport to="body">
      <div
        v-if="ctxMenu.visible"
        class="ctx-overlay"
        @click="closeCtxMenu"
        @contextmenu.prevent="closeCtxMenu"
      >
        <div class="ctx-menu" :style="{ left: `${ctxMenu.x}px`, top: `${ctxMenu.y}px` }">
          <button class="ctx-menu__item" type="button" @click="ctxZoom">放 大</button>
          <button class="ctx-menu__item" type="button" @click="ctxCopyPath">复制路径</button>
          <button class="ctx-menu__item" type="button" @click="ctxDownload">下 载</button>
        </div>
      </div>
    </Teleport>

    <!-- 放大预览 -->
    <Teleport to="body">
      <Transition name="view-fade">
        <div v-if="lightboxVisible" class="lightbox" @click="lightboxVisible = false">
          <img :src="queryImage?.url" :alt="queryImage?.name" />
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* ---------- 页面布局 ---------- */
.search-page {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 1rem;
  height: 100vh;
  padding: 1rem;
  animation: fade-in 0.5s ease both;
}

/* ---------- 工具栏 ---------- */
.toolbar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.4rem;
  width: 4.25rem;
  padding: 1rem 0;
  border: 1px solid var(--color-border);
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.07);
  transition: width 0.28s ease;
}

/* 收起态：变窄并隐藏文字标签 */
.toolbar--collapsed {
  width: 3.4rem;
}

.toolbar__back {
  display: grid;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  background: var(--color-card);
  color: var(--color-text-secondary);
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    color 0.2s ease;
}

.toolbar__back:hover {
  transform: translateY(-1px);
  border-color: var(--color-accent-light);
  color: var(--color-accent);
}

.toolbar__back:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

/* 收起时箭头转向右侧，提示可展开 */
.toolbar__back svg {
  transition: transform 0.28s ease;
}

.toolbar--collapsed .toolbar__back svg {
  transform: rotate(180deg);
}

.toolbar__label {
  margin-top: 0.4rem;
  writing-mode: vertical-rl;
  font-size: 0.8rem;
  letter-spacing: 0.5em;
  color: var(--color-text-muted);
  user-select: none;
}

/* ---------- 主体两栏 ---------- */
.content {
  display: grid;
  flex: 1;
  grid-template-columns: minmax(280px, 2fr) 3fr;
  gap: 1rem;
  min-height: 0;
  min-width: 0;
}

.panel-col {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 0;
  min-width: 0;
}

/* 查询图下方的按钮组：选择图片 + 开始搜索 */
.query-actions {
  display: flex;
  gap: 0.75rem;
}

.query-actions .pill-btn {
  flex: 1;
  padding-inline: 1rem;
}

/* ---------- 目录组：展示框与按钮拼接为一体 ---------- */
.dir-group {
  display: flex;
  min-width: 0;
  padding: 3px;
  border-radius: 9999px;
  background: #eef1fb;
  box-shadow:
    0 4px 14px rgba(100, 116, 139, 0.08),
    0 10px 26px rgba(99, 102, 241, 0.09);
}

.dir-display {
  display: flex;
  flex: 1;
  align-items: center;
  min-width: 0;
  padding: 0 1.25rem;
}

.dir-display__text {
  overflow: hidden;
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.dir-group__btn {
  flex-shrink: 0;
  margin-left: auto;
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 9999px;
  background: linear-gradient(120deg, var(--color-accent) 0%, var(--color-sky) 100%);
  color: #ffffff;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-indent: 0.15em;
  transition: filter 0.2s ease;
}

.dir-group__btn:hover {
  filter: brightness(0.94);
}

.dir-group__btn:focus-visible {
  outline: 2px solid #475569;
  outline-offset: 2px;
}

/* ---------- 轻提示 ---------- */
.toast {
  position: fixed;
  bottom: 2.2rem;
  left: 50%;
  z-index: 60;
  padding: 0.6rem 1.3rem;
  border-radius: 9999px;
  background: rgba(30, 41, 59, 0.85);
  color: #f8fafc;
  font-size: 0.85rem;
  white-space: nowrap;
  backdrop-filter: blur(6px);
  box-shadow: 0 10px 30px rgba(30, 41, 59, 0.25);
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(0.6rem);
}

/* ---------- 卡片 ---------- */
.card {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  border: 1px solid rgba(99, 102, 241, 0.16);
  border-radius: 1.25rem;
  background: linear-gradient(170deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 255, 0.7) 100%);
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.07);
}

/* 查询图卡片：叠加淡靛蓝渐变，与结果卡形成主次 */
.query-card {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background:
    linear-gradient(165deg, rgba(99, 102, 241, 0.07) 0%, rgba(56, 189, 248, 0.03) 45%, rgba(255, 255, 255, 0) 100%),
    linear-gradient(170deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 255, 0.7) 100%);
}

.query-card__img {
  max-width: 100%;
  max-height: 100%;
  min-height: 0;
  border-radius: 0.75rem;
  object-fit: contain;
  box-shadow: 0 6px 20px rgba(100, 116, 139, 0.16);
}

/* 悬停显示的移除按钮（红叉） */
.query-card__remove {
  position: absolute;
  top: 0.85rem;
  right: 0.85rem;
  z-index: 1;
  display: grid;
  place-items: center;
  width: 1.75rem;
  height: 1.75rem;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #e11d48;
  box-shadow: 0 4px 12px rgba(30, 41, 59, 0.18);
  opacity: 0;
  transform: scale(0.85);
  transition:
    opacity 0.2s ease,
    transform 0.2s ease,
    background-color 0.2s ease,
    color 0.2s ease;
}

.query-card:hover .query-card__remove {
  opacity: 1;
  transform: scale(1);
}

.query-card__remove:hover {
  background: #e11d48;
  color: #ffffff;
}

.query-card__remove:focus-visible {
  outline: 2px solid #e11d48;
  outline-offset: 2px;
}

.query-card__name {
  position: absolute;
  bottom: 0.75rem;
  left: 50%;
  transform: translateX(-50%);
  max-width: calc(100% - 2rem);
  padding: 0.3rem 0.8rem;
  overflow: hidden;
  border-radius: 9999px;
  background: rgba(30, 41, 59, 0.72);
  color: #f8fafc;
  font-size: 0.75rem;
  white-space: nowrap;
  text-overflow: ellipsis;
  backdrop-filter: blur(6px);
}

/* 空状态 */
.card-empty {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: center;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  line-height: 1.9;
  user-select: none;
}

.card-empty__icon {
  width: 3.25rem;
  height: 3.25rem;
  color: var(--color-accent-light);
}

/* ---------- 加载指示 ---------- */
.spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid var(--color-accent-light);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ---------- 结果网格 ---------- */
.result-card {
  display: flex;
  flex-direction: column;
  padding: 1rem;
}

/* 结果卡片内的空状态/加载态：撑满卡片并垂直居中 */
.result-card > .card-empty {
  flex: 1;
  justify-content: center;
}

.result-card__count {
  position: absolute;
  top: 0.85rem;
  right: 0.9rem;
  z-index: 1;
  padding: 0.25rem 0.75rem;
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 9999px;
  background: rgba(238, 242, 255, 0.92);
  color: var(--color-accent);
  font-size: 0.72rem;
  font-weight: 600;
  backdrop-filter: blur(6px);
}

.result-grid {
  display: grid;
  flex: 1;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.9rem;
  align-content: start;
  min-height: 0;
  padding: 0.15rem;
  padding-right: 0.5rem;
  overflow-y: auto;
  animation: fade-in 0.4s ease both;
}

.result-grid::-webkit-scrollbar {
  width: 6px;
}

.result-grid::-webkit-scrollbar-thumb {
  border-radius: 9999px;
  background: #c7d2fe;
}

.result-item {
  margin: 0;
  overflow: hidden;
  border: 1px solid rgba(99, 102, 241, 0.14);
  border-radius: 0.9rem;
  background: var(--color-card);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.result-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 24px rgba(99, 102, 241, 0.16);
}

.result-item img {
  display: block;
  aspect-ratio: 4 / 3;
  width: 100%;
  object-fit: cover;
}

.result-item figcaption {
  padding: 0.45rem 0.65rem;
  overflow: hidden;
  color: var(--color-text-secondary);
  font-size: 0.72rem;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* 错误提示 */
.result-error {
  display: grid;
  place-items: center;
  flex: 1;
  color: #e11d48;
  font-size: 0.9rem;
}

/* ---------- 按钮 ---------- */
.pill-btn {
  padding: 0.8rem 2.2rem;
  border: 1px solid var(--color-border);
  border-radius: 9999px;
  background: var(--color-card);
  color: var(--color-text);
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-indent: 0.15em;
  box-shadow:
    0 4px 14px rgba(100, 116, 139, 0.08),
    0 10px 26px rgba(99, 102, 241, 0.09);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease,
    opacity 0.2s ease;
}

.pill-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  border-color: var(--color-accent-light);
  box-shadow:
    0 6px 18px rgba(100, 116, 139, 0.1),
    0 14px 34px rgba(99, 102, 241, 0.16);
}

.pill-btn:active:not(:disabled) {
  transform: translateY(0);
}

.pill-btn:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 3px;
}

.pill-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.pill-btn--primary {
  border-color: transparent;
  background: linear-gradient(120deg, var(--color-accent) 0%, var(--color-sky) 100%);
  color: #ffffff;
}

/* ---------- 图片右键菜单 ---------- */
.ctx-overlay {
  position: fixed;
  inset: 0;
  z-index: 55;
}

.ctx-menu {
  position: fixed;
  z-index: 56;
  min-width: 9.5rem;
  padding: 0.4rem;
  border: 1px solid var(--color-border);
  border-radius: 0.85rem;
  background: #ffffff;
  box-shadow: 0 16px 40px rgba(30, 41, 59, 0.16);
  animation: menu-pop 0.16s ease both;
}

@keyframes menu-pop {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-4px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.ctx-menu__item {
  display: block;
  width: 100%;
  padding: 0.55rem 1rem;
  border: none;
  border-radius: 0.6rem;
  background: transparent;
  color: var(--color-text);
  font-size: 0.88rem;
  text-align: left;
  letter-spacing: 0.05em;
  transition:
    background-color 0.15s ease,
    color 0.15s ease;
}

.ctx-menu__item:hover {
  background: #eef2ff;
  color: var(--color-accent);
}

/* ---------- 放大预览 ---------- */
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: grid;
  place-items: center;
  padding: 2.5rem;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(6px);
  cursor: zoom-out;
}

.lightbox img {
  max-width: 100%;
  max-height: 100%;
  border-radius: 0.75rem;
  object-fit: contain;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.4);
}

.view-fade-enter-active,
.view-fade-leave-active {
  transition: opacity 0.22s ease;
}

.view-fade-enter-from,
.view-fade-leave-to {
  opacity: 0;
}

/* ---------- 工具类 ---------- */
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}

@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* ---------- 窄屏适配 ---------- */
@media (max-width: 900px) {
  .search-page {
    flex-direction: column;
    height: auto;
    min-height: 100vh;
    overflow-y: auto;
  }

  .toolbar {
    flex-direction: row;
    width: auto;
    padding: 0.5rem 1rem;
  }

  .toolbar__label {
    margin-top: 0;
    writing-mode: horizontal-tb;
  }

  .content {
    grid-template-columns: 1fr;
  }

  .card {
    min-height: 300px;
  }
}
</style>

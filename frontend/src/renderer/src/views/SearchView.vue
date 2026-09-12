<script setup>
import { onBeforeUnmount, onMounted, ref, nextTick } from 'vue'
import { uploadAnchorBox, uploadLocalGallery, displayGallery, displayModels, generateFeatures, resolveImageUrl, selectTarget, slowSearchImages, swiftSearchImages } from '../api'

// ---------- 工具栏收起/展开 ----------
const toolbarCollapsed = ref(false)

// ---------- 特征方法 ----------
const featureMethods = ref([])
const selectedFeatureMethod = ref('vgg16')
const featureMenuOpen = ref(false)
const featureToolEl = ref(null)
const featureMethodsLoading = ref(false)
const featureMethodsError = ref('')

// ---------- 搜索方式 ----------
const searchModes = [
  { id: 'slow', name: 'slow', description: '当前可用 · 全量相似度搜索' },
  { id: 'swift', name: 'swift', description: '暂未接入 · FAISS 快速搜索' },
]
const selectedSearchMode = ref('slow')
const searchMenuOpen = ref(false)
const searchToolEl = ref(null)
const searchTop = ref(20)
const boxSelectEnabled = ref(false)
const boxSelecting = ref(false)
const boxUploading = ref(false)
const boxImageEl = ref(null)
const boxSelection = ref(null)
let boxStartPoint = null

function toggleBoxSelect() {
  boxSelectEnabled.value = !boxSelectEnabled.value
  if (!boxSelectEnabled.value) {
    boxSelecting.value = false
    boxSelection.value = null
  }
}

function getBoxPoint(event) {
  const rect = boxImageEl.value?.getBoundingClientRect()
  if (!rect) return null
  return {
    x: Math.max(0, Math.min(event.clientX - rect.left, rect.width)),
    y: Math.max(0, Math.min(event.clientY - rect.top, rect.height)),
  }
}

function onBoxPointerDown(event) {
  if (!boxSelectEnabled.value || !queryImage.value || boxUploading.value) return
  event.preventDefault()
  boxImageEl.value?.setPointerCapture?.(event.pointerId)
  boxStartPoint = getBoxPoint(event)
  boxSelecting.value = true
  boxSelection.value = { left: boxStartPoint.x, top: boxStartPoint.y, width: 0, height: 0 }
}

function onBoxPointerMove(event) {
  if (!boxSelecting.value || !boxStartPoint) return
  const point = getBoxPoint(event)
  const left = Math.min(boxStartPoint.x, point.x)
  const top = Math.min(boxStartPoint.y, point.y)
  boxSelection.value = {
    left,
    top,
    width: Math.abs(point.x - boxStartPoint.x),
    height: Math.abs(point.y - boxStartPoint.y),
  }
}

async function onBoxPointerUp(event) {
  if (!boxSelecting.value) return
  const point = getBoxPoint(event)
  onBoxPointerMove(event)
  boxSelecting.value = false
  boxStartPoint = null
  if (!point || !boxSelection.value || boxSelection.value.width < 8 || boxSelection.value.height < 8) {
    boxSelection.value = null
    showToast('框选区域太小，请重新选择')
    return
  }
  await uploadSelectedBox()
}

async function uploadSelectedBox() {
  const img = boxImageEl.value
  const selection = boxSelection.value
  if (!img || !selection || !queryImage.value) return
  boxUploading.value = true
  try {
    let sourceBlob
    if (queryImage.value.path && window.api?.readLocalImage) {
      const localImage = await window.api.readLocalImage(queryImage.value.path)
      sourceBlob = new Blob([new Uint8Array(localImage.data)], { type: localImage.type })
    } else {
      const response = await fetch(queryImage.value.url)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      sourceBlob = await response.blob()
    }
    const sourceUrl = URL.createObjectURL(sourceBlob)
    const sourceImage = new Image()
    sourceImage.src = sourceUrl
    await new Promise((resolve, reject) => {
      sourceImage.onload = resolve
      sourceImage.onerror = reject
    })
    const scaleX = sourceImage.naturalWidth / img.clientWidth
    const scaleY = sourceImage.naturalHeight / img.clientHeight
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(selection.width * scaleX))
    canvas.height = Math.max(1, Math.round(selection.height * scaleY))
    canvas.getContext('2d').drawImage(
      sourceImage,
      Math.round(selection.left * scaleX), Math.round(selection.top * scaleY), canvas.width, canvas.height,
      0, 0, canvas.width, canvas.height,
    )
    URL.revokeObjectURL(sourceUrl)
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'))
    if (!blob) throw new Error('无法生成裁剪图片')
    const formData = new FormData()
    const galleryImagePath = galleryImages.value[0]?.path
    if (!galleryImagePath) throw new Error('请先选择图片库目录')
    formData.append('anchor', blob, 'anchor.png')
    formData.append('method', selectedFeatureMethod.value)
    formData.append('top', String(searchTop.value))
    formData.append('image_path', galleryImagePath)
    formData.append('search_model', selectedSearchMode.value)
    const results = await uploadAnchorBox(formData)
    searchError.value = ''
    searchResults.value = results.map(item => ({
      name: item.name || item.image?.split(/[\\/]/).pop() || '图片',
      extension: item.extension || '',
      path: item.image,
      url: resolveImageUrl(item.thumbnail),
      similarity: item.similarity,
    }))
    if (!searchResults.value.length) {
      showToast('框选请求成功，但后端没有返回搜索结果')
    } else {
      showToast(`已找到 ${searchResults.value.length} 张相似图片`)
    }
  } catch (error) {
    showToast(error instanceof Error ? error.message : String(error))
  } finally {
    boxUploading.value = false
  }
}
const topAudio = new Audio('/audio/pyk-toon-n-n.mp3')
topAudio.loop = false
topAudio.volume = 0.55
let topAudioActive = false

function startTopAudio() {
  if (topAudioActive) return
  topAudioActive = true
  topAudio.currentTime = 0
  topAudio.play().catch(() => {})
}

function stopTopAudio() {
  topAudioActive = false
  topAudio.pause()
}

function onTopKeyDown(event) {
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight' || event.key === 'Home' || event.key === 'End') {
    startTopAudio()
  }
}

async function toggleFeatureMenu() {
  featureMenuOpen.value = !featureMenuOpen.value
  if (!featureMenuOpen.value) return

  featureMethodsLoading.value = true
  featureMethodsError.value = ''
  try {
    const models = await displayModels()
    featureMethods.value = models.map(model => ({
      id: model.toLowerCase(),
      name: model.toUpperCase(),
      description: model.toLowerCase() === 'vgg16' ? '通用图像特征' : '后端已注册的方法',
    }))
    if (featureMethods.value.length && !featureMethods.value.some(method => method.id === selectedFeatureMethod.value)) {
      selectedFeatureMethod.value = featureMethods.value[0].id
    }
  } catch (error) {
    featureMethodsError.value = error instanceof Error ? error.message : String(error)
  } finally {
    featureMethodsLoading.value = false
  }
}

function selectFeatureMethod(method) {
  selectedFeatureMethod.value = method.id
  featureMenuOpen.value = false
  showToast(`已选择 ${method.name}`)
}

function closeFeatureMenuOnOutsideClick(event) {
  if (featureToolEl.value && !featureToolEl.value.contains(event.target)) {
    featureMenuOpen.value = false
  }
  if (searchToolEl.value && !searchToolEl.value.contains(event.target)) {
    searchMenuOpen.value = false
  }
}

function closeFeatureMenuOnEscape(event) {
  if (event.key === 'Escape') {
    featureMenuOpen.value = false
    searchMenuOpen.value = false
  }
}

function toggleSearchMenu() {
  searchMenuOpen.value = !searchMenuOpen.value
}

function selectSearchMode(mode) {
  selectedSearchMode.value = mode.id
  searchMenuOpen.value = false
  showToast(`已选择 ${mode.name} 搜索`)
}

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

async function onFileChange(event) {
  const file = event.target.files?.[0]
  // 清空 value，允许重复选择同一文件
  event.target.value = ''
  if (!file) return

  // Electron 下取选中文件的绝对路径（新版 Electron 移除了 File.path）
  const filePath = window.api?.getPathForFile ? window.api.getPathForFile(file) : (file.path ?? '')
  if (!filePath) {
    fallbackLocalPreview(file)
    showToast('未获取到文件路径，当前展示本地预览')
    return
  }

  try {
    // 路径发给后端登记，用后端返回的信息展示
    const data = await selectTarget(filePath)
    releaseQueryObjectUrl()
    const displayUrl = resolveImageUrl(data.imageUrl)
    queryImage.value = {
      // 加时间戳破坏缓存，避免查询图的 <img> 加载污染之后可能的 cors 请求
      url: `${displayUrl}${displayUrl.includes('?') ? '&' : '?'}_t=${Date.now()}`,
      name: data.name || file.name,
      path: filePath,
    }
  } catch (error) {
    // 接口失败时退回本地预览，保证可用
    fallbackLocalPreview(file)
    showToast(error instanceof Error ? error.message : String(error))
  }
}

// 释放当前查询图的对象地址
function releaseQueryObjectUrl() {
  if (queryObjectUrl) {
    URL.revokeObjectURL(queryObjectUrl)
    queryObjectUrl = null
  }
}

// 本地 blob 预览兜底（无路径/接口失败时）
function fallbackLocalPreview(file) {
  releaseQueryObjectUrl()
  queryObjectUrl = URL.createObjectURL(file)
  queryImage.value = { url: queryObjectUrl, name: file.name }
}

// 移除已选查询图片
function clearQueryImage() {
  if (queryObjectUrl) URL.revokeObjectURL(queryObjectUrl)
  queryObjectUrl = null
  queryImage.value = null
  boxSelection.value = null
  boxSelecting.value = false
}

// ---------- 图片右键菜单（查询图 / 图库图通用） ----------
const ctxMenu = ref({ visible: false, x: 0, y: 0 })
const ctxTarget = ref(null) // 右键目标图片 { name, url, path? }
const zoomImage = ref(null) // 放大预览的图片
const lightboxVisible = ref(false)

// 拿原图地址：图库图用 path 走 get/localImage（原图），查询图就是本地 blob
// 加时间戳参数破坏缓存：no-cors 的 <img> 加载会把"无 CORS 头"的响应存进 HTTP 缓存，
// 污染之后 cors 模式的下载/放大请求
function itemOriginalUrl(item) {
  if (!item) return ''
  if (item.path) {
    const url = resolveImageUrl(`/retrieve/get/localImage?image=${encodeURIComponent(item.path)}`)
    return `${url}${url.includes('?') ? '&' : '?'}_t=${Date.now()}`
  }
  return item.url
}

function openMenu(event, target) {
  event.preventDefault()
  if (!target) return
  ctxTarget.value = target
  // 视口边缘防溢出
  const x = Math.min(event.clientX, window.innerWidth - 170)
  const y = Math.min(event.clientY, window.innerHeight - 150)
  ctxMenu.value = { visible: true, x, y }
}

function openCtxMenu(event) {
  openMenu(event, queryImage.value)
}

function openGalleryMenu(event, item) {
  openMenu(event, item)
}

function closeCtxMenu() {
  ctxMenu.value.visible = false
}

function ctxZoom() {
  closeCtxMenu()
  zoomImage.value = {
    url: itemOriginalUrl(ctxTarget.value),
    name: ctxTarget.value?.name,
  }
  lightboxVisible.value = true
}

// 在资源管理器中打开图片所在位置并选中
function ctxOpen() {
  closeCtxMenu()
  const target = ctxTarget.value
  if (!target?.path) {
    showToast('该图片没有可定位的本地路径')
    return
  }
  window.api?.showItemInFolder(target.path)
}

async function ctxCopyPath() {
  closeCtxMenu()
  const target = ctxTarget.value
  if (!target) return
  try {
    if (target.path) {
      // 图库图：DB 里存的是真实绝对路径
      await navigator.clipboard.writeText(target.path)
      showToast('已复制图片路径')
    } else {
      await navigator.clipboard.writeText(target.name ?? '')
      showToast('已复制文件名（浏览器无法获取完整本地路径）')
    }
  } catch {
    showToast('复制失败')
  }
}

async function ctxDownload() {
  closeCtxMenu()
  const target = ctxTarget.value
  if (!target) return
  try {
    // 跨域地址 download 属性不生效，用 blob 中转；no-store 绕过可能被污染的缓存
    const response = await fetch(itemOriginalUrl(target), { cache: 'no-store' })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const blob = await response.blob()
    const objUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = objUrl
    link.download = target.name ?? 'image'
    link.click()
    URL.revokeObjectURL(objUrl)
  } catch {
    showToast('下载失败，请稍后重试')
  }
}

// ---------- 开始搜索 ----------
const searchResults = ref([])
const searchLoading = ref(false)
const searchError = ref('')
let searchRequestId = 0

async function restoreGalleryFirstPage() {
  if (!galleryFolder.value) return
  galleryLoading.value = true
  galleryError.value = ''
  try {
    const images = await displayGallery(galleryFolder.value, 1)
    galleryPage.value = 1
    hasMore.value = images.length > 0
    galleryImages.value = images.map(item => ({
      name: item.name,
      path: item.path,
      url: resolveImageUrl(item.thumbnailPath),
    }))
  } catch (error) {
    galleryError.value = error instanceof Error ? error.message : String(error)
  } finally {
    galleryLoading.value = false
  }
  ensureGridScrollable()
}

async function cancelSearch() {
  searchRequestId += 1
  searchResults.value = []
  searchError.value = ''
  searchLoading.value = false
  clearQueryImage()
  await restoreGalleryFirstPage()
}

async function startSearch() {
  if (!queryImage.value?.path) {
    showToast('请选择可读取本地路径的查询图片')
    return
  }
  if (!galleryFolder.value || !galleryImages.value[0]?.path) {
    showToast('请先选择含图片的图片库目录')
    return
  }

  const payload = {
    targetImage: queryImage.value.path,
    imagePath: galleryImages.value[0].path,
    method: selectedFeatureMethod.value,
    top: searchTop.value,
  }
  const requestId = ++searchRequestId
  searchLoading.value = true
  searchError.value = ''
  searchResults.value = []
  try {
    await generateFeatures(payload)
    const results = selectedSearchMode.value === 'swift'
      ? await swiftSearchImages(payload)
      : await slowSearchImages(payload)
    if (requestId !== searchRequestId) return
    searchResults.value = results.map(item => ({
      name: item.name || item.image?.split(/[\\/]/).pop() || '图片',
      extension: item.extension || '',
      path: item.image,
      url: resolveImageUrl(item.thumbnail),
      similarity: item.similarity,
    }))
    showToast(`已找到 ${searchResults.value.length} 张相似图片`)
  } catch (error) {
    if (requestId !== searchRequestId) return
    searchError.value = error instanceof Error ? error.message : String(error)
  } finally {
    if (requestId === searchRequestId) searchLoading.value = false
  }
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
  document.removeEventListener('click', closeFeatureMenuOnOutsideClick)
  window.removeEventListener('keydown', closeFeatureMenuOnEscape)
  stopTopAudio()
  topAudio.src = ''
})

onMounted(() => {
  document.addEventListener('click', closeFeatureMenuOnOutsideClick)
  window.addEventListener('keydown', closeFeatureMenuOnEscape)
})

// ---------- 本地图库（原生目录选择 + 无限滚动分页） ----------
const galleryImages = ref([]) // [{ name, url }]
const galleryFolder = ref('') // 选中目录的绝对路径
const galleryLoading = ref(false)
const galleryError = ref('')
const galleryPage = ref(1) // 当前已加载的页码
const hasMore = ref(true) // 是否还有更多图片
const galleryLoadingMore = ref(false) // 是否正在加载下一页
const gridEl = ref(null) // 网格容器，用于判断是否已铺满可视区

// 点击「目录」：原生目录框拿绝对路径 → 上传目录给后端扫盘入库 → 请求第 1 页展示
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
    // 1. 上传目录（后端扫描生成缩略图 + 入库）
    await uploadLocalGallery(folderPath)
    // 2. 请求第 1 页数据展示
    const images = await displayGallery(folderPath, 1)
    galleryFolder.value = folderPath
    galleryPage.value = 1
    hasMore.value = images.length > 0
    galleryImages.value = images.map(item => ({
      name: item.name,
      path: item.path,
      url: resolveImageUrl(item.thumbnailPath),
    }))
  } catch (error) {
    galleryError.value = error instanceof Error ? error.message : String(error)
  } finally {
    galleryLoading.value = false
  }
  // 首屏未铺满时自动续拉，直到网格可滚动或加载完
  ensureGridScrollable()
}

// 加载下一页并追加到网格
async function loadMore() {
  if (!hasMore.value || galleryLoadingMore.value || galleryLoading.value) return
  galleryLoadingMore.value = true
  try {
    const next = await displayGallery(galleryFolder.value, galleryPage.value + 1)
    if (!next.length) {
      hasMore.value = false
    } else {
      galleryPage.value += 1
      galleryImages.value.push(...next.map(item => ({
        name: item.name,
        path: item.path,
        url: resolveImageUrl(item.thumbnailPath),
      })))
    }
  } catch (error) {
    showToast(error instanceof Error ? error.message : String(error))
  } finally {
    galleryLoadingMore.value = false
  }
}

// 若网格内容未溢出（未铺满可视区）且还有更多，则继续加载，直到铺满或加载完
async function ensureGridScrollable() {
  await nextTick()
  const el = gridEl.value
  if (!el || !hasMore.value) return
  if (el.scrollHeight <= el.clientHeight) {
    await loadMore()
    ensureGridScrollable()
  }
}

// 网格滚动到底部附近时触发加载下一页
function onGridScroll(event) {
  const el = event.target
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 100) {
    loadMore()
  }
}
</script>

<template>
  <div class="search-page">
    <header class="workspace-header">
      <div>
        <p class="workspace-header__kicker">IMAGE LAB · 01</p>
        <h1 class="workspace-header__title">图片检索工作台</h1>
      </div>
      <div class="workspace-header__meta"><span class="meta-dot"></span> LOCAL LIBRARY</div>
    </header>
    <!-- 左侧工具栏 -->
    <aside class="toolbar" :class="{ 'toolbar--collapsed': toolbarCollapsed }">
      <span v-show="!toolbarCollapsed" class="toolbar__label">工具栏</span>
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
      <div ref="featureToolEl" class="toolbar__feature-tool">
        <button
          class="toolbar__feature-button"
          :class="{ 'toolbar__feature-button--active': featureMenuOpen }"
          type="button"
          :title="`方法：${featureMethods.find(method => method.id === selectedFeatureMethod)?.name || selectedFeatureMethod.toUpperCase()}`"
          :aria-expanded="featureMenuOpen"
          aria-controls="feature-method-menu"
          @click="toggleFeatureMenu"
        >
          <svg viewBox="0 0 24 24" width="19" height="19" fill="none" aria-hidden="true">
            <circle cx="6" cy="7" r="2.2" stroke="currentColor" stroke-width="1.8" />
            <circle cx="18" cy="6" r="2.2" stroke="currentColor" stroke-width="1.8" />
            <circle cx="12" cy="18" r="2.2" stroke="currentColor" stroke-width="1.8" />
            <path d="m7.8 8.2 2.7 7M16 7.6l-2.7 8M8.1 7.1l7.7-.4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
          </svg>
          <span v-show="!toolbarCollapsed" class="toolbar__feature-text">方法</span>
        </button>
        <Transition name="feature-menu">
          <section
            v-if="featureMenuOpen"
            id="feature-method-menu"
            class="feature-menu"
            aria-label="方法"
          >
            <p class="feature-menu__title">方法</p>
            <p v-if="featureMethodsLoading" class="feature-menu__status">正在获取方法…</p>
            <p v-else-if="featureMethodsError" class="feature-menu__status feature-menu__status--error">{{ featureMethodsError }}</p>
            <p v-else-if="!featureMethods.length" class="feature-menu__status">暂未注册可用方法</p>
            <button
              v-else
              v-for="method in featureMethods"
              :key="method.id"
              class="feature-menu__option"
              :class="{ 'feature-menu__option--selected': selectedFeatureMethod === method.id }"
              type="button"
              @click="selectFeatureMethod(method)"
            >
              <span><strong>{{ method.name }}</strong><small>{{ method.description }}</small></span>
              <svg v-if="selectedFeatureMethod === method.id" viewBox="0 0 24 24" width="17" height="17" fill="none" aria-label="已选择">
                <path d="m5 12 4.2 4.2L19 6.8" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
          </section>
        </Transition>
      </div>
      <div ref="searchToolEl" class="toolbar__feature-tool">
        <button
          class="toolbar__feature-button"
          :class="{ 'toolbar__feature-button--active': searchMenuOpen }"
          type="button"
          :title="`搜索：${selectedSearchMode}`"
          :aria-expanded="searchMenuOpen"
          aria-controls="search-mode-menu"
          @click="toggleSearchMenu"
        >
          <svg viewBox="0 0 24 24" width="19" height="19" fill="none" aria-hidden="true">
            <circle cx="10.8" cy="10.8" r="5.8" stroke="currentColor" stroke-width="1.9" />
            <path d="m15.2 15.2 4.7 4.7" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" />
          </svg>
          <span v-show="!toolbarCollapsed" class="toolbar__feature-text">搜索</span>
        </button>
        <Transition name="feature-menu">
          <section
            v-if="searchMenuOpen"
            id="search-mode-menu"
            class="feature-menu"
            aria-label="搜索方式"
          >
            <p class="feature-menu__title">搜索</p>
            <button
              v-for="mode in searchModes"
              :key="mode.id"
              class="feature-menu__option"
              :class="{ 'feature-menu__option--selected': selectedSearchMode === mode.id }"
              type="button"
              @click="selectSearchMode(mode)"
            >
              <span><strong>{{ mode.name }}</strong><small>{{ mode.description }}</small></span>
              <svg v-if="selectedSearchMode === mode.id" viewBox="0 0 24 24" width="17" height="17" fill="none" aria-label="已选择">
                <path d="m5 12 4.2 4.2L19 6.8" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
          </section>
        </Transition>
      </div>
      <div class="toolbar__feature-tool">
        <button
          class="toolbar__feature-button"
          :class="{ 'toolbar__feature-button--active': boxSelectEnabled }"
          type="button"
          title="框选"
          :aria-pressed="boxSelectEnabled"
          @click="toggleBoxSelect"
        >
          <svg viewBox="0 0 24 24" width="19" height="19" fill="none" aria-hidden="true">
            <path d="M5 9V5h4M15 5h4v4M19 15v4h-4M9 19H5v-4" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span v-show="!toolbarCollapsed" class="toolbar__feature-text">框选</span>
        </button>
      </div>
    </aside>

    <!-- 主体两栏 -->
    <div class="content">
      <!-- 左：查询图片 -->
      <section class="panel-col">
        <div class="panel-heading">
          <div>
            <p class="panel-heading__eyebrow">QUERY IMAGE</p>
            <h2>从一张图片开始</h2>
          </div>
          <label class="top-control" title="设置返回结果数量">
            <span class="top-control__label">TOP</span>
            <input
              v-model.number="searchTop"
              class="top-control__range"
              type="range"
              min="0"
              max="200"
              step="1"
              :style="{ '--range-progress': `${(searchTop / 200) * 100}%` }"
              @pointerdown="startTopAudio"
              @pointerup="stopTopAudio"
              @pointercancel="stopTopAudio"
              @keydown="onTopKeyDown"
              @keyup="stopTopAudio"
              @blur="stopTopAudio"
            />
            <output class="top-control__value">{{ searchTop }}</output>
          </label>
          <span class="panel-heading__mark">✦</span>
        </div>
        <div class="card query-card">
          <template v-if="queryImage">
            <div
              ref="boxImageEl"
              class="query-image-stage"
              :class="{ 'query-image-stage--box': boxSelectEnabled, 'query-image-stage--selecting': boxSelecting }"
              @pointerdown="onBoxPointerDown"
              @pointermove="onBoxPointerMove"
              @pointerup="onBoxPointerUp"
              @pointercancel="onBoxPointerUp"
              @contextmenu="openCtxMenu"
            >
              <img class="query-card__img" :src="queryImage.url" :alt="queryImage.name" />
              <div
                v-if="boxSelection"
                class="box-selection"
                :style="{ left: `${boxSelection.left}px`, top: `${boxSelection.top}px`, width: `${boxSelection.width}px`, height: `${boxSelection.height}px` }"
              ></div>
              <span v-if="boxUploading" class="box-selection__status">正在提交…</span>
            </div>
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
            :disabled="!queryImage || searchLoading"
            @click="startSearch"
          >
            开 始 搜 索
          </button>
        </div>
      </section>

      <!-- 右：检索结果 -->
      <section class="panel-col panel-col--results">
        <div class="card result-card">
          <div v-if="searchResults.length || galleryImages.length" class="result-card__heading">
            <div>
              <p class="result-card__eyebrow">{{ searchResults.length ? 'SEARCH RESULTS' : 'COLLECTION' }}</p>
              <h2>{{ searchResults.length ? '相似图片' : '图库预览' }}</h2>
            </div>
            <div class="result-card__actions">
              <button v-if="searchResults.length || searchLoading || searchError" class="result-card__cancel" type="button" @click="cancelSearch">取 消</button>
              <span class="result-card__count">共 {{ searchResults.length || galleryImages.length }} 张</span>
            </div>
          </div>

          <!-- 加载中 -->
          <div v-if="galleryLoading || searchLoading" class="card-empty">
            <span class="spinner" aria-hidden="true"></span>
            <p>正在扫描目录…</p>
          </div>

          <!-- 出错 -->
          <div v-else-if="galleryError || searchError" class="result-error">{{ searchError || galleryError }}</div>

          <div v-else-if="searchResults.length" class="result-grid">
            <figure v-for="item in searchResults" :key="item.path" class="result-item">
              <img :src="item.url" :alt="item.name" :title="item.name" loading="lazy" @contextmenu="openGalleryMenu($event, item)" />
              <figcaption>
                <span :title="item.name">{{ item.name }}</span>
                <small>{{ item.extension }} · {{ (item.similarity * 100).toFixed(1) }}%</small>
              </figcaption>
            </figure>
          </div>

          <!-- 图库网格 -->
          <div v-else-if="galleryImages.length" ref="gridEl" class="result-grid" @scroll="onGridScroll">
            <figure v-for="item in galleryImages" :key="item.url" class="result-item">
              <img
                :src="item.url"
                :alt="item.name"
                :title="item.name"
                loading="lazy"
                @contextmenu="openGalleryMenu($event, item)"
              />
              <figcaption class="gallery-item__caption" :title="item.name"><span>{{ item.name }}</span></figcaption>
            </figure>
            <!-- 底部加载状态条 -->
            <div class="grid-footer">
              <template v-if="galleryLoadingMore">
                <span class="spinner spinner--small" aria-hidden="true"></span>
                <span>加载中…</span>
              </template>
              <span v-else-if="!hasMore">没有更多了</span>
            </div>
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
          <button class="ctx-menu__item" type="button" @click="ctxOpen">打 开</button>
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
          <img :src="zoomImage?.url" :alt="zoomImage?.name" />
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
  display: grid;
  grid-template-columns: 4.25rem minmax(0, 1fr);
  grid-template-rows: auto minmax(0, 1fr);
  gap: 0 1rem;
  height: 100vh;
  padding: 1.1rem 1.25rem 1.25rem;
  animation: fade-in 0.5s ease both;
}

.workspace-header {
  grid-column: 2;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 0 0.45rem 1rem;
  border-bottom: 1px solid rgba(216, 201, 181, 0.7);
}
.workspace-header__kicker, .panel-heading__eyebrow, .result-card__eyebrow { color: var(--color-accent-deep); font-size: 0.68rem; letter-spacing: 0.18em; }
.workspace-header__title { margin-top: 0.15rem; color: var(--color-text); font-size: clamp(1.35rem, 2.5vw, 2rem); line-height: 1.2; }
.workspace-header__meta { display: flex; align-items: center; gap: 0.45rem; padding: 0.4rem 0.75rem; border: 1px solid var(--color-border); border-radius: 999px; color: var(--color-text-muted); font-family: 'Patrick Hand', cursive; font-size: 0.8rem; letter-spacing: 0.08em; }
.meta-dot { width: 0.42rem; height: 0.42rem; border-radius: 50%; background: var(--color-success); box-shadow: 0 0 0 4px rgba(139, 201, 138, 0.15); }

.content {
  grid-column: 2;
  display: grid;
  grid-template-columns: minmax(280px, 0.85fr) minmax(0, 1.5fr);
  gap: 1.1rem;
  min-height: 0;
  min-width: 0;
  padding-top: 1.1rem;
}

.panel-col { display: flex; flex-direction: column; gap: 0.75rem; min-height: 0; min-width: 0; }
.panel-heading { display: flex; align-items: center; justify-content: space-between; min-height: 3.6rem; padding: 0 0.35rem; }
.panel-heading h2, .result-card__heading h2 { margin-top: 0.12rem; color: var(--color-text); font-size: 1.08rem; font-weight: 400; }
.panel-heading__mark { display: grid; place-items: center; width: 2rem; height: 2rem; border: 1px solid var(--color-border); border-radius: 50%; color: var(--color-accent); transform: rotate(12deg); }

.top-control {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-left: auto;
  margin-right: 0.9rem;
  min-height: 3.5rem;
  padding: 0.62rem 0.85rem;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sketchy);
  background: rgba(255, 253, 248, 0.58);
  color: var(--color-text-muted);
  cursor: pointer;
}

.top-control__label {
  color: var(--color-accent-deep);
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.top-control__range {
  width: clamp(10rem, 17vw, 16rem);
  height: 1rem;
  margin: 0;
  appearance: none;
  -webkit-appearance: none;
  background: transparent;
  accent-color: var(--color-accent);
  cursor: pointer;
}

.top-control__range::-webkit-slider-runnable-track {
  height: 0.75rem;
  border-radius: 999px;
  background: linear-gradient(
    to right,
    var(--color-accent-light) 0%,
    var(--color-accent) var(--range-progress),
    rgba(216, 201, 181, 0.75) var(--range-progress),
    rgba(216, 201, 181, 0.75) 100%
  );
}

.top-control__range::-webkit-slider-thumb {
  width: 1.8rem;
  height: 1.8rem;
  margin-top: -0.5rem;
  border: 3px solid var(--color-card);
  border-radius: 50%;
  background: var(--color-accent);
  box-shadow: 0 2px 7px rgba(74, 63, 53, 0.2);
  appearance: none;
  -webkit-appearance: none;
  box-sizing: border-box;
  transform: translateY(0);
}

.top-control__range::-moz-range-track {
  height: 0.75rem;
  border-radius: 999px;
  background: linear-gradient(
    to right,
    var(--color-accent-light) 0%,
    var(--color-accent) var(--range-progress),
    rgba(216, 201, 181, 0.75) var(--range-progress),
    rgba(216, 201, 181, 0.75) 100%
  );
}

.top-control__range::-moz-range-thumb {
  width: 1.8rem;
  height: 1.8rem;
  border: 3px solid var(--color-card);
  border-radius: 50%;
  background: var(--color-accent);
  box-shadow: 0 2px 7px rgba(74, 63, 53, 0.2);
  cursor: pointer;
}

.top-control__range:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 4px;
}

.top-control__value {
  min-width: 3.4rem;
  padding: 0.42rem 0.6rem;
  border: 2px solid var(--color-border);
  border-radius: 999px;
  background: rgba(255, 253, 248, 0.72);
  color: var(--color-accent-deep);
  font-size: 1rem;
  font-weight: 700;
  text-align: center;
}

/* ---------- 工具栏 ---------- */
.toolbar {
  position: relative;
  z-index: 30;
  grid-row: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.4rem;
  width: 4.25rem;
  padding: 1rem 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sketchy);
  background: rgba(255, 253, 248, 0.78);
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow-pixel-sm);
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
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sketchy);
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
  order: -1;
  margin: 0 0 0.25rem;
  writing-mode: vertical-rl;
  font-size: 0.8rem;
  letter-spacing: 0.5em;
  color: var(--color-text-muted);
  user-select: none;
}

.toolbar__feature-tool {
  position: relative;
  display: flex;
  justify-content: center;
  width: 100%;
}

.toolbar__feature-button {
  display: flex;
  flex-direction: column;
  place-items: center;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  width: 2.5rem;
  min-height: 2.5rem;
  padding: 0.3rem;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sketchy);
  background: var(--color-card);
  color: var(--color-text-secondary);
  transition: transform 0.2s ease, border-color 0.2s ease, color 0.2s ease, background-color 0.2s ease;
}

.toolbar__feature-button:hover,
.toolbar__feature-button--active {
  border-color: var(--color-accent-light);
  background: rgba(255, 253, 248, 0.96);
  color: var(--color-accent);
}

.toolbar__feature-button:hover { transform: translateY(-1px); }
.toolbar__feature-button:focus-visible,
.feature-menu__option:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

.toolbar__feature-text {
  font-size: 0.62rem;
  line-height: 1.1;
  white-space: nowrap;
}

.feature-menu {
  position: absolute;
  top: -0.35rem;
  left: calc(100% + 0.75rem);
  z-index: 100;
  width: 14.5rem;
  padding: 0.55rem;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sketchy);
  background: rgba(255, 253, 248, 0.97);
  box-shadow: 0 16px 38px rgba(74, 63, 53, 0.18);
  backdrop-filter: blur(10px);
}

.feature-menu__title {
  margin: 0.15rem 0.45rem 0.45rem;
  color: var(--color-text-muted);
  font-size: 0.68rem;
  letter-spacing: 0.15em;
}

.feature-menu__status {
  margin: 0;
  padding: 0.75rem;
  color: var(--color-text-muted);
  font-size: 0.78rem;
  line-height: 1.5;
}

.feature-menu__status--error { color: var(--color-danger); }

.feature-menu__option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0.7rem 0.75rem;
  border: 1px solid transparent;
  border-radius: var(--radius-sketchy);
  background: transparent;
  color: var(--color-text);
  text-align: left;
  transition: background-color 0.16s ease, border-color 0.16s ease;
}

.feature-menu__option:hover,
.feature-menu__option--selected {
  border-color: var(--color-border);
  background: rgba(227, 165, 177, 0.14);
}

.feature-menu__option strong,
.feature-menu__option small { display: block; }
.feature-menu__option strong { font-size: 0.9rem; font-weight: 600; }
.feature-menu__option small { margin-top: 0.16rem; color: var(--color-text-muted); font-size: 0.7rem; }
.feature-menu__option svg { flex: 0 0 auto; color: var(--color-accent); }

.feature-menu-enter-active,
.feature-menu-leave-active { transition: opacity 0.16s ease, transform 0.16s ease; }
.feature-menu-enter-from,
.feature-menu-leave-to { opacity: 0; transform: translateX(-0.4rem) scale(0.98); }

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
  border-radius: var(--radius-sketchy);
  background: var(--color-card);
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
  border-radius: var(--radius-sketchy);
  background: var(--color-accent);
  color: var(--color-text);
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
  border-radius: var(--radius-sketchy);
  background: rgba(74, 63, 53, 0.9);
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
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sketchy);
  background: var(--color-card);
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow-pixel-sm);
}

/* 查询图卡片：叠加淡靛蓝渐变，与结果卡形成主次 */
.query-card {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background:
    linear-gradient(165deg, rgba(227, 165, 177, 0.18) 0%, rgba(167, 189, 208, 0.1) 45%, rgba(255, 255, 255, 0) 100%),
    rgba(255, 253, 248, 0.78);
}

.query-card__img {
  display: block;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 100%;
  min-height: 0;
  border-radius: var(--radius-sketchy);
  object-fit: contain;
  box-shadow: 0 6px 20px rgba(100, 116, 139, 0.16);
}

.query-image-stage {
  position: relative;
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  max-width: 100%;
  max-height: 100%;
  overflow: hidden;
}

.query-image-stage--box { cursor: crosshair; }
.query-image-stage--selecting { user-select: none; }
.query-image-stage--box .query-card__img { pointer-events: none; }

.box-selection {
  position: absolute;
  z-index: 2;
  border: 2px solid rgba(214, 123, 145, 0.95);
  background: rgba(244, 174, 192, 0.34);
  box-shadow: 0 0 0 9999px rgba(244, 174, 192, 0.08);
  pointer-events: none;
}

.box-selection__status {
  position: absolute;
  top: 0.75rem;
  left: 50%;
  z-index: 3;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  background: rgba(74, 63, 53, 0.78);
  color: #fff;
  font-size: 0.75rem;
  transform: translateX(-50%);
  pointer-events: none;
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
  border-radius: var(--radius-sketchy);
  background: var(--color-card);
  color: var(--color-danger);
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
  background: var(--color-danger);
  color: #ffffff;
}

.query-card__remove:focus-visible {
  outline: 2px solid var(--color-danger);
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
  border-radius: var(--radius-sketchy);
  background: rgba(74, 63, 53, 0.85);
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

.result-card__heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  min-height: 2.8rem;
  margin: 0 0 0.7rem;
  padding: 0 0.2rem;
}

.result-card__actions {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.result-card__cancel {
  padding: 0.32rem 0.72rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sketchy);
  background: rgba(255, 253, 248, 0.72);
  color: var(--color-text-secondary);
  font-size: 0.76rem;
  cursor: pointer;
  transition: border-color 0.16s ease, color 0.16s ease, background-color 0.16s ease;
}

.result-card__cancel:hover {
  border-color: var(--color-danger);
  background: rgba(226, 109, 109, 0.1);
  color: var(--color-danger);
}

.result-card__cancel:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

/* 结果卡片内的空状态/加载态：撑满卡片并垂直居中 */
.result-card > .card-empty {
  flex: 1;
  justify-content: center;
}

.result-card__count {
  position: static;
  padding: 0.28rem 0.65rem;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: rgba(255, 253, 248, 0.72);
  color: var(--color-accent-deep);
  font-size: 0.7rem;
  font-weight: 600;
  backdrop-filter: blur(6px);
}

.result-grid {
  display: grid;
  flex: 1;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  grid-auto-rows: max-content;
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
  border-radius: 8px;
  background: var(--color-border);
}

.result-item {
  margin: 0;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sketchy);
  background: rgba(255, 253, 248, 0.8);
  box-shadow: 0 8px 22px rgba(132, 103, 83, 0.1);
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
  display: flex;
  flex-direction: column;
  gap: 0.14rem;
  padding: 0.45rem 0.65rem;
  color: var(--color-text-secondary);
  font-size: 0.72rem;
}

.result-item figcaption > span {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.result-item figcaption small {
  color: var(--color-accent-deep);
  font-size: 0.65rem;
}

.result-item figcaption.gallery-item__caption {
  box-sizing: border-box;
  height: calc(2 * 1.28em + 0.9rem);
  min-height: calc(2 * 1.28em + 0.9rem);
  overflow: hidden;
}

.result-item figcaption.gallery-item__caption > span {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-height: 1.28;
  white-space: normal;
  text-overflow: ellipsis;
}

/* 网格底部加载状态条 */
.grid-footer {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 0;
  color: var(--color-text-muted);
  font-size: 0.8rem;
}

/* 小号加载指示 */
.spinner--small {
  width: 1.25rem;
  height: 1.25rem;
  border-width: 2px;
}

/* 错误提示 */
.result-error {
  display: grid;
  place-items: center;
  flex: 1;
  color: var(--color-danger);
  font-size: 0.9rem;
}

/* ---------- 按钮 ---------- */
.pill-btn {
  padding: 0.8rem 2.2rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sketchy);
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
  background: var(--color-accent);
  color: var(--color-text);
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
  border-radius: var(--radius-sketchy);
  background: var(--color-card);
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
  border-radius: var(--radius-sketchy);
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
  background: var(--color-border);
  color: var(--color-accent);
}

/* ---------- 放大预览 ---------- */
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2.5rem;
  background: rgba(74, 63, 53, 0.6);
  backdrop-filter: blur(6px);
  cursor: zoom-out;
}

.lightbox img {
  display: block;
  max-width: 100%;
  max-height: 100%;
  min-width: 0;
  min-height: 0;
  border-radius: var(--radius-sketchy);
  object-fit: contain;
  box-shadow: 0 16px 50px rgba(74, 63, 53, 0.25);
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
    display: flex;
    flex-direction: column;
    height: auto;
    min-height: 100vh;
    overflow-y: auto;
  }

  .workspace-header { order: 0; padding-bottom: 0.8rem; }
  .workspace-header__meta { display: none; }
  .content { display: grid; order: 1; padding-top: 0.8rem; }

  .toolbar {
    grid-row: auto;
    flex-direction: row;
    width: auto;
    padding: 0.5rem 1rem;
  }

  .toolbar__feature-button {
    flex-direction: row;
    width: auto;
    min-height: 2.3rem;
    padding-inline: 0.65rem;
  }

  .feature-menu {
    top: calc(100% + 0.65rem);
    left: 0;
  }

  .feature-menu-enter-from,
  .feature-menu-leave-to { transform: translateY(-0.35rem) scale(0.98); }

  .toolbar__label {
    margin-top: 0;
    writing-mode: horizontal-tb;
  }

  .panel-heading {
    flex-wrap: wrap;
    row-gap: 0.45rem;
  }

  .top-control {
    order: 3;
    flex-basis: 100%;
    margin: 0;
    min-height: 3.75rem;
    padding-inline: 1rem;
  }

  .top-control__range {
    flex: 1;
    width: auto;
    height: 1.1rem;
  }

  .top-control__range::-webkit-slider-thumb {
    width: 2rem;
    height: 2rem;
    margin-top: -0.625rem;
  }

  .top-control__range::-moz-range-thumb {
    width: 2rem;
    height: 2rem;
  }

  .content {
    grid-template-columns: 1fr;
  }

  .card {
    min-height: 300px;
  }
}
</style>

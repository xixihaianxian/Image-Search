// 后端接口基础地址
export const API_BASE = 'http://127.0.0.1:8000'

/**
 * 上传本地目录到后端（后端扫盘生成缩略图并入库）
 * @param {string} folderPath 目录完整路径
 * @returns {Promise<object>} 后端响应
 */
export async function uploadLocalGallery(folderPath) {
  let response
  try {
    response = await fetch(`${API_BASE}/retrieve/upload/local/gallery`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folderPath }),
    })
  } catch {
    // fetch 抛 TypeError：后端不可达，或后端 500 等错误响应缺失 CORS 头被浏览器拦截
    throw new Error('请求未到达后端或响应被浏览器拦截（后端可能 500），请查看 Network 面板')
  }
  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') {
        detail = body.detail
      }
    } catch {
      /* 响应体不是 JSON 时忽略，使用默认提示 */
    }
    throw new Error(`上传目录失败（${detail}）`)
  }
  return await response.json()
}

/**
 * 分页获取图库图片数据
 * @param {string} folderPath 目录完整路径
 * @param {number} [page] 页码，从 1 开始
 * @returns {Promise<Array<{path:string, name:string, extension:string, thumbnailPath:string}>>}
 */
export async function displayGallery(folderPath, page = 1) {
  let response
  try {
    response = await fetch(
      `${API_BASE}/retrieve/display/gallery?folder=${encodeURIComponent(folderPath)}&page=${page}`
    )
  } catch {
    throw new Error('请求未到达后端或响应被浏览器拦截（后端可能 500），请查看 Network 面板')
  }
  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') {
        detail = body.detail
      }
    } catch {
      /* 响应体不是 JSON 时忽略，使用默认提示 */
    }
    throw new Error(`获取图库失败（${detail}）`)
  }
  const result = await response.json()
  // 兼容 data 为 JSON 字符串或数组两种情况
  const data = typeof result?.data === 'string' ? JSON.parse(result.data) : result?.data
  return Array.isArray(data) ? data : []
}

/**
 * 把后端返回的图片相对地址拼接为完整可访问地址
 * @param {string} imageUrl 后端返回的 image_url
 * @returns {string} 完整 URL
 */
export function resolveImageUrl(imageUrl) {
  return `${API_BASE}${imageUrl}`
}

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

/**
 * 获取后端已注册的特征方法列表。
 * @returns {Promise<string[]>}
 */
export async function displayModels() {
  let response
  try {
    response = await fetch(`${API_BASE}/retrieve/display/model`)
  } catch {
    throw new Error('无法连接后端，暂时不能获取方法列表')
  }
  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      /* 使用默认错误信息 */
    }
    throw new Error(`获取方法列表失败：${detail}`)
  }
  const result = await response.json()
  const data = typeof result?.data === 'string' ? JSON.parse(result.data) : result?.data
  return Array.isArray(data) ? data.filter(method => typeof method === 'string') : []
}

async function requestSearchEndpoint(path, payload, action) {
  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch {
    throw new Error(`无法连接后端，${action}未完成`)
  }
  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      /* 使用默认错误信息 */
    }
    throw new Error(`${action}失败：${detail}`)
  }
  const result = await response.json()
  return typeof result?.data === 'string' ? JSON.parse(result.data) : result?.data
}

export function generateFeatures(payload) {
  return requestSearchEndpoint('/retrieve/generate/features', payload, '生成特征')
}

export async function slowSearchImages(payload) {
  const data = await requestSearchEndpoint('/retrieve/slow/search/images', payload, '搜索图片')
  return Array.isArray(data) ? data : []
}

export async function swiftSearchImages(payload) {
  const data = await requestSearchEndpoint('/retrieve/swift/search/images', payload, '搜索图片')
  return Array.isArray(data) ? data : []
}

export async function uploadAnchorBox(formData) {
  let response
  try {
    response = await fetch(`${API_BASE}/retrieve/anchor/box/image`, {
      method: 'POST',
      body: formData,
    })
  } catch {
    throw new Error('无法连接后端，框选图片上传未完成')
  }
  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      /* 使用默认错误信息 */
    }
    throw new Error(`框选图片上传失败：${detail}`)
  }
  const result = await response.json()
  let data = result?.data
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data)
    } catch {
      return []
    }
  }
  // 兼容后端将结果再次包装为 { data: [...] } 的响应
  if (!Array.isArray(data) && Array.isArray(data?.data)) data = data.data
  return Array.isArray(data) ? data : []
}

/**
 * 登记选中的目标图片，后端返回其展示信息
 * @param {string} imagePath 选中图片的绝对路径
 * @returns {Promise<{name:string, imageUrl:string}>}
 */
export async function selectTarget(imagePath) {
  let response
  try {
    response = await fetch(
      `${API_BASE}/retrieve/select/target?image_path=${encodeURIComponent(imagePath)}`
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
    throw new Error(`获取选中图片失败（${detail}）`)
  }
  const result = await response.json()
  // 兼容 data 为 JSON 字符串或对象两种情况
  const data = typeof result?.data === 'string' ? JSON.parse(result.data) : result?.data
  return data ?? {}
}

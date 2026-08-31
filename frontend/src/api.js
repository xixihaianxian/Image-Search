// 后端接口基础地址
export const API_BASE = 'http://127.0.0.1:8000'

/**
 * 加载本地图库目录
 * @param {string} folderPath 服务器上的图片文件夹路径
 * @returns {Promise<Array<{name:string, imageUrl:string}>>} 图片信息列表
 */
export async function loadLocalGallery(folderPath) {
  let response
  try {
    response = await fetch(`${API_BASE}/retrieve/log/local/gallery`, {
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
    throw new Error(`加载图库失败（${detail}）`)
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
 * 批量上传图片文件到后端图库
 * @param {File[]} files 图片文件列表
 * @param {string} folder 目录名（后端据此存到 upload/<folder>/ 子目录）
 * @param {(progress:number)=>void} [onProgress] 上传进度回调（0~1）
 * @returns {Promise<Array<{name:string, imageUrl:string, thumbnail?:string}>>} 后端登记结果
 */
export function uploadGallery(files, folder, onProgress) {
  return new Promise((resolve, reject) => {
    const form = new FormData()
    // 后端路由签名：folder 是表单字段，images 是表单文件字段
    form.append('folder', folder)
    files.forEach(file => form.append('images', file))
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE}/retrieve/upload/gallery`)
    xhr.upload.onprogress = event => {
      if (event.lengthComputable && onProgress) {
        onProgress(event.loaded / event.total)
      }
    }
    xhr.onload = () => {
      if (xhr.status !== 200) {
        reject(new Error(`上传失败（HTTP ${xhr.status}）`))
        return
      }
      try {
        const result = JSON.parse(xhr.responseText)
        const data = typeof result?.data === 'string' ? JSON.parse(result.data) : result?.data
        resolve(Array.isArray(data) ? data : [])
      } catch {
        reject(new Error('后端响应解析失败'))
      }
    }
    xhr.onerror = () => reject(new Error('网络错误，请检查后端是否运行'))
    xhr.send(form)
  })
}

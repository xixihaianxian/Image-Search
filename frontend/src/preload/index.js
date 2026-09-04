import { contextBridge, ipcRenderer, webUtils } from 'electron'

// 通过 contextBridge 安全地暴露主进程能力给渲染进程
contextBridge.exposeInMainWorld('api', {
  // 弹出原生目录选择框，返回绝对路径；取消返回 null
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  // 拿文件选择框中文件的绝对路径（新版 Electron 移除了 File.path，必须走 webUtils）
  getPathForFile: file => webUtils.getPathForFile(file),
  // 在资源管理器中打开文件所在位置并选中（shell 在主进程通过 IPC 调用）
  showItemInFolder: path => ipcRenderer.invoke('show-item-in-folder', path),
})

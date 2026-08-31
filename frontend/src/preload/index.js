import { contextBridge, ipcRenderer } from 'electron'

// 通过 contextBridge 安全地暴露主进程能力给渲染进程
contextBridge.exposeInMainWorld('api', {
  // 弹出原生目录选择框，返回绝对路径；取消返回 null
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
})

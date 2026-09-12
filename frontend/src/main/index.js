import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron'
import { join, extname } from 'path'
import { promises as fs } from 'fs'

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  // 开发模式加载 Vite dev server，生产模式加载打包后的 renderer
  if (process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  // 原生目录选择：返回绝对路径（用户取消返回 null）
  ipcMain.handle('select-directory', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory'],
    })
    return result.canceled ? null : result.filePaths[0]
  })

  // 在资源管理器中打开文件所在位置并选中（shell 只能在主进程使用）
  ipcMain.handle('show-item-in-folder', (_event, path) => {
    shell.showItemInFolder(path)
  })

  // 通过主进程读取本地查询图，避免渲染进程 fetch 本地文件接口时受到 CORS 限制
  ipcMain.handle('read-local-image', async (_event, path) => {
    const data = await fs.readFile(path)
    const extension = extname(path).toLowerCase()
    const mimeTypes = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.bmp': 'image/bmp', '.gif': 'image/gif' }
    return { data, type: mimeTypes[extension] || 'application/octet-stream' }
  })

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

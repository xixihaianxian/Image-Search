"use strict";
const electron = require("electron");
electron.contextBridge.exposeInMainWorld("api", {
  // 弹出原生目录选择框，返回绝对路径；取消返回 null
  selectDirectory: () => electron.ipcRenderer.invoke("select-directory")
});

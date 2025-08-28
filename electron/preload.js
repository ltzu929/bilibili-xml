const { contextBridge, ipcRenderer } = require('electron');

// Securely expose a custom API to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  openExternal: (url) => {
    // 发送消息到主进程，使用系统默认浏览器打开链接
    ipcRenderer.send('open-external-link', url);
  }
});

const { contextBridge, ipcRenderer } = require('electron');

// Securely expose a custom API to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  openExternal: (url) => ipcRenderer.send('open-external-link', url)
});

const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let pyProc = null;

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  // 开发环境加载 Vite 本地服务，生产环境加载打包后的 index.html
  if (process.env.NODE_ENV === 'development') {
    win.loadURL('http://localhost:5173');
  } else {
    win.loadFile(path.join(__dirname, 'dist', 'index.html'));
  }
}

function startPythonServer() {
  // 自动启动 danmaku_server.py
  const script = path.join(__dirname, '../danmaku_server.py');
  pyProc = spawn('python', [script], {
    cwd: path.join(__dirname, '..'),
    detached: true,
    stdio: 'inherit', // 这样能看到日志
  });
  pyProc.unref();
}

app.whenReady().then(() => {
  startPythonServer();
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
}); 
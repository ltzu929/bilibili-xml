const { app, BrowserWindow, shell, ipcMain } = require('electron');
const path = require('path');
const { fork } = require('child_process');

let mainWindow;
let serverProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
        },
    });

    // Start the backend server
    const serverPath = path.join(__dirname, '..', 'server', 'index.js');
    const isDev = !app.isPackaged;
    const staticPath = isDev
        ? path.join(__dirname, '..', 'dist')
        : path.join(app.getAppPath(), '..', 'dist');

    serverProcess = fork(serverPath, [], {
        env: { ...process.env, STATIC_PATH: staticPath }
    });

    serverProcess.on('message', (message) => {
        console.log(`Message from server: ${message}`);
    });

    // Load the local URL served by our Express app
    // We give it a small delay to ensure the server starts up
    setTimeout(() => {
         mainWindow.loadURL('http://localhost:3001');
    }, 2000);

    // Open DevTools for debugging, can be removed for production
    // mainWindow.webContents.openDevTools();

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.on('ready', createWindow);

// Handle the 'open-external-link' event from the renderer process
ipcMain.on('open-external-link', (event, url) => {
    shell.openExternal(url);
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    // Ensure the server process is killed when the app quits
    if (serverProcess) {
        console.log('Killing server process...');
        serverProcess.kill();
        serverProcess = null;
    }
});


app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

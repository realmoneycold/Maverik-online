import { app, BrowserWindow } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Determine if we are running in development mode
const isDev = process.env.NODE_ENV === 'development';

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    backgroundColor: '#000000',
    icon: path.join(__dirname, '../build/icon.png'),
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    // Customize window style for a personal assistant feel
    autoHideMenuBar: true,
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#000000',
      symbolColor: '#ffffff'
    }
  });

  if (isDev) {
    // In development, load the Vite dev server URL
    mainWindow.loadURL('http://localhost:5173');
    // Open Developer Tools automatically
    mainWindow.webContents.openDevTools();
  } else {
    // In production, load the built HTML file
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

import { app, BrowserWindow, session, protocol } from 'electron';
import path from 'path';
import { fileURLToPath, URL } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Set the application name to "Maverik" so it shows up in taskbar correctly
app.setName('Maverik');

// Register app:// protocol as secure to bypass Chrome file:// media limits
protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { secure: true, standard: true, supportFetchAPI: true } }
]);

// Single instance lock prevents multiple windows
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  // Determine if we are running in development mode
  const isDev = process.env.NODE_ENV === 'development';

  let mainWindow;

  function createWindow() {
    mainWindow = new BrowserWindow({
      title: 'Maverik',
      width: 1200,
      height: 800,
      backgroundColor: '#000000',
      icon: 'C:/Users/mon1ycold/Documents/Maverik/imgs/logo.png',
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false,
        webSecurity: false
      },
      autoHideMenuBar: true,
      titleBarStyle: 'hidden',
      titleBarOverlay: {
        color: '#000000',
        symbolColor: '#ffffff'
      }
    });

    // Auto-allow all permissions (Microphone, etc.)
    mainWindow.webContents.session.setPermissionRequestHandler((webContents, permission, callback) => {
      callback(true);
    });
    mainWindow.webContents.session.setPermissionCheckHandler((webContents, permission) => {
      return true;
    });

    if (isDev) {
      mainWindow.loadURL('http://localhost:5173');
    } else {
      // Use app://-/ so that '-' is the hostname and absolute paths resolve correctly.
      mainWindow.loadURL('app://-/index.html');
      mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
      mainWindow = null;
    });
  }

  app.on('second-instance', (event, commandLine, workingDirectory) => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(() => {
    // Intercept app:// requests and serve local files securely with proper MIME types
    protocol.handle('app', (request) => {
      const urlObj = new URL(request.url);
      let reqPath = decodeURIComponent(urlObj.pathname);
      if (reqPath === '/') reqPath = '/index.html';
      
      const filePath = path.join(__dirname, '../dist', reqPath);
      
      let ext = path.extname(filePath).toLowerCase();
      let mimeType = 'text/plain';
      if (ext === '.html') mimeType = 'text/html';
      else if (ext === '.js' || ext === '.mjs') mimeType = 'text/javascript';
      else if (ext === '.css') mimeType = 'text/css';
      else if (ext === '.json') mimeType = 'application/json';
      else if (ext === '.png') mimeType = 'image/png';
      else if (ext === '.jpg' || ext === '.jpeg') mimeType = 'image/jpeg';
      else if (ext === '.svg') mimeType = 'image/svg+xml';
      
      try {
        const data = fs.readFileSync(filePath);
        return new Response(data, {
          headers: { 'Content-Type': mimeType }
        });
      } catch (e) {
        return new Response('Not Found', { status: 404 });
      }
    });

    createWindow();
  });

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
}

const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { execFile } = require('child_process');

function createWindow() {
  const win = new BrowserWindow({
    width: 1000,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  });

  win.loadFile('renderer/index.html');
}

function getParserPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, 'parser', 'parser.py')
    : path.join(__dirname, 'parser', 'parser.py');
}

ipcMain.handle('select-csv', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    filters: [{ name: 'CSV Files', extensions: ['csv'] }],
    properties: ['openFile']
  });
  return canceled ? null : filePaths[0];
});

ipcMain.handle('parse-csv', async (_, filePath) => {
  return new Promise((resolve, reject) => {
    const parserPath = getParserPath();
    execFile('python', [parserPath, filePath], (error, stdout, stderr) => {
      if (error) {
        reject(stderr || error.message);
      } else {
        resolve(stdout);
      }
    });
  });
});

app.whenReady().then(() => {
  createWindow();
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

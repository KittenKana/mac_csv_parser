const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  selectCSV: () => ipcRenderer.invoke('select-csv'),
  parseCSV: (filePath) => ipcRenderer.invoke('parse-csv', filePath)
});

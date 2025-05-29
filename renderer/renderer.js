document.getElementById('select-file').addEventListener('click', async () => {
  const filePath = await window.electronAPI.selectCSV();
  if (filePath) {
    try {
      const result = await window.electronAPI.parseCSV(filePath);
      document.getElementById('output').textContent = result;
    } catch (error) {
      document.getElementById('output').textContent = `Error: ${error}`;
    }
  }
});

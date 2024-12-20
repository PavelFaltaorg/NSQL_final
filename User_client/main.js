const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')

function createWindow () {
  const win = new BrowserWindow({
    width: 1280,
    height: 720,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  })
  win.loadFile('index.html')
}


app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})


// Listen for messages from the renderer
ipcMain.on('start-game', (event, session_id) => {
  const command = `python3 start_game.py "${session_id}"`;
  const { exec } = require('child_process');

    exec(command, (error, stdout, stderr) => {
        if (error) {
        console.error(`exec error: ${error}`);
        return;
        }
        console.log(`stdout: ${stdout}`);
        console.error(`stderr: ${stderr}`);
    });
});

ipcMain.on('message', (event, message) => {
    console.log('Recieved message:', message);
});





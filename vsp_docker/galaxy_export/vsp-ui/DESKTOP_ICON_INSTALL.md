# Installing the VSP Pipeline Desktop Icon

This guide shows you how to install a desktop icon that launches the VSP Pipeline UI with a single click.

## What the Desktop Icon Does

When you click the VSP Pipeline desktop icon, it will:

1. Start the VSP Pipeline UI server (or detect if already running)
2. Automatically open your web browser to the UI (`http://127.0.0.1:8765`)
3. Open the input folder (`~/vsp_input/`) in your file manager

This makes it easy to start working without remembering terminal commands!

## Installation Steps

### Option 1: Desktop Icon (Recommended)

Install an icon on your desktop for quick access:

```bash
cd /workspace/vsp-ui
chmod +x vsp-pipeline.desktop
cp vsp-pipeline.desktop ~/Desktop/
```

After copying, you may need to:

1. Right-click the icon on your desktop
2. Select "Allow Launching" or "Trust" (depends on your desktop environment)
3. Double-click to launch

### Option 2: Applications Menu

Install to your system applications menu:

```bash
cd /workspace/vsp-ui
chmod +x vsp-pipeline.desktop
mkdir -p ~/.local/share/applications
cp vsp-pipeline.desktop ~/.local/share/applications/
```

The VSP Pipeline will appear in your applications menu under "Audio & Video" or "Video".

### Option 3: Both Locations

For maximum convenience, install to both desktop and applications menu:

```bash
cd /workspace/vsp-ui
chmod +x vsp-pipeline.desktop
cp vsp-pipeline.desktop ~/Desktop/
mkdir -p ~/.local/share/applications
cp vsp-pipeline.desktop ~/.local/share/applications/
```

## Using the Desktop Icon

### First Time Launch

1. Double-click the VSP Pipeline icon
2. Your browser will open to the UI
3. The input folder will open in your file manager
4. Drag video files into the input folder
5. Use the web UI to process them

### Subsequent Launches

If the server is already running:

- The icon will detect this
- It will just open the browser and input folder
- No duplicate servers will be started

### Stopping the Server

To stop the VSP Pipeline server:

```bash
/workspace/vsp-ui/launcher.sh stop
```

Or check server status:

```bash
/workspace/vsp-ui/launcher.sh status
```

## Troubleshooting

### Desktop Icon Won't Launch

1. Make sure the desktop file is executable:
   ```bash
   chmod +x ~/Desktop/vsp-pipeline.desktop
   ```

2. Try right-clicking and selecting "Allow Launching" or "Trust"

3. Check that the launcher script is executable:
   ```bash
   chmod +x /workspace/vsp-ui/launcher.sh
   ```

### Browser Doesn't Open Automatically

The launcher script tries several browsers in order:
- xdg-open (default)
- Firefox
- Chromium
- Google Chrome

If none are found, the terminal will show the URL to open manually: `http://127.0.0.1:8765`

### File Manager Doesn't Open

The launcher tries several file managers:
- xdg-open (default)
- Nautilus (GNOME)
- Nemo (Cinnamon)
- Thunar (XFCE)
- Dolphin (KDE)
- PCManFM (LXDE)

If none are found, the terminal will show the folder path: `~/vsp_input/`

You can manually open this folder or add videos via the terminal.

### Server Won't Start

Check the log file for errors:

```bash
cat ~/.vsp-ui.log
```

Common issues:
- Port 8765 already in use (restart your computer or kill the process)
- Python dependencies missing (re-run install.sh)
- Permission issues (check file permissions)

## Manual Launch (Without Desktop Icon)

If you prefer to launch from the terminal:

```bash
/workspace/vsp-ui/launcher.sh
```

Commands:
- `launcher.sh` - Start server and open browser (default)
- `launcher.sh stop` - Stop the server
- `launcher.sh restart` - Restart the server
- `launcher.sh status` - Check if server is running

## Uninstalling the Desktop Icon

To remove the desktop icon:

```bash
rm ~/Desktop/vsp-pipeline.desktop
rm ~/.local/share/applications/vsp-pipeline.desktop
```

This only removes the icon - the VSP Pipeline software itself remains installed.

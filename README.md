# HomeBridge StreamController Plugin

A StreamController plugin that enables control of smart home devices through Homebridge from your Stream Deck.

## Features

- **Toggle Lights**: Turn lights on and off with a single button press
- **Auto-Discovery**: Automatically discovers all controllable devices (lights, switches, dimmers, outlets) from your Homebridge instance
- **Smart Device Support**: Works with Lightbulbs, Switches, Outlets, Dimmers, and other controllable HomeKit devices
- **Easy Configuration**: Simple UI to configure Homebridge connection with automatic light discovery
- **Dynamic Refresh**: Refresh your device list without restarting StreamController
- **Token Management**: Automatic authentication token management with refresh

## Installation

1. Clone this repository into your StreamController plugins folder:
   ```
   ~/.var/app/com.github.streamcontroller/data/plugins/
   ```
2. Restart StreamController
3. The HomeBridge Controller plugin should appear in your available plugins

## Configuration

### Basic Setup

1. In StreamController, add a **ToggleLight** action to your deck
2. Configure your Homebridge server:
   - **Homebridge Host**: The URL of your Homebridge server (e.g., `http://localhost:8581` or `http://192.168.1.100:8581`)
   - **Username**: Your Homebridge username (default: `admin`)
   - **Password**: Your Homebridge password
3. Click **Refresh Lights** to discover your devices
4. Select the light/device you want to control from the dropdown
5. That's it! Your button is now ready to use

### Finding Your Homebridge Server

- **Local Network**: Find your Homebridge IP address (usually printed in the console when Homebridge starts)
- **Port**: The default Homebridge REST API port is `8581`
- **Example URLs**:
  - `http://localhost:8581` (same machine)
  - `http://192.168.1.100:8581` (different machine on same network)

## Requirements

- Python 3.8+
- StreamController 1.5.0 or later
- Homebridge server running and accessible
- `requests` library (installed automatically)

## Supported Devices

This plugin supports any HomeKit-compatible device that exposes an "On" characteristic, including:

- **Lightbulbs**: Standard lights, smart bulbs, RGB lights
- **Switches**: Smart switches, outlets
- **Dimmers**: Lights with adjustable brightness
- **Other devices**: Any controllable device with power control

Device discovery is automatic - the plugin will find all controllable devices in your Homebridge instance.

## Actions

### Toggle Light
Toggles a light between on and off states. The button displays a light icon showing the current state (on/off).

## Troubleshooting

### Connection Issues

**"Failed to connect to Homebridge"**
- Verify your Homebridge server is running
- Check that the host URL is correct and accessible from your machine
- Ensure username and password are correct
- Check firewall/network settings if connecting remotely

**"Connected but could not retrieve accessories"**
- Make sure you have HomeKit devices/bridges added to your Homebridge instance
- Check your Homebridge logs for any errors
- Try restarting Homebridge

### Refresh Issues

- **Button doesn't respond**: Ensure Homebridge connection is configured properly
- **No lights found**: Verify your Homebridge instance has controllable devices set up
- **Stale device list**: Click "Refresh Lights" button in the action configuration

### Toggle Not Working

1. Verify the device is actually connected and controllable in Homebridge
2. Try toggling the device in the Homebridge web UI to confirm it works
3. Check that your user account has permission to control the device
4. Restart the StreamController action

## Architecture

- **`backend/homebridge_client.py`**: REST API client for Homebridge communication
- **`actions/ToggleLight/`**: Stream Deck button action for toggling lights
- **`manifest.json`**: Plugin metadata

## License

GNU General Public License v3.0 - See LICENSE file for details

## Credits

- **StreamController**: [GitHub](https://github.com/StreamController/StreamController)
- **Homebridge**: [GitHub](https://github.com/homebridge/homebridge) - The HomeKit API server implementation
- **Homebridge REST API Documentation**: [NPM Package](https://www.npmjs.com/package/homebridge)
- **Official Homebridge Stream Deck Plugin**: [sergey-tihon/streamdeck-homebridge](https://github.com/sergey-tihon/streamdeck-homebridge) - Inspiring the design and API integration pattern
- **GNOME/GTK**: [GTK Documentation](https://www.gtk.org/) - Used for the UI framework via Adwaita

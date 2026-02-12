# Quick Start Guide - HomeBridge StreamController Plugin

## Prerequisites

Before you start, make sure you have:
1. **StreamController** installed on Linux
2. **Homebridge** running and accessible from your machine  
   (Find the IP address from Homebridge startup logs, usually on port 8581)
3. Smart lights configured in Homebridge
4. Your Homebridge username and password (default username is often `admin`)

## Installation

1. **Clone the plugin into your plugins folder:**
   ```bash
   cd ~/.var/app/com.github.streamcontroller/data/plugins/
   git clone https://github.com/ethanb/HomeBridge-StreamController com_ethanbanker_homebridge
   ```

2. **Install Python dependencies:**
   ```bash
   cd com_ethanbanker_homebridge
   pip install -r requirements.txt
   ```

3. **Restart StreamController**

## Setting Up Toggle Light Action

1. **Open StreamController** and select your deck
2. **Click on a button** to add an action
3. **Find "HomeBridge Controller"** plugin in the plugin list
4. **Select "Toggle Light"** action
5. **Configure the action:**
   - **Homebridge Host**: `http://localhost:8581` (local)  
     OR `http://192.168.X.X:8581` (remote machine's IP from Homebridge logs)
   - **Username**: Your Homebridge username (default: `admin`)
   - **Password**: Your Homebridge password
6. **Click "Refresh Lights"** to discover your devices
7. **Select the light** you want to control from the dropdown
8. **Done!** Now you can toggle your light by pressing the button

## Finding Your Homebridge Server

### Local Machine
```
http://localhost:8581
```

### Remote Machine
1. Start Homebridge on the remote machine
2. Look in the console/logs for the IP address (usually `192.168.X.X`)
3. Use `http://192.168.X.X:8581` in the plugin configuration

### Test Your Connection
- Click the action settings "Connect" button to test
- Should show success message and light count

## Troubleshooting

### Connection Failed
- Check that Homebridge is running: `ps aux | grep homebridge`
- Verify firewall allows port 8581
- Check username/password are correct
- Try connecting to `http://localhost:8581` from your browser first

### No Lights Found
- Make sure you have HomeKit devices/bridges in Homebridge
- Verify devices are controllable (not just viewable)
- Check Homebridge logs for any errors
- Click "Refresh Lights" again

### Light Doesn't Toggle
- Verify the device toggles in the Homebridge web UI
- Check you have permission to control the device
- Restart the action and try again1. **Same as above, but select "Brightness Control"** action
2. **Configure:**
   - **Homebridge Host**: Your Homebridge URL
   - **Homebridge PIN**: Your PIN
   - **Light UUID**: Your light's UUID
   - **Brightness Increment**: How much to increase on each press (1-50%)
3. **Test Connection** to verify
4. **Done!** Each press will increase brightness by the increment you set

## Tips

- **Testing Locally**: If you have no Stream Deck, enable "FakeDecks" in StreamController's Developer Settings to test
- **Finding PIN**: Look at the terminal output when Homebridge starts - it shows your PIN
- **Default Homebridge Host**: If running on the same machine, use `http://localhost:8581`
- **Remote Access**: Use your Homebridge public URL if controlling from another machine
- **Multiple Lights**: Each button can control a different light - just use different UUIDs

## Troubleshooting

### "Connection Failed" Error
- Verify Homebridge is running
- Check that the host URL is correct (include port)
- Verify the PIN format is correct (XXX-XX-XXX)
- Check your firewall settings

### Light doesn't respond
- Make sure the UUID is correct (copy-paste from Homebridge web UI)
- Verify the light is online in Homebridge
- Check Homebridge logs for errors

### Plugin not appearing
- Ensure you've installed dependencies: `pip install requests`
- Restart StreamController completely
- Check that the plugin folder is in `~/.streamcontroller/plugins/`

## Support

For issues or feature requests, visit: https://github.com/ethanb/HomeBridge-StreamController

## What's Supported

This plugin works with any smart light that:
- Is compatible with Homebridge
- Uses standard HomeKit light accessories
- Supports the "On" characteristic (and optionally Brightness)

Common devices:
- Philips Hue lights
- LIFX lights
- Nanoleaf panels
- Most Wi-Fi smart lights

Let's automate your smart home! 🏠💡

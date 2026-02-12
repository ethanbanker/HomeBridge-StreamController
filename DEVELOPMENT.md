# HomeBridge StreamController Plugin - Development Guide

## Project Structure

```
HomeBridge-StreamController/
├── main.py                          # Plugin entry point and registration
├── manifest.json                    # Plugin metadata
├── attribution.json                 # Attribution and licensing info
├── requirements.txt                 # Python dependencies
├── README.md                        # User documentation
├── actions/
│   ├── ToggleLight/                # Toggle Light action
│   │   ├── ToggleLight.py          # Action implementation
│   │   └── __init__.py
│   └── __init__.py
├── backend/
│   ├── __init__.py                 # Package initialization
│   ├── homebridge_client.py        # Homebridge API client
│   └── config_helper.py            # Configuration utilities
└── assets/
    ├── light-on.png                # Light on icon (TODO: add)
    ├── light-off.png               # Light off icon (TODO: add)
    └── thumbnail.png               # Plugin thumbnail (TODO: add)
```

## Components

### Actions

#### ToggleLight
- Toggles a light between on and off states
- Displays current state visually
- Configuration: Homebridge host, username, password, light unique ID

**Features:**
- Reads current light state from Homebridge
- Updates display based on actual state
- Includes connection test
- Thread-safe operation
- Uses Homebridge API with username/password authentication

### Backend Modules

#### homebridge_client.py
Provides HTTP API client for Homebridge communication following the official Homebridge API pattern:

**Main Methods:**
- `authenticate()` - Get access token via `/api/auth/login`
- `test_connection()` - Verify server connectivity
- `get_accessories()` - List all accessories via `/api/accessories`
- `toggle_light(accessory_id)` - Toggle light on/off via `PUT /api/accessories/{uniqueId}`
- `set_characteristic(accessory_id, characteristic_type, value)` - Set any characteristic

**Authentication:**
Uses POST `/api/auth/login` with username/password to obtain Bearer token for authenticated requests.

#### config_helper.py
Provides configuration utilities:

**Classes:**
- `HomebridgeConfigHelper` - Manages connection settings and device discovery
- `AccessoryListModel` - Model for displaying available accessories

**Key Features:**
- Asynchronous accessory discovery
- Light-only filtering
- Credential management
- Connection testing

## Next Steps & TODO Items

### For Basic Functionality
- [x] Create plugin structure
- [x] Implement ToggleLight action
- [x] Create Homebridge API client
- [x] Add configuration UI
- [x] Remove BrightnessControl action (simplified)
- [ ] Create icon assets (PNG files for light-on, light-off, thumbnail)
- [ ] Test with live Homebridge installation

### For Future Enhancements
1. **Additional Actions**
   - Brightness control action
   - ColorTemperature action for adjusting color temperature
   - Hue/Saturation color picker for RGB lights
   - Multi-light toggle (toggle multiple lights at once)
   - Scene selector (activate Homebridge scenes)


2. **Advanced Features**
   - Status ticker showing real-time light status
   - Accessory discovery and selection UI within plugin
   - Automatic status polling to update button displays
   - Support for other accessory types (switches, thermostats, etc.)
   - Fade effects for brightness transitions

3. **Configuration Improvements**
   - GUI-based accessory selector instead of manual UUID entry
   - Homebridge server auto-discovery
   - Pin validation
   - Connection status indicator

4. **Performance**
   - Implement request caching
   - Async/await for non-blocking API calls
   - Error recovery and reconnection logic
   - Request rate limiting

## Installation for Development

1. Clone repository into StreamController plugins folder:
   ```bash
   git clone https://github.com/ethanb/HomeBridge-StreamController ~/.streamcontroller/plugins/
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Restart StreamController

4. Enable FakeDecks in settings for testing without Stream Deck hardware

## Testing

### Connection Testing
1. Add an action to your deck
2. Configure Homebridge host, username, and password
3. Click "Refresh Lights" button
4. Select a light from the dropdown
5. Press the button to toggle and verify light changes

### Manual Testing Steps
1. Create ToggleLight action
2. Set Homebridge host to `http://localhost:8581`
3. Enter your Homebridge username and password
4. Click "Refresh Lights" to discover devices
5. Select a light from the dropdown
6. Press button and verify light toggles
7. Check that display updates correctly

## API Endpoints Used

The plugin communicates with Homebridge's REST API using username/password authentication:

**Authentication:**
```
POST /api/auth/login
  Request: {"username": "admin", "password": "..."}
  Response: {"access_token": "...", "expires_in": 3600}
```

**Device Operations:**
```
GET /api/accessories                                    # List all accessories
GET /api/accessories/{uniqueId}                         # Get specific accessory details
PUT /api/accessories/{uniqueId}                         # Toggle or control device
  Request: {"characteristicType": "On", "value": 1}
```

All requests use Bearer token authentication in the Authorization header.
Tokens are automatically refreshed when expired (10-minute buffer).

## Troubleshooting Development

### Import Errors
If you see import errors related to backend modules:
- Verify `__init__.py` files exist in all package directories
- Check that sys.path is correctly configured in action files

### Connection Issues
- Verify Homebridge is running
- Check that the URL is accessible (no https:// required for local)
- Verify username and password are correct (default username is `admin`)
- Check firewall settings if connecting to remote machine

### Changes Not Loading
- Restart StreamController completely
- Clear any .pyc cache files
- Check logs in terminal for error messages

## Code Style Guidelines

Following StreamController conventions:
- Use descriptive variable names
- Document all public methods with docstrings
- Use type hints where possible
- Thread-sensitive operations in separate threads
- Always handle exceptions gracefully
- Use logging for debug information

## References

- [StreamController Plugin Development Docs](https://streamcontroller.core447.com/streamcontroller/docs/latest/plugin_dev/intro/)
- [Homebridge API Documentation](https://github.com/homebridge/homebridge/blob/master/README.md)
- [Official StreamDeck Homebridge Plugin](https://github.com/sergey-tihon/streamdeck-homebridge)
- [ActionBase Documentation](https://streamcontroller.core447.com/streamcontroller/docs/latest/plugin_dev/bases/ActionBase_py/)

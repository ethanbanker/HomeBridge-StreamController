# Import StreamController modules
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

# Import python modules
import os
import json
import threading
from typing import Optional
import sys

# Add parent directory to path for imports
plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, plugin_dir)

from backend.homebridge_client import HomebridgeClient


class BrightnessControl(ActionBase):
    HAS_CONFIGURATION = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.homebridge_client = None
        self.light_accessory = None
        self.brightness = 50
        self.increment = 10
        
    def on_ready(self) -> None:
        """Initialize the action when the plugin is ready"""
        # Load settings
        settings = self.get_settings()
        
        if settings:
            self.increment = settings.get("increment", 10)
            self.brightness = settings.get("initial_brightness", 50)
        
        # Set default icon
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "brightness.png")
        if os.path.exists(icon_path):
            self.set_media(media_path=icon_path, size=0.75)
        else:
            self.set_label(text="Brightness", position="center")
        
        # Initialize Homebridge connection if configured
        if settings and "accessory_uuid" in settings:
            self.initialize_homebridge_connection()
            self._update_state_from_homebridge()
    
    def on_key_down(self) -> None:
        """Increase brightness when key is pressed"""
        if not self.homebridge_client:
            self.show_error(duration=2)
            return
        
        # Run in separate thread to avoid blocking
        threading.Thread(target=self._increase_brightness, daemon=True).start()
    
    def on_key_up(self) -> None:
        """Optional: handle key release"""
        pass
    
    def _increase_brightness(self) -> None:
        """Increase the brightness"""
        try:
            settings = self.get_settings()
            if not settings or not self.homebridge_client:
                return
            
            accessory_uuid = settings.get("accessory_uuid")
            if not accessory_uuid:
                return
            
            # Get current brightness
            status = self.homebridge_client.get_light_status(accessory_uuid)
            if status and "brightness" in status:
                current_brightness = status["brightness"]
            else:
                current_brightness = self.brightness
            
            # Increase brightness
            self.brightness = min(100, current_brightness + self.increment)
            
            # Set brightness via Homebridge
            success = self.homebridge_client.set_brightness(accessory_uuid, self.brightness)
            
            if success:
                self._update_display()
            else:
                self.show_error(duration=3)
            
        except Exception as e:
            print(f"Error increasing brightness: {e}")
            self.show_error(duration=3)
    
    def _update_state_from_homebridge(self) -> None:
        """Update display based on current light state from Homebridge"""
        try:
            settings = self.get_settings()
            if not settings or not self.homebridge_client:
                return
            
            accessory_uuid = settings.get("accessory_uuid")
            if not accessory_uuid:
                return
            
            # Get current state from Homebridge
            status = self.homebridge_client.get_light_status(accessory_uuid)
            
            if status and "brightness" in status:
                self.brightness = status["brightness"]
                self._update_display()
        
        except Exception as e:
            print(f"Error updating state from Homebridge: {e}")
    
    def _update_display(self) -> None:
        """Update the display with current brightness"""
        assets_dir = os.path.join(self.plugin_base.PATH, "assets")
        icon_path = os.path.join(assets_dir, "brightness.png")
        
        if os.path.exists(icon_path):
            self.set_media(media_path=icon_path, size=0.75)
        
        self.set_bottom_label(text=f"{self.brightness}%")
    
    def initialize_homebridge_connection(self) -> None:
        """Initialize connection to Homebridge"""
        settings = self.get_settings()
        if not settings:
            return
        
        try:
            host = settings.get("homebridge_host", "http://localhost:8581")
            pin = settings.get("homebridge_pin")
            
            self.homebridge_client = HomebridgeClient(host, pin)
            
            # Test connection
            if not self.homebridge_client.test_connection():
                print("Failed to connect to Homebridge server")
                self.homebridge_client = None
        
        except Exception as e:
            print(f"Error initializing Homebridge connection: {e}")
            self.homebridge_client = None
    
    def get_config_rows(self):
        """Return configuration rows for the action"""
        settings = self.get_settings()
        
        preferences_group = Adw.PreferencesGroup()
        
        # Homebridge Server Configuration
        server_group = Adw.PreferencesGroup()
        server_group.set_title("Homebridge Server")
        server_group.set_description("Configure your Homebridge server connection")
        
        # Host/URL
        host_row = Adw.EntryRow()
        host_row.set_title("Homebridge Host")
        if settings and "homebridge_host" in settings:
            host_row.set_text(settings["homebridge_host"])
        else:
            host_row.set_text("http://localhost:8581")
        host_row.connect("notify::text", self._on_host_changed)
        server_group.add(host_row)
        
        # PIN
        pin_row = Adw.PasswordEntryRow()
        pin_row.set_title("Homebridge PIN")
        if settings and "homebridge_pin" in settings:
            pin_row.set_text(settings["homebridge_pin"])
        else:
            pin_row.set_text("000-00-000")
        pin_row.connect("notify::text", self._on_pin_changed)
        server_group.add(pin_row)
        
        preferences_group.add(server_group)
        
        # Light Configuration
        light_group = Adw.PreferencesGroup()
        light_group.set_title("Light Selection")
        light_group.set_description("Select the light to control")
        
        # Accessory UUID
        accessory_row = Adw.EntryRow()
        accessory_row.set_title("Light UUID")
        if settings and "accessory_uuid" in settings:
            accessory_row.set_text(settings["accessory_uuid"])
        else:
            accessory_row.set_text("Enter or select light UUID")
        accessory_row.connect("notify::text", self._on_accessory_changed)
        light_group.add(accessory_row)
        
        # Connection test button
        button = Gtk.Button(label="Test Connection")
        button.connect("clicked", self._on_test_connection)
        button_row = Adw.ActionRow()
        button_row.set_title("Connection")
        button_row.add_suffix(button)
        light_group.add(button_row)
        
        preferences_group.add(light_group)
        
        # Brightness Control Settings
        control_group = Adw.PreferencesGroup()
        control_group.set_title("Control Settings")
        control_group.set_description("Configure brightness control behavior")
        
        # Increment
        increment_adj = Gtk.Adjustment(
            value=settings.get("increment", 10) if settings else 10,
            lower=1,
            upper=50,
            step_increment=1,
            page_increment=5
        )
        increment_spin = Gtk.SpinButton(adjustment=increment_adj, climb_rate=0.0)
        increment_spin.set_digits(0)
        
        increment_row = Adw.ActionRow()
        increment_row.set_title("Brightness Increment")
        increment_row.set_subtitle("% to increase per press")
        increment_row.add_suffix(increment_spin)
        increment_spin.connect("notify::value", self._on_increment_changed)
        control_group.add(increment_row)
        
        preferences_group.add(control_group)
        
        return [preferences_group]
    
    def _on_host_changed(self, widget, param) -> None:
        """Handle host change"""
        settings = self.get_settings() or {}
        settings["homebridge_host"] = widget.get_text()
        self.set_settings(settings)
        self.homebridge_client = None  # Reset connection
    
    def _on_pin_changed(self, widget, param) -> None:
        """Handle PIN change"""
        settings = self.get_settings() or {}
        settings["homebridge_pin"] = widget.get_text()
        self.set_settings(settings)
        self.homebridge_client = None  # Reset connection
    
    def _on_accessory_changed(self, widget, param) -> None:
        """Handle accessory change"""
        settings = self.get_settings() or {}
        settings["accessory_uuid"] = widget.get_text()
        self.set_settings(settings)
    
    def _on_increment_changed(self, widget, param) -> None:
        """Handle increment change"""
        settings = self.get_settings() or {}
        self.increment = int(widget.get_value())
        settings["increment"] = self.increment
        self.set_settings(settings)
    
    def _on_test_connection(self, button) -> None:
        """Test connection to Homebridge"""
        settings = self.get_settings()
        if not settings:
            self.show_error(duration=2)
            return
        
        # Reset and reinitialize connection
        self.homebridge_client = None
        self.initialize_homebridge_connection()
        
        if self.homebridge_client:
            # Try to get accessories
            accessories = self.homebridge_client.get_accessories()
            if accessories:
                print("Successfully connected to Homebridge")
            else:
                print("Connected but could not retrieve accessories")
        else:
            print("Failed to connect to Homebridge")


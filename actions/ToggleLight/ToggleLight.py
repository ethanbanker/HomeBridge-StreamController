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
import asyncio
from typing import Optional
import sys

# Add parent directory to path for imports
plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, plugin_dir)

from backend.homebridge_client import HomebridgeClient


class ToggleLight(ActionBase):
    HAS_CONFIGURATION = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.homebridge_client = None
        self.is_on = False
        
    def on_ready(self) -> None:
        """Initialize the action when the plugin is ready"""
        # Load settings
        settings = self.get_settings()
        
        # Set default icon
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "light-off.png")
        if os.path.exists(icon_path):
            self.set_media(media_path=icon_path, size=0.75)
        else:
            self.set_label(text="", position="center")
        
        # Initialize Homebridge connection if configured
        if settings and "accessory_uuid" in settings:
            self.initialize_homebridge_connection()
            # Update display with current state
            self._update_state_from_homebridge()
    
    def on_key_down(self) -> None:
        """Toggle the light when the key is pressed"""
        settings = self.get_settings()
        
        # Check if we have required configuration
        if not settings or "accessory_uuid" not in settings:
            self.show_error(duration=2)
            return
        
        # Ensure client is initialized
        if not self.homebridge_client:
            self.initialize_homebridge_connection()
        
        if not self.homebridge_client:
            self.show_error(duration=2)
            return
        
        # Run in separate thread to avoid blocking
        threading.Thread(target=self._toggle_light, daemon=True).start()
    
    def _toggle_light(self) -> None:
        """Toggle the light state"""
        try:
            settings = self.get_settings()
            if not settings:
                return
            
            accessory_uuid = settings.get("accessory_uuid")
            if not accessory_uuid or not self.homebridge_client:
                return
            
            # Toggle the light using the Homebridge client
            success = self.homebridge_client.toggle_light(accessory_uuid)
            
            if success:
                # Get updated state
                self._update_state_from_homebridge()
            else:
                self.show_error(duration=3)
            
        except Exception as e:
            logger.error(f"Error toggling light: {e}", exc_info=True)
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
            
            if status and "on" in status:
                self.is_on = status["on"]
                self._update_display()
        
        except Exception as e:
            logger.error(f"Error updating state from Homebridge: {e}", exc_info=True)
    
    def _update_display(self) -> None:
        """Update the display based on light state"""
        assets_dir = os.path.join(self.plugin_base.PATH, "assets")
        
        if self.is_on:
            icon_path = os.path.join(assets_dir, "light-on.png")
            label = "On"
        else:
            icon_path = os.path.join(assets_dir, "light-off.png")
            label = "Off"
        
        if os.path.exists(icon_path):
            self.set_media(media_path=icon_path, size=0.75)
        
        self.set_bottom_label(text=label)
    
    def initialize_homebridge_connection(self) -> None:
        """Initialize connection to Homebridge"""
        settings = self.get_settings()
        if not settings:
            return
        
        try:
            host = settings.get("homebridge_host", "http://localhost:8581")
            username = settings.get("homebridge_username", "admin")
            password = settings.get("homebridge_password", "")
            
            self.homebridge_client = HomebridgeClient(host, username, password)
            
            # Test connection
            if not self.homebridge_client.test_connection():
                logger.error("Failed to connect to Homebridge server")
                self.homebridge_client = None
        
        except Exception as e:
            logger.error(f"Error initializing Homebridge connection: {e}", exc_info=True)
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
        
        # Username
        username_row = Adw.EntryRow()
        username_row.set_title("Username")
        if settings and "homebridge_username" in settings:
            username_row.set_text(settings["homebridge_username"])
        else:
            username_row.set_text("admin")
        username_row.connect("notify::text", self._on_username_changed)
        server_group.add(username_row)
        
        # Password
        password_row = Adw.PasswordEntryRow()
        password_row.set_title("Password")
        if settings and "homebridge_password" in settings:
            password_row.set_text(settings["homebridge_password"])
        password_row.connect("notify::text", self._on_password_changed)
        server_group.add(password_row)
        
        # Connection test button
        test_button = Gtk.Button(label="Refresh Lights")
        test_button.connect("clicked", self._on_refresh_lights)
        test_button_row = Adw.ActionRow()
        test_button_row.set_title("Connection")
        test_button_row.add_suffix(test_button)
        server_group.add(test_button_row)
        
        preferences_group.add(server_group)
        
        # Light Configuration
        light_group = Adw.PreferencesGroup()
        light_group.set_title("Light Selection")
        light_group.set_description("Select the light to control")
        
        # Create dropdown for light selection
        light_model = Gtk.StringList()
        
        # Load available lights from Homebridge
        lights = self._get_available_lights()
        selected_index = 0
        current_uuid = settings.get("accessory_uuid") if settings else None
        
        for idx, light in enumerate(lights):
            light_model.append(light['name'])
            if light['uniqueId'] == current_uuid:
                selected_index = idx
        
        # If no lights found, add placeholder
        if len(lights) == 0:
            light_model.append("No lights found - Check connection")
        
        light_dropdown = Gtk.DropDown(model=light_model)
        light_dropdown.set_selected(selected_index)
        light_dropdown.connect("notify::selected", self._on_light_selected)
        
        # Store references for refresh button
        self._available_lights = lights
        self._light_dropdown = light_dropdown
        self._light_model = light_model
        
        light_row = Adw.ActionRow()
        light_row.set_title("Light")
        light_row.add_suffix(light_dropdown)
        light_group.add(light_row)
        
        preferences_group.add(light_group)
        
        return [preferences_group]
    
    def _get_available_lights(self) -> list:
        """Fetch available lights from Homebridge"""
        accessories = []
        
        try:
            settings = self.get_settings()
            if not settings:
                return accessories
            
            host = settings.get("homebridge_host", "http://localhost:8581")
            username = settings.get("homebridge_username", "admin")
            password = settings.get("homebridge_password", "")
            
            client = HomebridgeClient(host, username, password, timeout=15)
            
            # Get all accessories/characteristics
            all_items = client.get_accessories()
            if not all_items:
                return accessories
            
            # Filter for lights - look for items with controllable types
            # The response is a flat list of characteristics
            seen_lights = set()
            
            for item in all_items:
                # Check if this is a controllable light/switch device
                # The flat list shows SERVICE types (Lightbulb, Switch, Outlet, etc.)
                if item.get("type") in ["On", "Switch", "Lightbulb", "Outlet", "Dimmer"]:
                    # Use serviceName as the device name
                    name = item.get("serviceName", "Light")
                    unique_id = item.get("uniqueId", "")
                    
                    # Avoid duplicates (some lights might have multiple characteristics)
                    if unique_id and unique_id not in seen_lights:
                        seen_lights.add(unique_id)
                        accessories.append({
                            "name": name,
                            "uniqueId": unique_id,
                            "aid": item.get("aid"),
                            "iid": item.get("iid"),
                            "full": item
                        })
            
        except Exception as e:
            logger.error(f"Error fetching lights from Homebridge: {e}", exc_info=True)
        
        return accessories
    
    def _on_light_selected(self, widget, param) -> None:
        """Handle light selection from dropdown"""
        selected_index = self._light_dropdown.get_selected()
        
        if selected_index < len(self._available_lights):
            light = self._available_lights[selected_index]
            settings = self.get_settings() or {}
            settings["accessory_uuid"] = light['uniqueId']
            self.set_settings(settings)
            # Don't reset client - it can be reused for different lights
    
    def _on_refresh_lights(self, button) -> None:
        """Refresh the list of lights from Homebridge"""
        button.set_sensitive(False)  # Disable button while fetching
        button.set_label("Refreshing...")
        
        # Run in thread to avoid blocking UI
        threading.Thread(target=self._refresh_lights_async, args=(button,), daemon=True).start()
    
    def _refresh_lights_async(self, button) -> None:
        """Fetch lights asynchronously and update dropdown"""
        try:
            # Fetch fresh list of lights
            lights = self._get_available_lights()
            
            # Update stored references
            self._available_lights = lights
            
            # Clear and repopulate the dropdown model
            while self._light_model.get_n_items() > 0:
                self._light_model.remove(0)
            
            current_uuid = self.get_settings().get("accessory_uuid") if self.get_settings() else None
            selected_index = 0
            
            if len(lights) > 0:
                for idx, light in enumerate(lights):
                    self._light_model.append(light['name'])
                    if light['uniqueId'] == current_uuid:
                        selected_index = idx
                self._light_dropdown.set_selected(selected_index)
            else:
                self._light_model.append("No lights found")
                self._light_dropdown.set_selected(0)
            
            button.set_label("Refresh Lights")
            button.set_sensitive(True)
            
        except Exception as e:
            logger.error(f"Error refreshing lights: {e}", exc_info=True)
            button.set_label("Refresh Lights")
            button.set_sensitive(True)
    
    def _on_host_changed(self, widget, param) -> None:
        """Handle host change"""
        settings = self.get_settings() or {}
        settings["homebridge_host"] = widget.get_text()
        self.set_settings(settings)
        self.homebridge_client = None  # Reset connection
    
    def _on_username_changed(self, widget, param) -> None:
        """Handle username change"""
        settings = self.get_settings() or {}
        settings["homebridge_username"] = widget.get_text()
        self.set_settings(settings)
        self.homebridge_client = None  # Reset connection
    
    def _on_password_changed(self, widget, param) -> None:
        """Handle password change"""
        settings = self.get_settings() or {}
        settings["homebridge_password"] = widget.get_text()
        self.set_settings(settings)
        self.homebridge_client = None  # Reset connection
    
    def _on_accessory_changed(self, widget, param) -> None:
        """Handle accessory change"""
        settings = self.get_settings() or {}
        settings["accessory_uuid"] = widget.get_text()
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
                logger.info("Successfully connected to Homebridge")
            else:
                logger.warning("Connected but could not retrieve accessories")
        else:
            logger.error("Failed to connect to Homebridge")


"""
Homebridge Configuration Helper Module

This module provides configuration utilities for connecting to Homebridge
and discovering available accessories.
"""

import threading
from typing import Optional, List, Dict, Any, Callable
from .homebridge_client import HomebridgeClient
import logging

logger = logging.getLogger(__name__)


class HomebridgeConfigHelper:
    """Helper class for Homebridge configuration and device discovery"""
    
    def __init__(self, host: str = None, pin: str = None):
        """
        Initialize configuration helper
        
        Args:
            host: Homebridge server URL
            pin: Homebridge PIN for authentication
        """
        self.host = host
        self.pin = pin
        self.client = None
        self._accessories_cache = None
        self._discovery_thread = None
    
    def set_credentials(self, host: str, pin: str = None) -> None:
        """
        Set Homebridge credentials
        
        Args:
            host: Homebridge server URL
            pin: Homebridge PIN for authentication
        """
        self.host = host
        self.pin = pin
        self.client = None
        self._accessories_cache = None
    
    def get_client(self) -> Optional[HomebridgeClient]:
        """
        Get or create a Homebridge client
        
        Returns:
            HomebridgeClient instance or None if not configured
        """
        if self.client is None and self.host:
            self.client = HomebridgeClient(self.host, self.pin)
        return self.client
    
    def test_connection(self) -> bool:
        """
        Test connection to Homebridge server
        
        Returns:
            True if connection successful, False otherwise
        """
        client = self.get_client()
        if not client:
            return False
        return client.test_connection()
    
    def discover_accessories(self, callback: Optional[Callable] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Discover available accessories from Homebridge
        
        Args:
            callback: Optional callback function to call when discovery is complete
                     Callback will receive a list of accessories or None
        
        Returns:
            List of accessories or None if discovery fails (or runs in background if callback provided)
        """
        if callback:
            # Run discovery in background thread
            self._discovery_thread = threading.Thread(
                target=self._discover_accessories_thread,
                args=(callback,),
                daemon=True
            )
            self._discovery_thread.start()
            return None
        else:
            # Run discovery synchronously
            return self._discover_accessories_sync()
    
    def _discover_accessories_sync(self) -> Optional[List[Dict[str, Any]]]:
        """Synchronously discover accessories"""
        client = self.get_client()
        if not client:
            return None
        
        accessories = client.get_accessories()
        
        if accessories:
            # Filter to only lightbulb accessories
            light_accessories = [
                acc for acc in accessories
                if self._is_light_accessory(acc)
            ]
            self._accessories_cache = light_accessories
            return light_accessories
        
        return None
    
    def _discover_accessories_thread(self, callback: Callable) -> None:
        """Discover accessories in a background thread"""
        try:
            accessories = self._discover_accessories_sync()
            callback(accessories)
        except Exception as e:
            logger.error(f"Error during accessory discovery: {e}")
            callback(None)
    
    def get_cached_accessories(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached accessories from last discovery
        
        Returns:
            Cached accessories or None
        """
        return self._accessories_cache
    
    def get_light_names(self) -> Optional[Dict[str, str]]:
        """
        Get mapping of accessory UUID to display name
        
        Returns:
            Dict mapping UUID to friendly name, or None if no accessories discovered
        """
        accessories = self._accessories_cache or self._discover_accessories_sync()
        
        if not accessories:
            return None
        
        names = {}
        for acc in accessories:
            uuid = acc.get("uuid")
            name = acc.get("name", "Unknown")
            
            if uuid:
                names[uuid] = name
        
        return names if names else None
    
    @staticmethod
    def _is_light_accessory(accessory: Dict[str, Any]) -> bool:
        """
        Check if accessory is a light
        
        Args:
            accessory: Accessory dictionary from Homebridge API
        
        Returns:
            True if accessory is a light, False otherwise
        """
        try:
            # Check if has services
            services = accessory.get("services", [])
            
            for service in services:
                service_type = service.get("type", "")
                # Look for standard light service types
                if "Lightbulb" in service_type or "000000043" in service_type:
                    return True
            
            # Check accessory type
            accessory_type = accessory.get("type", "").lower()
            if "light" in accessory_type:
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking if accessory is light: {e}")
            return False


class AccessoryListModel:
    """Model for displaying list of available accessories"""
    
    def __init__(self, config_helper: HomebridgeConfigHelper):
        """
        Initialize accessory list model
        
        Args:
            config_helper: HomebridgeConfigHelper instance
        """
        self.config_helper = config_helper
        self.accessories = []
        self.listeners = []
    
    def add_listener(self, callback: Callable) -> None:
        """
        Add listener for model changes
        
        Args:
            callback: Function to call when model changes
        """
        self.listeners.append(callback)
    
    def notify_listeners(self) -> None:
        """Notify all listeners of model changes"""
        for listener in self.listeners:
            try:
                listener(self.accessories)
            except Exception as e:
                logger.error(f"Error notifying listener: {e}")
    
    def refresh(self) -> None:
        """Refresh accessory list from Homebridge"""
        def on_discovery_complete(accessories):
            if accessories:
                self.accessories = [
                    {
                        "uuid": acc.get("uuid", ""),
                        "name": acc.get("name", "Unknown"),
                        "manufacturer": acc.get("manufacturer", ""),
                        "model": acc.get("model", ""),
                        "serial_number": acc.get("serial_number", "")
                    }
                    for acc in accessories
                ]
            else:
                self.accessories = []
            
            self.notify_listeners()
        
        self.config_helper.discover_accessories(callback=on_discovery_complete)
    
    def get_accessories(self) -> List[Dict[str, str]]:
        """
        Get list of accessories
        
        Returns:
            List of accessory dictionaries
        """
        return self.accessories
    
    def get_accessory_by_uuid(self, uuid: str) -> Optional[Dict[str, str]]:
        """
        Get accessory by UUID
        
        Args:
            uuid: Accessory UUID
        
        Returns:
            Accessory dictionary or None
        """
        for acc in self.accessories:
            if acc["uuid"] == uuid:
                return acc
        return None

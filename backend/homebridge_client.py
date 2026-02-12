"""
Homebridge API Client Module

This module provides a simple interface to communicate with Homebridge servers.
Based on: https://github.com/sergey-tihon/streamdeck-homebridge
"""

import requests
import json
from typing import Optional, Dict, List, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class HomebridgeClient:
    """Client for interacting with Homebridge API using Bearer token authentication"""
    
    def __init__(self, host: str, username: str, password: str, timeout: int = 5):
        """
        Initialize Homebridge client
        
        Args:
            host: The Homebridge server URL (e.g., http://localhost:8581)
            username: Homebridge username (usually 'admin')
            password: Homebridge password
            timeout: Request timeout in seconds
        """
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
    def _is_token_valid(self) -> bool:
        """Check if current token is still valid"""
        if not self.access_token or not self.token_expires_at:
            return False
        is_valid = datetime.now() < self.token_expires_at
        time_remaining = (self.token_expires_at - datetime.now()).total_seconds() / 60
        logger.debug(f"Token valid: {is_valid}, Time remaining: {time_remaining:.1f} mins")
        return is_valid
    
    def authenticate(self) -> bool:
        """
        Authenticate with Homebridge server via /api/auth/login
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            url = f"{self.host}/api/auth/login"
            body = {
                "username": self.username,
                "password": self.password
            }
            
            logger.info(f"Authenticating with Homebridge at {self.host}")
            
            response = requests.post(
                url,
                json=body,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get("access_token")
            
            # Calculate when token expires (subtract 10 mins as buffer)
            expires_in = data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 600)
            
            logger.info(f"✓ Token obtained successfully. Expires in {expires_in/3600:.1f} hours at {self.token_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            return bool(self.access_token)
        except Exception as e:
            logger.error(f"✗ Authentication failed: {e}")
            self.access_token = None
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authorization token"""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
        
    def get_accessories(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of all accessories from Homebridge via /api/accessories
        
        Returns:
            List of accessories or None if request fails
        """
        try:
            # Re-authenticate if token is expired
            if not self._is_token_valid() and not self.authenticate():
                logger.debug("[GET_ACC] Failed to authenticate before fetching")
                return None
                
            url = f"{self.host}/api/accessories"
            headers = self._get_headers()
            
            logger.debug(f"[GET_ACC] Fetching from {url}")
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"[GET_ACC] Received {len(data) if isinstance(data, list) else '?'} items")
            if isinstance(data, list) and len(data) > 0:
                logger.debug(f"[GET_ACC] First item sample: {data[0]}")
            
            return data
            
        except Exception as e:
            logger.error(f"[GET_ACC] Error fetching accessories: {e}", exc_info=True)
            return None
    
    def set_characteristic(self, accessory_id: str, characteristic_type: str, value: Any) -> bool:
        """
        Set a characteristic value for an accessory via PUT /api/accessories/{uniqueId}
        
        Args:
            accessory_id: The unique ID of the accessory
            characteristic_type: The type of characteristic (e.g., "On", "Brightness")
            value: The value to set
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Re-authenticate if token is expired
            if not self._is_token_valid() and not self.authenticate():
                logger.error("Failed to authenticate before setting characteristic")
                return False
                
            url = f"{self.host}/api/accessories/{accessory_id}"
            headers = self._get_headers()
            
            # Convert boolean to 0/1 for JSON serialization
            # Keep value as int/float, NOT as string - JSON will handle the type
            if isinstance(value, bool):
                value_to_send = 1 if value else 0
            else:
                value_to_send = value
            
            payload = {
                "characteristicType": characteristic_type,
                "value": value_to_send
            }
            
            logger.debug(f"Setting {characteristic_type}={value_to_send} for {accessory_id}")
            
            response = requests.put(url, json=payload, headers=headers, timeout=self.timeout)
            
            if response.status_code >= 400:
                logger.error(f"Failed to set characteristic: HTTP {response.status_code}")
                return False
            
            response.raise_for_status()
            logger.debug(f"Successfully set {characteristic_type} for {accessory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting characteristic: {e}", exc_info=True)
            return False
    
    def toggle_light(self, accessory_id: str) -> bool:
        """
        Toggle a light on/off
        
        Args:
            accessory_id: The unique ID of the light accessory
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current state from the individual accessory endpoint
            url = f"{self.host}/api/accessories/{accessory_id}"
            
            # Re-authenticate if needed
            if not self._is_token_valid() and not self.authenticate():
                logger.error("Failed to authenticate")
                return False
            
            headers = self._get_headers()
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse the response to find current state
            current_state = None
            
            # The official plugin expects serviceCharacteristics array
            if isinstance(data, dict) and "serviceCharacteristics" in data:
                chars = data.get("serviceCharacteristics", [])
                
                # For dimmers and other devices, look for On characteristic
                for char in chars:
                    if char.get("type") in ["On", "Switch"]:
                        current_state = char.get("value")
                        break
            elif isinstance(data, dict) and "values" in data:
                # Alternative values dict structure
                values = data.get("values", {})
                for key, value in values.items():
                    if isinstance(value, bool):
                        current_state = value
                        break
            elif isinstance(data, list):
                # Flat list structure - find Switch characteristic
                for item in data:
                    if item.get("type") in ["On", "Switch"]:
                        current_state = item.get("value")
                        break
            
            if current_state is None:
                logger.error(f"Could not determine current state for accessory {accessory_id}")
                return False
            
            # Convert to boolean if needed
            if isinstance(current_state, int):
                current_state = bool(current_state)
            
            # Toggle the state
            new_state = not current_state
            logger.debug(f"Toggling light {accessory_id}: {current_state} → {new_state}")
            
            # Set the new state - ALWAYS use "On" as characteristic type
            result = self.set_characteristic(accessory_id, "On", new_state)
            return result
            
        except Exception as e:
            logger.error(f"Error toggling light: {e}", exc_info=True)
            return False
    
    def get_light_status(self, accessory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete status of a light accessory via dedicated endpoint
        
        Args:
            accessory_id: The unique ID of the light accessory
        
        Returns:
            Dictionary with light status or None if request fails
        """
        try:
            # Re-authenticate if token is expired
            if not self._is_token_valid() and not self.authenticate():
                return None
            
            # Use the individual accessory endpoint to get current values
            url = f"{self.host}/api/accessories/{accessory_id}"
            headers = self._get_headers()
            
            logger.debug(f"[GET_STATUS] Fetching from {url}")
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"[GET_STATUS] Response: {data}")
            
            status = {}
            
            # The response should have a 'values' array with current characteristic values
            if isinstance(data, dict):
                # Check if it has values array
                if "values" in data:
                    values = data.get("values", {})
                    # values is likely a dict: {"1.10": true, "1.9": false, ...}
                    for key, value in values.items():
                        logger.debug(f"[GET_STATUS]   {key}: {value}")
                        # We need to map these back to characteristic types somehow
                        # For now, assume the first boolean is the On/Switch state
                        if isinstance(value, bool):
                            status["on"] = value
                            break
                elif "serviceCharacteristics" in data:
                    # Alternative structure with nested characteristics
                    for char in data.get("serviceCharacteristics", []):
                        char_type = char.get("type")
                        value = char.get("value")
                        
                        if char_type in ["On", "Switch"]:
                            status["on"] = value
                        elif char_type == "Brightness":
                            status["brightness"] = value
                else:
                    # Flat structure - find On/Switch characteristic
                    if isinstance(data, list):
                        for item in data:
                            char_type = item.get("type")
                            value = item.get("value")
                            if char_type in ["On", "Switch"]:
                                status["on"] = value
            
            logger.debug(f"[GET_STATUS] Parsed status: {status}")
            return status if status else None
            
        except Exception as e:
            logger.error(f"[GET_STATUS] Error getting light status: {e}", exc_info=True)
            return None
    
    def get_token_status(self) -> Dict[str, Any]:
        """
        Get current token status for debugging
        
        Returns:
            Dictionary with token status information
        """
        if not self.access_token:
            return {"status": "No token", "authenticated": False}
        
        if not self.token_expires_at:
            return {"status": "Token exists but expiration unknown", "authenticated": True}
        
        time_remaining = (self.token_expires_at - datetime.now()).total_seconds()
        is_valid = time_remaining > 0
        
        return {
            "authenticated": True,
            "status": "Valid" if is_valid else "Expired",
            "expires_at": self.token_expires_at.isoformat(),
            "time_remaining_minutes": round(time_remaining / 60, 1)
        }
    
    def test_connection(self) -> bool:
        """
        Test if connection to Homebridge server is working
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Re-authenticate if token is expired
            if not self._is_token_valid() and not self.authenticate():
                return False
            
            url = f"{self.host}/api/accessories"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


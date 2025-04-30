"""
Configuration Manager Module for I-CTF Application

This module provides functionality for managing application configuration settings, 
including directory paths. It handles loading, saving, and updating configuration data
for the CTF training platform.

Author: Matthew Tomme
Date: April 30, 2025
Version: 1.0
"""

import os
import json
import logging
from PyQt5.QtWidgets import QMessageBox

# Set up logging
logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages application configuration settings, including directory paths for the CTF application.
    
    This class handles loading, saving, and updating configuration data stored in a JSON file.
    It provides methods for getting and setting the base directory and managing multiple CTF directories.
    """
    
    def __init__(self):
        """
        Initialize the configuration manager by setting up the config file path
        and loading the current configuration.
        """
        # Set up the path to the configuration file
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ctf_config.json")
        
        # Load the configuration
        self.config = self.load()
        
        logger.info("Configuration manager initialized")
    
    def load(self):
        """
        Load the configuration file from disk.
        
        Returns:
            dict: A dictionary containing the configuration settings
        """
        # Default configuration
        config = {
            "base_directory": None, 
            "directories": []
        }
        
        # Try to load existing configuration
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info("Configuration loaded from file")
            except json.JSONDecodeError:
                logger.error("Invalid JSON in configuration file")
            except Exception as e:
                logger.error(f"Error loading config: {str(e)}")
        else:
            logger.info("No configuration file found, using defaults")
        
        return config
    
    def save(self):
        """
        Save the current configuration to disk.
        
        Returns:
            bool: True if the save was successful, False otherwise
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved to file")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            return False
    
    def get_base_directory(self):
        """
        Get the current base directory for CTF files.
        
        Returns:
            str: The current base directory path, or None if not set
        """
        return self.config.get("base_directory")
    
    def set_base_directory(self, directory):
        """
        Set the base directory for CTF files and save the configuration.
        
        Args:
            directory (str): The directory path to set as the base directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not directory or not os.path.exists(directory):
            logger.error(f"Invalid directory path: {directory}")
            return False
            
        self.config["base_directory"] = directory
        
        # Also add to the list of directories if not already there
        if directory not in self.config.get("directories", []):
            if "directories" not in self.config:
                self.config["directories"] = []
            self.config["directories"].append(directory)
            
        return self.save()
    
    def get_directories(self):
        """
        Get all saved CTF directories.
        
        Returns:
            list: A list of all directory paths that have been saved
        """
        return self.config.get("directories", [])
    
    def add_directory(self, directory):
        """
        Add a directory to the list if it's not already there.
        
        Args:
            directory (str): The directory path to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate directory path
        if not directory or not os.path.exists(directory):
            logger.error(f"Invalid directory path: {directory}")
            return False
            
        # Ensure the directories key exists
        if "directories" not in self.config:
            self.config["directories"] = []
        
        # Only add if not already in the list
        if directory not in self.config["directories"]:
            self.config["directories"].append(directory)
            logger.info(f"Added directory to configuration: {directory}")
            return self.save()
        
        return True
    
    def remove_directory(self, directory):
        """
        Remove a directory from the list and update the base directory if needed.
        
        Args:
            directory (str): The directory path to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        if "directories" in self.config and directory in self.config["directories"]:
            # Remove the directory
            self.config["directories"].remove(directory)
            logger.info(f"Removed directory from configuration: {directory}")
            
            # If we're removing the current directory, update that too
            if directory == self.config.get("base_directory"):
                if self.config["directories"]:
                    # Use the first available directory as the new base
                    self.config["base_directory"] = self.config["directories"][0]
                    logger.info(f"Updated base directory to: {self.config['base_directory']}")
                else:
                    # No directories left
                    self.config["base_directory"] = None
                    logger.info("No base directory set")
            
            return self.save()
        
        return False
    
    def clear_all(self):
        """
        Clear all configuration data.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.config = {
            "base_directory": None,
            "directories": []
        }
        logger.info("Configuration cleared")
        return self.save()
    
    def export_config(self, export_path):
        """
        Export the configuration to a specified file.
        
        Args:
            export_path (str): Path to export the configuration to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(export_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration exported to: {export_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting configuration: {str(e)}")
            return False
    
    def import_config(self, import_path):
        """
        Import configuration from a specified file.
        
        Args:
            import_path (str): Path to import the configuration from
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(import_path):
            logger.error(f"Import file does not exist: {import_path}")
            return False
            
        try:
            with open(import_path, 'r') as f:
                new_config = json.load(f)
                
            # Validate the imported configuration
            if not isinstance(new_config, dict):
                logger.error("Invalid configuration format")
                return False
                
            # Check required keys
            if "base_directory" not in new_config:
                new_config["base_directory"] = None
            if "directories" not in new_config:
                new_config["directories"] = []
                
            # Validate directories exist
            valid_dirs = []
            for directory in new_config["directories"]:
                if os.path.exists(directory):
                    valid_dirs.append(directory)
                else:
                    logger.warning(f"Directory from imported config does not exist: {directory}")
            
            new_config["directories"] = valid_dirs
            
            # Update base directory if it doesn't exist
            if new_config["base_directory"] is not None and not os.path.exists(new_config["base_directory"]):
                if valid_dirs:
                    new_config["base_directory"] = valid_dirs[0]
                else:
                    new_config["base_directory"] = None
                    
            # Update configuration and save
            self.config = new_config
            success = self.save()
            
            if success:
                logger.info(f"Configuration imported from: {import_path}")
            
            return success
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in import file")
            return False
        except Exception as e:
            logger.error(f"Error importing configuration: {str(e)}")
            return False
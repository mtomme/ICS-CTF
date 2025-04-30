"""
Main Module for I-CTF Application

This is the entry point for the Islander Cyber Society's CTF application.
It initializes the application and starts the main event loop.

Author: Matthew Tomme
Date: April 30, 2025
Version: 1.0
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ctf_app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_required_files():
    """
    Create required JSON files if they don't exist.
    
    This function ensures that the necessary configuration and
    data files exist before the application starts.
    
    Returns:
        bool: True if all files were created successfully or already exist, False otherwise
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = {
        "ctf_stats.json": "{}",
        "ctf_progress.json": "{}",
        "ctf_config.json": '{"base_directory": null, "directories": []}'
    }
    
    success = True
    
    for filename, initial_content in required_files.items():
        file_path = os.path.join(base_dir, filename)
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w') as f:
                    f.write(initial_content)
                logger.info(f"Created {filename}")
            except Exception as e:
                logger.error(f"Error creating {filename}: {str(e)}")
                success = False
        else:
            logger.info(f"{filename} already exists")
    
    # Create required directories
    required_dirs = ["icons"]
    
    for dirname in required_dirs:
        dir_path = os.path.join(base_dir, dirname)
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
                logger.info(f"Created directory: {dirname}")
            except Exception as e:
                logger.error(f"Error creating directory {dirname}: {str(e)}")
                success = False
        else:
            logger.info(f"Directory {dirname} already exists")
    
    return success


def parse_arguments():
    """
    Parse command line arguments.
    
    This function handles command line arguments that control
    the application's behavior at startup.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Islander Cyber Society CTF Application')
    parser.add_argument('--directory', '-d', help='Path to CTF directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--reset', action='store_true', help='Reset all progress')
    
    return parser.parse_args()


def main():
    """
    Main function to start the application.
    
    This function initializes the PyQt5 application,
    creates the main window, and starts the event loop.
    """
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Set logging level based on debug flag
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
        
        # Create required files and directories
        if not create_required_files():
            logger.warning("Some required files or directories could not be created")
        
        # Import Qt libraries here to fail gracefully if not installed
        try:
            from PyQt5.QtWidgets import QApplication
            from app import CTFApplication
        except ImportError:
            logger.error("PyQt5 is required to run this application. Please install it using 'pip install PyQt5'")
            sys.exit(1)
        
        # Start the Qt application
        app = QApplication(sys.argv)
        main_window = CTFApplication()
        
        # Apply command line arguments
        if args.directory:
            logger.info(f"Setting CTF directory from command line: {args.directory}")
            if os.path.exists(args.directory):
                main_window.paths.set_base_directory(args.directory)
                main_window.set_path_label(args.directory)
                main_window.load_modules()
            else:
                logger.error(f"Directory not found: {args.directory}")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(main_window, "Error", f"Directory not found: {args.directory}")
        
        # Reset progress if requested
        if args.reset and hasattr(main_window, 'progress'):
            logger.info("Resetting progress from command line")
            main_window.progress.reset()
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(main_window, "Reset", "Progress has been reset")
        
        # Show the main window and start the application
        main_window.show()
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        print(f"Critical error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
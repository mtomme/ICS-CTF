"""
TAMU-CC Colors Module for I-CTF Application

This module defines the official TAMU-CC colors for use in the CTF application.
It provides constants for all primary, secondary, and accent colors from the
university's official brand guidelines.

Author: Matthew Tomme
Date: April 30, 2025
Version: 1.0
"""

class TAMUCCColors:
    """
    Contains all official TAMU-CC brand colors as constants.
    Colors are organized by primary, secondary, and accent categories.
    """
    
    # Primary Palette
    ISLANDER_BLUE = "#0067C5"    # RGB: 0, 103, 197
    ISLANDER_GREEN = "#007F3E"   # RGB: 0, 127, 62
    SILVER = "#9EA2A4"           # RGB: 158, 162, 164
    
    # Secondary Palette
    IZZY_BLUE = "#1C92D1"        # RGB: 28, 146, 209
    DEEP_END_BLUE = "#001A31"    # RGB: 0, 26, 49
    LITE_COOL_GRAY = "#C8C9C7"   # RGB: 200, 201, 199
    COOL_GRAY = "#636A6A"        # RGB: 99, 106, 106
    
    # Special Use Accent Colors
    SKY_BLUE = "#5AC9E5"         # RGB: 90, 201, 229
    PALM_GREEN = "#00AD4D"       # RGB: 0, 173, 77
    BLACK_3C = "#000000"         # RGB: 0, 0, 0
    
    @staticmethod
    def get_difficulty_color(difficulty):
        """
        Get the color associated with a specific difficulty level.
        
        Args:
            difficulty (str): The difficulty level ('Beginner', 'Intermediate', 'Advanced', 'Insane')
            
        Returns:
            str: Hex color code for the difficulty
        """
        difficulty_colors = {
            "Beginner": TAMUCCColors.ISLANDER_BLUE,
            "Intermediate": TAMUCCColors.IZZY_BLUE,
            "Advanced": TAMUCCColors.DEEP_END_BLUE,
            "Insane": TAMUCCColors.ISLANDER_GREEN
        }
        
        return difficulty_colors.get(difficulty, TAMUCCColors.ISLANDER_BLUE)
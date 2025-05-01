"""
Application Module for I-CTF Application

This module provides the main application class for the CTF application.
It manages the overall application flow, UI, and interactions between components.

Author: Matthew Tomme
Date: April 30, 2025
Version: 1.0
"""

import os
import sys
import logging
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QFrame, QGridLayout,
                           QFileDialog, QMessageBox, QStatusBar, QSplitter, 
                           QScrollArea, QSizePolicy, QDialog, QDialogButtonBox,
                           QTextEdit)
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtGui import QFont, QIcon, QPixmap

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    pdf_viewer_available = True
except ImportError:
    pdf_viewer_available = False
    logging.warning("PyQtWebEngine not available, PDF viewing will be limited to download only")

# Import application components - these will be implemented in separate files
from config import ConfigManager
from paths import PathManager
from progress import ProgressManager
from ui_components import (ModuleCard, TopicCard, QuestionPanel, 
                          RoundedPushButton, create_styled_label)

# Set up logging
logger = logging.getLogger(__name__)


class CTFApplication(QMainWindow):
    """
    Main application class for the Islander Cyber Society's CTF application.
    
    This class integrates all components and provides the main UI and
    application logic for the CTF training platform.
    """
    
    def __init__(self):
        """Initialize the application with all required components."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("Islander Cyber Society CTF")
        self.setMinimumSize(900, 700)
        
        # Initialize managers
        self.config = ConfigManager()
        self.paths = PathManager(self.config)
        self.progress = ProgressManager()
        
        # Data structures
        self.modules = []
        self.difficulties = ["Beginner", "Intermediate", "Advanced", "Insane"]
        self.current_module = None
        self.current_difficulty = None
        self.current_topic = None
        self.current_topic_display = None
        self.question_widgets = {}
        
        # Current page tracking
        self.current_page = "modules"  # Can be: modules, difficulties, topics, questions
        
        # Set up the UI
        self.setup_ui()
        
        # Set up the menus
        self.create_menus()
        
        logger.info("CTF Application initialized")

    def setup_ui(self):
        """Set up the main user interface."""
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create title bar
        self.create_title_bar()
        
        # Create navigation area
        self.create_navigation_area()
        
        # Create content area
        self.create_content_area()
        
        # Create status bar
        self.setup_status_bar()
        
        logger.debug("UI setup complete")
    
    def create_title_bar(self):
        """Create the application title bar."""
        title_container = QWidget()
        title_container.setStyleSheet("""
            background-color: #0067C5;
            border-bottom: 1px solid #001A31;
            padding: 10px;
        """)
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        # Title text
        title_label = QLabel("Islander Cyber Society CTF")
        title_label.setStyleSheet("""
            color: white;
            font-size: 40px;
            font-weight: bold;
        """)
        title_layout.addWidget(title_label)
        
        # Add stretch to push everything to the left
        title_layout.addStretch()
        
        # Add to main layout
        self.main_layout.addWidget(title_container)
    
    def create_navigation_area(self):
        """Create the navigation area with breadcrumb and back button panel."""
        nav_container = QWidget()
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(15, 10, 15, 10)  # Increased margins
        
        # Create back button section
        self.nav_buttons_panel = QWidget()
        nav_buttons_layout = QHBoxLayout(self.nav_buttons_panel)
        nav_buttons_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.addWidget(self.nav_buttons_panel)
        
        # Create breadcrumb
        self.breadcrumb_label = QLabel("Main Menu")
        self.breadcrumb_label.setStyleSheet("""
            color: #0067C5;
            font-weight: bold;
            font-size: 12pt;  /* Increased font size */
            padding: 5px;
        """)
        nav_layout.addWidget(self.breadcrumb_label)
        
        # Add stretch to push the path label to the right
        nav_layout.addStretch()
        
        # Add path label with larger font
        self.path_label = QLabel(f"CTF Path: {self.paths.base_directory or 'Not Selected'}")
        self.path_label.setStyleSheet("""
            font-size: 12pt;  /* Increased font size */
            padding: 5px;
        """)
        nav_layout.addWidget(self.path_label)
        
        # Add to main layout
        self.main_layout.addWidget(nav_container)
    
    def create_content_area(self):
        """Create the main content area with responsive layout."""
        # Create the content frame
        self.content_frame = QFrame()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(20, 20, 20, 20)  # Increased margins
        self.content_layout.setSpacing(15)  # Increased spacing
        
        # Set the content frame to expand and fill available space
        self.content_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Add to main layout
        self.main_layout.addWidget(self.content_frame, 1)  # stretch=1 to take remaining space
    
    def resizeEvent(self, event):
        """Handle window resize events to adjust layout."""
        super().resizeEvent(event)
        
        # Adjust the number of columns based on window width
        window_width = event.size().width()
        
        # Adjust cols variable in show_modules_page if we're on that page
        if hasattr(self, 'current_page') and self.current_page == "modules":
            if window_width < 800:
                self.module_columns = 3
            elif window_width < 1200:
                self.module_columns = 4
            else:
                self.module_columns = 5
                
            # Refresh the modules page to use the new column count
            # Only do this if we've already loaded modules
            if hasattr(self, 'modules') and self.modules:
                # Store the current scroll position
                scroll_area = None
                scroll_position = 0
                
                # If we can find a scroll area, store its position
                for i in range(self.content_layout.count()):
                    widget = self.content_layout.itemAt(i).widget()
                    if isinstance(widget, QScrollArea):
                        scroll_area = widget
                        scroll_position = scroll_area.verticalScrollBar().value()
                        break
                
                # Refresh the page
                self.show_modules_page()
                
                # Restore scroll position if we had one
                if scroll_area:
                    scroll_area.verticalScrollBar().setValue(scroll_position)
    
    def setup_status_bar(self):
        """Create the status bar with completion information."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Status message
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: white;")
        status_bar.addWidget(self.status_label)
        
        # Add spacer
        status_bar.addPermanentWidget(QWidget(), 1)  # stretch=1
        
        # Add accuracy indicator
        self.accuracy_label = QLabel("Accuracy: N/A")
        self.accuracy_label.setStyleSheet("color: white; padding-right: 10px;")
        status_bar.addPermanentWidget(self.accuracy_label)
        
        # Update accuracy display
        self.update_accuracy_display()

    def clear_content_frame(self):
        """
        Clear all widgets from the content frame to prepare for new content.
        
        Also clears navigation buttons while keeping the path label.
        """
        # Clear content layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear navigation buttons panel
        while self.nav_buttons_panel.layout().count():
            item = self.nav_buttons_panel.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def set_path_label(self, path):
        """
        Update the path label with the provided path.
        
        Args:
            path (str): The path to display
        """
        self.path_label.setText(f"CTF Path: {path}")
    
    def update_accuracy_display(self):
        """Update the accuracy display in the status bar."""
        stats = self.progress.get_overall_stats()
        
        if stats['total_attempts'] > 0:
            accuracy = stats['accuracy'] * 100
            self.accuracy_label.setText(f"Accuracy: {accuracy:.1f}% ({stats['correct_attempts']}/{stats['total_attempts']})")
        else:
            self.accuracy_label.setText("Accuracy: N/A")

    def show_directory_dialog(self):
        """Show dialog to select the CTF directory."""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        directory = QFileDialog.getExistingDirectory(
            self, "Select CTF Directory", 
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            # Check if it's a valid CTF directory
            if not self.paths.is_valid_ctf_directory(directory):
                reply = QMessageBox.question(
                    self, "Warning", 
                    "This directory doesn't appear to be a valid CTF directory. Use it anyway?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            
            # Set the directory
            success = self.paths.set_base_directory(directory)
            if success:
                self.set_path_label(directory)
                self.load_modules()
                self.status_label.setText(f"Loaded CTF directory: {directory}")
                logger.info(f"Set CTF directory: {directory}")
            else:
                QMessageBox.critical(self, "Error", f"Could not set CTF directory: {directory}")

    def add_ctf_directory(self):
        """Add a new CTF directory to the list of available directories."""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        directory = QFileDialog.getExistingDirectory(
            self, "Add New CTF Directory", 
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not directory:
            return
            
        # Check if it's a valid CTF directory
        if not self.paths.is_valid_ctf_directory(directory):
            reply = QMessageBox.question(
                self, "Warning", 
                "This directory doesn't appear to be a valid CTF directory. Add it anyway?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # Add directory to config
        if self.config.add_directory(directory):
            QMessageBox.information(self, "Success", f"Added directory: {directory}")
            
            # Ask if user wants to switch to this directory
            reply = QMessageBox.question(
                self, "Switch Directory", 
                f"Do you want to switch to the new directory?\n{directory}",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.paths.set_base_directory(directory)
                self.set_path_label(directory)
                self.load_modules()
                self.status_label.setText(f"Loaded CTF directory: {directory}")
        else:
            QMessageBox.critical(self, "Error", f"Could not add directory: {directory}")
    
    def load_modules(self):
        """
        Load modules from the base directory and display the module selection page.
        
        Gets all subdirectories in the base directory and shows the modules page.
        """
        if not self.paths.base_directory or not os.path.exists(self.paths.base_directory):
            QMessageBox.critical(self, "Error", "Please select a valid CTF directory.")
            return
        
        # Get all subdirectories in the base directory (modules)
        self.modules = []
        try:
            for item in os.listdir(self.paths.base_directory):
                item_path = os.path.join(self.paths.base_directory, item)
                if os.path.isdir(item_path):
                    self.modules.append(item)
            
            logger.info(f"Loaded {len(self.modules)} modules")
            
            # Show the modules page
            self.show_modules_page()
        except Exception as e:
            logger.error(f"Error loading modules: {str(e)}")
            QMessageBox.critical(self, "Error", f"Could not load modules: {str(e)}")
        
    def show_modules_page(self):
        """
        Display the main module selection page with responsive layout.
        
        Shows all available modules and highlights the "Getting Started" module.
        Adapts to the window size for better display.
        """
        self.clear_content_frame()
        self.current_page = "modules"

        # Update breadcrumb
        self.breadcrumb_label.setText("Main Menu")

        # Create a title
        title_label = create_styled_label(
            "Select a Module", 
            font_size=24, 
            font_weight="bold",
            color="#0067C5",
            alignment=Qt.AlignCenter
        )
        self.content_layout.addWidget(title_label)

        # Create a scroll area to contain the grid
        from PyQt5.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create container for grid
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(20, 20, 20, 20)
        grid_layout.setSpacing(25)  # Increased spacing
        
        # Set initial number of columns based on window width (if not already set)
        if not hasattr(self, 'module_columns'):
            window_width = self.width()
            if window_width < 800:
                self.module_columns = 3
            elif window_width < 1200:
                self.module_columns = 4
            else:
                self.module_columns = 5
        
        cols = self.module_columns
        
        # Position Getting Started at top center if available
        getting_started_row = 0
        getting_started_col = cols // 2  # Center column
        getting_started_shown = False

        if "Getting Started" in self.modules:
            # Check completion status
            completed = self.is_module_completed("Getting Started")
            completion_percentage = self.calculate_module_completion("Getting Started")
            
            # Create the module card with the completion percentage (which will be converted to int internally)
            getting_started_card = ModuleCard("Getting Started", completed, completion_percentage)
            getting_started_card.set_click_handler(lambda: self.select_module("Getting Started"))
            
            # Add to the grid at the top center position
            grid_layout.addWidget(getting_started_card, getting_started_row, getting_started_col)
            getting_started_shown = True
            
            # Remove from the list so it's not repeated below
            modules_list = [m for m in sorted(self.modules) if m != "Getting Started"]
        else:
            modules_list = sorted(self.modules)
        
        # Calculate grid dimensions for remaining modules
        start_row = 1 if getting_started_shown else 0
        
        # Place modules in the grid
        for i, module in enumerate(modules_list):
            row = start_row + (i // cols)
            col = i % cols
            
            # Check completion status
            completed = self.is_module_completed(module)
            completion_percentage = self.calculate_module_completion(module)
            
            # Create module card
            module_card = ModuleCard(module, completed, completion_percentage)
            module_card.set_click_handler(lambda m=module: self.select_module(m))
            
            # Place in grid
            grid_layout.addWidget(module_card, row, col)

        # Make sure columns have equal width
        for i in range(cols):
            grid_layout.setColumnStretch(i, 1)
        
        # Add the grid container to the scroll area
        scroll_area.setWidget(grid_container)
        
        # Add the scroll area to the content layout with stretch to fill available space
        self.content_layout.addWidget(scroll_area, 1)  # Use stretch factor of 1

        # Update status
        self.status_label.setText("Select a module to begin")

    def select_module(self, module):
        """
        Handle module selection and navigate to the appropriate page.
        
        Args:
            module (str): The selected module name
        """
        # Update state
        self.current_module = module
        
        # If this is "Getting Started", go directly to topics
        if module == "Getting Started":
            self.show_topics_page(None)  # No difficulty for Getting Started
        else:
            self.show_difficulties_page()
    
    def show_difficulties_page(self):
        """
        Display the difficulty selection page for the current module.
        
        Shows the available difficulty levels for the selected module with improved layout.
        """
        self.clear_content_frame()
        self.current_page = "difficulties"
        
        # Update breadcrumb
        self.breadcrumb_label.setText(f"Main Menu > {self.current_module}")

        # Add back button
        back_btn = RoundedPushButton("Back to Modules")
        back_btn.setMinimumHeight(40)  # Make button taller
        back_btn.setFont(QFont("Segoe UI", 11))  # Larger font
        back_btn.clicked.connect(self.show_modules_page)
        self.nav_buttons_panel.layout().addWidget(back_btn)

        # Create title
        title_label = create_styled_label(
            f"Select Difficulty for {self.current_module}", 
            font_size=24, 
            font_weight="bold",
            color="#0067C5",
            alignment=Qt.AlignCenter
        )
        self.content_layout.addWidget(title_label)

        # Create a container for difficulty buttons
        difficulties_container = QWidget()
        difficulties_layout = QVBoxLayout(difficulties_container)
        difficulties_layout.setSpacing(20)
        difficulties_layout.setContentsMargins(50, 30, 50, 30)  # Add more spacing around buttons
        
        # Get screen size to calculate appropriate button size
        screen_width = self.width()
        button_width = int(min(600, screen_width * 0.5))  # 50% of screen width, max 600px
        
        # Display difficulty buttons
        for difficulty in self.difficulties:
            # Check if this difficulty exists for the current module
            difficulty_path = self.paths.get_difficulty_path(self.current_module, difficulty)
            if difficulty_path and os.path.exists(difficulty_path):
                # Check completion status
                completed = self.is_difficulty_completed(self.current_module, difficulty)
                
                # Create container for button with horizontal layout to center it
                button_container = QWidget()
                button_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                h_layout = QHBoxLayout(button_container)
                h_layout.setContentsMargins(0, 0, 0, 0)
                
                # Get the appropriate color for the difficulty
                color = self.get_difficulty_color(difficulty)
                
                # Create button with completion indicator
                btn_text = f"✓ {difficulty}" if completed else difficulty
                difficulty_btn = RoundedPushButton(btn_text)
                difficulty_btn.set_color(color)
                
                # Set a darker hover color for Intermediate to ensure contrast
                if difficulty == "Intermediate":
                    difficulty_btn.set_hover_color("#0E7EB9")  # Darker shade than normal color
                
                # Make button bigger
                difficulty_btn.setMinimumHeight(70)
                difficulty_btn.setMinimumWidth(button_width)
                difficulty_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
                difficulty_btn.clicked.connect(lambda checked, d=difficulty: self.select_difficulty(d))
                
                # Center the button
                h_layout.addStretch(1)
                h_layout.addWidget(difficulty_btn)
                h_layout.addStretch(1)
                
                # Add to main layout
                difficulties_layout.addWidget(button_container)

        # Create scroll area to handle potential overflow
        from PyQt5.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(difficulties_container)
        
        # Add the scroll area to the content area
        self.content_layout.addWidget(scroll_area, 1)  # Use stretch=1

        # Update status
        self.status_label.setText(f"Module: {self.current_module} - Select a difficulty level")
    
    def select_difficulty(self, difficulty):
        """
        Handle difficulty selection and navigate to topics page.
        
        Args:
            difficulty (str): The selected difficulty level
        """
        # Update state
        self.current_difficulty = difficulty
        self.show_topics_page(difficulty)
    
    def get_difficulty_color(self, difficulty):
        """
        Get the color associated with a difficulty level.
        
        Args:
            difficulty (str): The difficulty level
            
        Returns:
            str: Hex color code for the difficulty
        """
        difficulty_colors = {
            "Beginner": "#0067C5",     # Islander Blue
            "Intermediate": "#1C92D1", # Izzy Blue
            "Advanced": "#001A31",     # Deep End Blue
            "Insane": "#007F3E"        # Islander Green
        }
        
        return difficulty_colors.get(difficulty, "#0067C5")
    
    def show_topics_page(self, difficulty):
        """
        Display the topic selection page for the current module and difficulty.
        
        Args:
            difficulty (str): The difficulty level, or None for modules without difficulties
        """
        self.clear_content_frame()
        self.current_page = "topics"

        # Update breadcrumb
        if difficulty:
            self.breadcrumb_label.setText(f"Main Menu > {self.current_module} > {difficulty}")
        else:
            self.breadcrumb_label.setText(f"Main Menu > {self.current_module}")

        # Add back button with improved styling
        if difficulty:
            back_btn = self.create_back_button("Back to Difficulties", self.show_difficulties_page)
        else:
            back_btn = self.create_back_button("Back to Modules", self.show_modules_page)
        self.nav_buttons_panel.layout().addWidget(back_btn)

        # Create title
        if difficulty:
            title_text = f"Select Topic for {self.current_module} - {difficulty}"
        else:
            title_text = f"Select Topic for {self.current_module}"
            
        title_label = create_styled_label(
            title_text, 
            font_size=24, 
            font_weight="bold",
            color="#0067C5",
            alignment=Qt.AlignCenter
        )
        self.content_layout.addWidget(title_label)

        # Create scroll area for topic grid
        from PyQt5.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Create container for topic grid
        topics_container = QWidget()
        from PyQt5.QtWidgets import QGridLayout
        topics_layout = QGridLayout(topics_container)
        topics_layout.setContentsMargins(20, 20, 20, 20)
        topics_layout.setSpacing(25)  # Increased spacing
        
        # Get topics for this module/difficulty
        topics = self.paths.get_topics(self.current_module, difficulty)
        
        # Calculate screen-based sizing
        screen_width = self.width()
        # Determine number of columns based on screen width
        if screen_width < 800:
            cols = 2
        elif screen_width < 1200:
            cols = 3
        else:
            cols = 4
        
        # Show topics in a grid
        for i, topic_item in enumerate(topics):
            # Handle both string and tuple formats
            if isinstance(topic_item, tuple) and len(topic_item) == 2:
                topic_dir, topic_display = topic_item
            else:
                # If just a string, use it for both
                topic_dir = topic_display = topic_item
                
            # Check completion status
            completed = self.is_topic_completed(self.current_module, self.current_difficulty, topic_dir)
            
            # Create topic card
            topic_card = TopicCard(topic_display, completed)
            topic_card.set_click_handler(lambda d=topic_dir, t=topic_display: self.select_topic(d, t))
            
            # Add to grid
            row = i // cols
            col = i % cols
            topics_layout.addWidget(topic_card, row, col)
        
        # Make sure columns have equal width
        for i in range(cols):
            topics_layout.setColumnStretch(i, 1)
        
        # Add the container to the scroll area
        scroll_area.setWidget(topics_container)
        
        # Add the scroll area to the content layout
        self.content_layout.addWidget(scroll_area, 1)  # Use stretch=1

        # Update status
        if difficulty:
            self.status_label.setText(f"Module: {self.current_module}, Difficulty: {difficulty} - Select a topic")
        else:
            self.status_label.setText(f"Module: {self.current_module} - Select a topic")
    
    def select_topic(self, topic_dir, topic_display=None):
        """
        Handle topic selection and navigate to questions page.
        
        Args:
            topic_dir (str): The topic directory name
            topic_display (str, optional): The display name for the topic
        """
        # Store both the directory name and display name
        self.current_topic = topic_dir
        self.current_topic_display = topic_display if topic_display else topic_dir
        self.show_questions_page()

    def show_questions_page(self):
        """
        Display the questions page for the current topic with improved layout.
        Shows all questions and associated media files for the topic.
        """
        self.clear_content_frame()
        self.current_page = "questions"

        # Get topic display name (falls back to directory name if not set)
        topic_display = self.current_topic_display or self.current_topic

        # Update breadcrumb
        if self.current_difficulty:
            self.breadcrumb_label.setText(f"Main Menu > {self.current_module} > {self.current_difficulty} > {topic_display}")
        else:
            self.breadcrumb_label.setText(f"Main Menu > {self.current_module} > {topic_display}")

        # Add back button with improved styling
        back_btn = self.create_back_button("Back to Topics", 
                    lambda: self.show_topics_page(self.current_difficulty))
        self.nav_buttons_panel.layout().addWidget(back_btn)

        # Create title with larger font
        if self.current_difficulty:
            page_title = f"Questions for {self.current_module} - {self.current_difficulty} - {topic_display}"
        else:
            page_title = f"Questions for {self.current_module} - {topic_display}"
            
        title_label = create_styled_label(
            page_title, 
            font_size=24, 
            font_weight="bold",
            color="#0067C5",
            alignment=Qt.AlignCenter
        )
        self.content_layout.addWidget(title_label)
        
        # Create a splitter for the main content
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Questions with improved styling
        questions_container = QWidget()
        questions_layout = QVBoxLayout(questions_container)
        questions_layout.setContentsMargins(15, 15, 15, 15)  # Increased margins
        questions_layout.setSpacing(15)  # Increased spacing
        
        # Add questions section title with larger font
        questions_title = create_styled_label(
            "Questions", 
            font_size=20, 
            font_weight="bold",
            color="#0067C5",
            alignment=Qt.AlignCenter
        )
        questions_layout.addWidget(questions_title)
        
        # Create scroll area for questions
        questions_scroll = QScrollArea()
        questions_scroll.setWidgetResizable(True)
        questions_scroll.setFrameShape(QFrame.NoFrame)
        
        # Questions inner container
        questions_inner = QWidget()
        questions_inner_layout = QVBoxLayout(questions_inner)
        questions_inner_layout.setContentsMargins(5, 5, 5, 5)
        questions_inner_layout.setSpacing(20)  # Increased spacing
        
        # Get questions for this topic
        questions = self.paths.get_questions(
            self.current_module, 
            self.current_difficulty, 
            self.current_topic
        )
        
        # Dictionary to store question widgets references
        self.question_widgets = {}
        
        # Display questions
        for i, (q_type, q_file) in enumerate(questions):
            self.display_question_item(questions_inner_layout, i, q_type, q_file)
        
        # Add stretch to push questions to the top
        questions_inner_layout.addStretch(1)
        
        # Set up scroll area
        questions_scroll.setWidget(questions_inner)
        questions_layout.addWidget(questions_scroll)
        
        # Add questions to splitter
        content_splitter.addWidget(questions_container)
        
        # Right side: Topic Resources/Media
        # Get all resources for this topic
        topic_resources = self.get_topic_resources()
        
        if topic_resources:
            resources_container = QWidget()
            resources_layout = QVBoxLayout(resources_container)
            resources_layout.setContentsMargins(15, 15, 15, 15)  # Increased margins
            resources_layout.setSpacing(15)  # Increased spacing
            
            # Add resources section title with larger font
            resources_title = create_styled_label(
                "Topic Resources", 
                font_size=20, 
                font_weight="bold",
                color="#0067C5",
                alignment=Qt.AlignCenter
            )
            resources_layout.addWidget(resources_title)
            
            # Create scroll area for resources
            resources_scroll = QScrollArea()
            resources_scroll.setWidgetResizable(True)
            resources_scroll.setFrameShape(QFrame.NoFrame)
            
            # Resources inner container
            resources_inner = QWidget()
            resources_inner_layout = QVBoxLayout(resources_inner)
            resources_inner_layout.setContentsMargins(5, 5, 5, 5)
            resources_inner_layout.setSpacing(15)  # Increased spacing
            
            # Display resources
            for i, resource_info in enumerate(topic_resources):
                self.display_resource_item(resources_inner_layout, i, *resource_info)
            
            # Add stretch to push resources to the top
            resources_inner_layout.addStretch(1)
            
            # Set up scroll area
            resources_scroll.setWidget(resources_inner)
            resources_layout.addWidget(resources_scroll)
            
            # Add resources to splitter
            content_splitter.addWidget(resources_container)
            
            # Set split sizes (60% questions, 40% resources)
            content_splitter.setSizes([600, 400])
        
        # Add the splitter to the content layout
        self.content_layout.addWidget(content_splitter, 1)
        
        # Update status bar
        if self.current_difficulty:
            self.status_label.setText(f"Module: {self.current_module}, Difficulty: {self.current_difficulty}, Topic: {topic_display}")
        else:
            self.status_label.setText(f"Module: {self.current_module}, Topic: {topic_display}")
    
    def display_question_item(self, parent_layout, index, q_type, q_file):
        """
        Display a single question item with improved readability.
        
        Args:
            parent_layout: Parent layout to add the question to
            index (int): Question index
            q_type (str): Question type
            q_file (str): Question file name
        """
        from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
        
        # Create question panel
        question_panel = QFrame()
        question_panel.setFrameShape(QFrame.StyledPanel)
        question_panel.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            border: 1px solid #9EA2A4;
            padding: 15px;  /* Increased padding */
        """)
        
        question_layout = QVBoxLayout(question_panel)
        question_layout.setSpacing(10)  # Increased spacing between elements
        
        # Add header with question number and identifier
        header_layout = QHBoxLayout()
        
        # Question number
        question_num = QLabel(f"Q{index+1}:")
        question_num.setStyleSheet("""
            color: #0067C5;
            font-weight: bold;
            font-size: 25px;  /* Increased font size */
        """)
        header_layout.addWidget(question_num)
        
        # Get the question identifier (first character/letter)
        identifier = q_file.replace("PS_", "").split('_')[0] if '_' in q_file else q_file[0]
        
        # Identifier
        identifier_label = QLabel(f"[{identifier}]")
        identifier_label.setStyleSheet("""
            color: #636A6A;
            font-size: 12px;  /* Increased font size */
        """)
        header_layout.addWidget(identifier_label)
        
        header_layout.addStretch()
        question_layout.addLayout(header_layout)
        
        # Load question content
        question_content, actual_question = self.paths.load_question_content(
            self.current_module, 
            self.current_difficulty,
            self.current_topic,
            q_type,
            q_file
        )
        
        # Add question text with larger font
        text_label = QLabel(question_content)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("""
            background-color: white;
            border-radius: 5px;
            padding: 15px;  /* Increased padding */
            font-size: 30px;  /* Increased font size */
            line-height: 1.4;  /* Add line height for better readability */
        """)
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # Make text selectable
        question_layout.addWidget(text_label)
        
        # Add answer section
        answer_layout = QHBoxLayout()
        
        # Answer label with larger font
        answer_label = QLabel("Answer:")
        answer_label.setStyleSheet("""
            color: #0067C5;
            font-weight: bold;
            font-size: 30px;  /* Increased font size */
        """)
        answer_layout.addWidget(answer_label)
        
        # Answer entry with larger height and font
        answer_entry = QLineEdit()
        answer_entry.setMinimumHeight(40)  # Taller input field
        answer_entry.setStyleSheet("""
            border: 1px solid #9EA2A4;
            border-radius: 5px;
            padding: 10px;  /* Increased padding */
            font-size: 25px;  /* Increased font size */
        """)
        
        # Connect Enter key to submit the answer
        answer_entry.returnPressed.connect(
            lambda: self.check_answer(q_file, answer_entry.text())
        )
        
        answer_layout.addWidget(answer_entry)
        
        question_layout.addLayout(answer_layout)
        
        # Add buttons
        buttons_layout = QHBoxLayout()
        
        # Submit button with larger size
        submit_button = RoundedPushButton("Submit")
        submit_button.setMinimumHeight(40)  # Taller button
        submit_button.setFont(QFont("Segoe UI", 12))  # Larger font
        submit_button.clicked.connect(
            lambda checked, qf=q_file, ae=answer_entry:
            self.check_answer(qf, ae.text())
        )
        buttons_layout.addWidget(submit_button)
        
        # Only show hint button for certain difficulties
        show_hint = self.current_difficulty in ["Beginner", "Intermediate", "Advanced"]
        
        if show_hint:
            # Create hint button with larger size
            hint_button = RoundedPushButton("Hint")
            hint_button.setMinimumHeight(40)  # Taller button
            hint_button.setFont(QFont("Segoe UI", 12))  # Larger font
            hint_button.clicked.connect(lambda checked, qf=q_file: self.show_hint(qf))
            
            # Set appropriate color based on difficulty
            hint_button.set_color(self.get_difficulty_color(self.current_difficulty))
            buttons_layout.addWidget(hint_button)
        
        # Add spacing between buttons
        buttons_layout.setSpacing(15)
        question_layout.addLayout(buttons_layout)
        
        # Add result label (initially hidden)
        result_label = QLabel()
        result_label.setStyleSheet("font-size: 25px;")  # Increased font size
        result_label.setVisible(False)
        question_layout.addWidget(result_label)
        
        # Store the widgets for this question
        self.question_widgets[q_file] = {
            'entry': answer_entry,
            'submit_button': submit_button,
            'result_label': result_label,
            'actual_question': actual_question,
            'identifier': identifier,
            'panel': question_panel
        }
        
        # Check if this question is already completed
        is_completed = self.progress.is_question_completed(
            self.current_module, 
            self.current_difficulty, 
            self.current_topic, 
            q_file
        )
        
        if is_completed:
            # Show completed status
            result_label.setText("✓ Correct!")
            result_label.setStyleSheet("color: #007F3E; font-weight: bold; font-size: 25px;")
            result_label.setVisible(True)
            
            # Disable answer entry and submit button
            answer_entry.setDisabled(True)
            submit_button.setDisabled(True)
        
        # Add to parent layout
        parent_layout.addWidget(question_panel)

    def display_resource_item(self, parent_layout, index, resource_type, resource_path, file_name):
        """
        Display a resource item in the resources panel with improved visibility.
        
        Args:
            parent_layout: Parent layout to add the resource to
            index (int): Resource index
            resource_type (str): Type of resource (image, pdf, file, etc.)
            resource_path (str): Path to the resource file
            file_name (str): Name of the file
        """
        from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel
        
        # Create resource panel
        resource_panel = QFrame()
        resource_panel.setFrameShape(QFrame.StyledPanel)
        resource_panel.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            border: 1px solid #9EA2A4;
            padding: 15px;  /* Increased padding */
            margin-bottom: 15px;  /* Add margin between resources */
        """)
        
        resource_layout = QVBoxLayout(resource_panel)
        resource_layout.setContentsMargins(10, 10, 10, 10)
        resource_layout.setSpacing(10)  # Increased spacing between elements
        
        # Resource header with icon and title
        header_layout = QHBoxLayout()
        
        # Icon based on resource type with larger size
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)  # Larger icon
        icon_label.setStyleSheet("font-size: 20px;")  # Larger emoji
        
        # Use resource type to determine icon
        icon_text = "📄"  # Default file icon
        if resource_type == "image":
            icon_text = "🖼️"
        elif resource_type == "pdf":
            icon_text = "📕"
        elif resource_type == "text":
            icon_text = "📝"
        elif resource_type == "video":
            icon_text = "🎬"
            
        icon_label.setText(icon_text)
        icon_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # Resource title with larger font
        title_label = QLabel(file_name)
        title_label.setStyleSheet("""
            color: #0067C5;
            font-weight: bold;
            font-size: 25px;  /* Increased font size */
        """)
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, 1)  # Give stretch factor to use available space
        
        resource_layout.addLayout(header_layout)
        
        # Add thumbnail for images if possible - make it much larger
        if resource_type == "image":
            try:
                # Create thumbnail
                thumbnail_label = QLabel()
                thumbnail_label.setAlignment(Qt.AlignCenter)
                pixmap = QPixmap(resource_path)
                
                # Scale to a larger thumbnail size
                if not pixmap.isNull():
                    max_width = 350  # Increased max width
                    max_height = 250  # Increased max height
                    pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    thumbnail_label.setPixmap(pixmap)
                    resource_layout.addWidget(thumbnail_label)
            except Exception as e:
                logger.error(f"Error creating thumbnail: {str(e)}")
        
        # Add file type label with larger font
        type_label = QLabel(f"Type: {resource_type.capitalize()}")
        type_label.setStyleSheet("""
            color: #636A6A;
            font-size: 25px;  /* Increased font size */
        """)
        resource_layout.addWidget(type_label)
        
        # Add buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)  # Increase spacing between buttons
        
        # View button with larger size
        view_button = RoundedPushButton("View")
        view_button.setMinimumHeight(40)  # Taller button
        view_button.setFont(QFont("Segoe UI", 12))  # Larger font
        view_button.clicked.connect(
            lambda checked, rt=resource_type, rp=resource_path: 
            self.open_resource(rt, rp)
        )
        view_button.set_color("#0067C5")  # Use blue for view button
        buttons_layout.addWidget(view_button)
        
        # Download button with larger size
        download_button = RoundedPushButton("Download")
        download_button.setMinimumHeight(40)  # Taller button
        download_button.setFont(QFont("Segoe UI", 12))  # Larger font
        download_button.clicked.connect(
            lambda checked, rp=resource_path: self.save_resource(rp)
        )
        download_button.set_color("#007F3E")  # Use green for download button
        buttons_layout.addWidget(download_button)
        
        resource_layout.addLayout(buttons_layout)
        
        # Add to parent layout
        parent_layout.addWidget(resource_panel)

    def check_answer(self, question_file, user_answer):
        """
        Check if a user's answer is correct, supporting multiple correct answers.
        
        Args:
            question_file (str): The question file name
            user_answer (str): The user's submitted answer
        """
        if not user_answer.strip():
            QMessageBox.information(self, "Answer", "Please enter an answer.")
            return
        
        # Get the correct answer using the path manager
        correct_answer = self.paths.get_correct_answer(
            self.current_module,
            self.current_difficulty,
            self.current_topic,
            question_file
        )
        
        if correct_answer is None:
            QMessageBox.information(self, "Answer", "No answer file found for this question.")
            return
        
        # Process user answer - trim whitespace and convert to lowercase
        user_answer = user_answer.lower().strip()
        
        # Check if the answer is correct, handling multiple possible answers separated by |
        correct_options = [option.lower().strip() for option in correct_answer.split('|')]
        is_correct = user_answer in correct_options
        
        # Record this attempt in the stats
        self.progress.record_attempt(
            self.current_module,
            self.current_difficulty,
            self.current_topic,
            question_file,
            is_correct
        )
        
        # Get the widgets for this question
        widgets = self.question_widgets.get(question_file, {})
        result_label = widgets.get('result_label')
        question_panel = widgets.get('panel')
        answer_entry = widgets.get('entry')
        submit_button = widgets.get('submit_button')
        
        if result_label is None:
            return
        
        if is_correct:
            # Update result label to show success
            result_label.setText("✓ Correct!")
            result_label.setStyleSheet("color: #007F3E; font-weight: bold;")
            result_label.setVisible(True)
            
            # Disable the input field and submit button
            answer_entry.setDisabled(True)
            submit_button.setDisabled(True)
            
            # Mark this question as completed
            self.progress.mark_question_completed(
                self.current_module,
                self.current_difficulty,
                self.current_topic,
                question_file
            )
            
            QMessageBox.information(self, "Correct!", "Your answer is correct!")
        else:
            # Update result label to show failure
            result_label.setText("✗ Incorrect. Try again.")
            result_label.setStyleSheet("color: #D32F2F; font-weight: bold;")
            result_label.setVisible(True)
        
        # Update the accuracy display after each attempt
        self.update_accuracy_display()
    
    def show_hint(self, question_file):
        """
        Show a hint for the specified question.
        
        Args:
            question_file (str): The question file name
        """
        # Get hint content
        hint_content = self.paths.get_hint_content(
            self.current_module,
            self.current_difficulty,
            self.current_topic,
            question_file
        )
        
        if hint_content:
            # Apply penalty based on difficulty level
            if self.current_difficulty == "Intermediate":
                # Record one incorrect attempt
                self.progress.record_attempt(
                    self.current_module,
                    self.current_difficulty,
                    self.current_topic,
                    question_file,
                    False
                )
                hint_title = "Hint (Counts as 1 incorrect attempt)"
            elif self.current_difficulty == "Advanced":
                # Record three incorrect attempts
                for _ in range(3):
                    self.progress.record_attempt(
                        self.current_module,
                        self.current_difficulty,
                        self.current_topic,
                        question_file,
                        False
                    )
                hint_title = "Hint (Counts as 3 incorrect attempts)"
            else:
                # No penalty for Beginner
                hint_title = "Hint"
            
            # Show hint in message box
            QMessageBox.information(self, hint_title, hint_content)
            
            # Update accuracy display
            self.update_accuracy_display()
        else:
            QMessageBox.information(self, "Hint", "No hint available for this question.")

    def is_topic_completed(self, module, difficulty, topic):
        """
        Check if all questions in a topic are completed.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str or tuple): The topic name or (directory, display_name) tuple
            
        Returns:
            bool: True if all questions in the topic are completed, False otherwise
        """
        # Handle case where topic might be a tuple from get_topics (dir_name, display_name)
        if isinstance(topic, tuple) and len(topic) == 2:
            # Extract just the directory name
            topic_dir = topic[0]
        else:
            # Use topic as is (backward compatibility)
            topic_dir = topic
        
        # Get all questions for this topic
        questions = self.paths.get_questions(module, difficulty, topic_dir)
        
        # If there are no questions, the topic is not completed
        if not questions:
            return False
            
        # Check if all questions are completed
        for q_type, q_file in questions:
            if not self.progress.is_question_completed(module, difficulty, topic_dir, q_file):
                return False
                
        return True

    def is_difficulty_completed(self, module, difficulty):
        """
        Check if all topics in a difficulty are completed.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level
            
        Returns:
            bool: True if all topics in the difficulty are completed, False otherwise
        """
        # Get all topics for this module and difficulty
        topics = self.paths.get_topics(module, difficulty)
        
        # If there are no topics, the difficulty is not completed
        if not topics:
            return False
            
        # Check if all topics are completed
        for topic in topics:
            if not self.is_topic_completed(module, difficulty, topic):
                return False
                
        return True

    def is_module_completed(self, module):
        """
        Check if a module is completed.
        
        Args:
            module (str): The module name
            
        Returns:
            bool: True if the module is completed, False otherwise
        """
        if not module:
            logger.error("Module name cannot be None when checking completion")
            return False
            
        if module == "Getting Started":
            # Getting Started has no difficulties
            topics = self.paths.get_topics(module, None)
            
            # If there are no topics, the module is not completed
            if not topics:
                return False
                
            # Check if all topics are completed
            for topic in topics:
                if not self.is_topic_completed(module, None, topic):
                    return False
                    
            return True
        else:
            # Regular module with difficulties
            # Check if all difficulties are completed
            for difficulty in self.difficulties:
                # Safely get the difficulty path with validation
                difficulty_path = self.paths.get_difficulty_path(module, difficulty)
                
                # Only check completion if this difficulty exists for this module
                if difficulty_path and os.path.exists(difficulty_path):
                    if not self.is_difficulty_completed(module, difficulty):
                        return False
            
            # Return True only if at least one difficulty was found and all are completed
            return True
        
    def refresh_all(self):
        """Refresh the current page based on the current state."""
        from PyQt5.QtWidgets import QMessageBox
        
        # Update the path label
        if self.paths.base_directory:
            self.set_path_label(self.paths.base_directory)
        else:
            self.set_path_label("Not Selected")
        
        # Update accuracy display
        self.update_accuracy_display()
        
        # Try to reload modules if we have a base directory
        if self.paths.base_directory and os.path.exists(self.paths.base_directory):
            self.load_modules()
        
        # Refresh the current page
        if self.current_page == "modules":
            self.show_modules_page()
        elif self.current_page == "difficulties":
            self.show_difficulties_page()
        elif self.current_page == "topics":
            self.show_topics_page(self.current_difficulty)
        elif self.current_page == "questions":
            self.show_questions_page()
        
        # Show a status message
        self.status_label.setText("UI refreshed")
        logger.info("UI refreshed")
    
    def show_about(self):
        """Show about dialog with application information."""
        QMessageBox.about(
            self, "About",
            "Islander-CTF Training & Testing Application\n"
            "Version 1.0\n\n"
            "Created for and by the Islander Cyber Society"
        )

    def show_help(self):
        """Show help dialog with usage instructions."""
        help_text = """
        CTF Challenge Navigation:

        If you are new to CTF's start with Getting Started
        1. Otherwise, select a module from the main menu
        2. Choose a difficulty level
        3. Select a topic to work on
        4. Attempt to solve the questions within each topic
        5. Use hints only when necessary
        6. Your progress is automatically saved
        7. View your overall progress from the Progress menu

        Remember, the goal is to learn and have fun!
        """
        QMessageBox.information(self, "Help", help_text)
    
    def reset_progress(self):
        """Reset all progress after confirmation."""
        reply = QMessageBox.question(
            self, "Confirm Reset", 
            "Are you sure you want to reset all progress? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.progress.reset()
            QMessageBox.information(self, "Reset Complete", "Your progress has been reset.")
            
            # Refresh the current page
            self.refresh_all()

    def create_menus(self):
        """Create the application menus."""
        from PyQt5.QtWidgets import QAction, QMenu, QMenuBar
        
        # Create menu bar
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # Add 'Open CTF Directory' action
        open_dir_action = QAction("Open CTF Directory", self)
        open_dir_action.setShortcut("Ctrl+O")
        open_dir_action.triggered.connect(self.show_directory_dialog)
        file_menu.addAction(open_dir_action)
        
        # Add 'Add New CTF Directory' action
        add_dir_action = QAction("Add New CTF Directory", self)
        add_dir_action.triggered.connect(self.add_ctf_directory)
        file_menu.addAction(add_dir_action)
        
        # Add separator
        file_menu.addSeparator()
        
        # Add 'Exit' action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        
        # Add 'Reset Progress' action
        reset_action = QAction("Reset Progress", self)
        reset_action.triggered.connect(self.reset_progress)
        edit_menu.addAction(reset_action)
        
        # Progress menu
        progress_menu = menu_bar.addMenu("Progress")
        
        # Add 'View Overall Progress' action
        view_progress_action = QAction("View Overall Progress", self)
        # Connect to the show_overall_progress method
        view_progress_action.triggered.connect(self.show_overall_progress)
        progress_menu.addAction(view_progress_action)
        
        # Add 'Refresh' action
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all)
        progress_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        # Add 'Help' action
        help_action = QAction("Help", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        # Add 'About' action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_title_bar(self):
        """Create a more prominent application title bar with centered title."""
        title_container = QWidget()
        title_container.setStyleSheet("""
            background-color: #0067C5;
            border-bottom: 1px solid #001A31;
            padding: 15px;
        """)
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add a stretch to push the title to the center
        title_layout.addStretch(1)
        
        # Title text with larger font
        title_label = QLabel("Islander Cyber Society CTF")
        title_label.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
            padding: 5px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_label)
        
        # Add another stretch to keep the title centered
        title_layout.addStretch(1)
        
        # Add to main layout
        self.main_layout.addWidget(title_container)

    def calculate_module_completion(self, module):
        """
        Calculate the completion percentage for a module.
        
        Args:
            module (str): The module name
            
        Returns:
            float: Percentage of module completion (0-100)
        """
        if not module:
            return 0
        
        total_questions = 0
        completed_questions = 0
        
        # For "Getting Started" which has no difficulties
        if module == "Getting Started":
            # Get topics for this module
            topics = self.paths.get_topics(module, None)
            
            # Count questions for each topic
            for topic in topics:
                # Get questions for this topic
                topic_dir = topic[0] if isinstance(topic, tuple) and len(topic) == 2 else topic
                questions = self.paths.get_questions(module, None, topic_dir)
                
                total_questions += len(questions)
                
                # Count completed questions
                for q_type, q_file in questions:
                    if self.progress.is_question_completed(module, None, topic_dir, q_file):
                        completed_questions += 1
        else:
            # Regular module with difficulties
            for difficulty in self.difficulties:
                # Check if this difficulty exists for this module
                difficulty_path = self.paths.get_difficulty_path(module, difficulty)
                if not difficulty_path or not os.path.exists(difficulty_path):
                    continue
                    
                # Get topics for this difficulty
                topics = self.paths.get_topics(module, difficulty)
                
                # Count questions for each topic
                for topic in topics:
                    # Get questions for this topic
                    topic_dir = topic[0] if isinstance(topic, tuple) and len(topic) == 2 else topic
                    questions = self.paths.get_questions(module, difficulty, topic_dir)
                    
                    total_questions += len(questions)
                    
                    # Count completed questions
                    for q_type, q_file in questions:
                        if self.progress.is_question_completed(module, difficulty, topic_dir, q_file):
                            completed_questions += 1
        
        # Calculate percentage (avoid division by zero)
        if total_questions == 0:
            return 0
        
        # Return as a float (this is fine as long as setValue gets an int)
        return (completed_questions / total_questions) * 100
    
    def create_back_button(self, text, callback):
        """
        Create a standardized back button with improved styling.
        
        Args:
            text (str): Button text (e.g., "Back to Modules")
            callback: Function to call when clicked
            
        Returns:
            RoundedPushButton: Styled back button
        """
        back_btn = RoundedPushButton(text)
        back_btn.setMinimumHeight(40)  # Make button taller
        back_btn.setMinimumWidth(150)  # Ensure minimum width
        back_btn.setFont(QFont("Segoe UI", 11))  # Larger font
        
        # Use a distinct color for back buttons
        back_btn.set_color("#505050")  # Dark gray
        back_btn.set_hover_color("#707070")  # Lighter gray on hover
        
        back_btn.clicked.connect(callback)
        return back_btn
    
    def get_question_resources(self, question_file):
        """
        Get resources (images, PDFs, etc.) associated with a question.
        
        Args:
            question_file (str): The question file name
            
        Returns:
            list: List of tuples (resource_type, resource_path)
        """
        resources = []
        
        # Extract base name for the question (remove extension if present)
        base_name = os.path.splitext(question_file)[0]
        
        # Get resources directory for this topic
        topic_path = self.paths.get_topic_path(
            self.current_module,
            self.current_difficulty,
            self.current_topic
        )
        
        if not topic_path:
            return resources
        
        # Check if a Resources directory exists
        resources_dir = os.path.join(topic_path, "Resources")
        if not os.path.exists(resources_dir) or not os.path.isdir(resources_dir):
            # Try alternative "Files" directory
            resources_dir = os.path.join(topic_path, "Files")
            if not os.path.exists(resources_dir) or not os.path.isdir(resources_dir):
                return resources
        
        # Look for resource files with the same base name as the question
        try:
            for item in os.listdir(resources_dir):
                item_path = os.path.join(resources_dir, item)
                
                if os.path.isfile(item_path):
                    item_base = os.path.splitext(item)[0]
                    item_ext = os.path.splitext(item)[1].lower()
                    
                    # Check if the file name is related to the question
                    if item_base == base_name or item_base.startswith(base_name + "_"):
                        # Determine resource type based on extension
                        resource_type = "file"  # Default type
                        
                        if item_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                            resource_type = "image"
                        elif item_ext == '.pdf':
                            resource_type = "pdf"
                        elif item_ext in ['.txt', '.text']:
                            resource_type = "text"
                        
                        resources.append((resource_type, item_path))
                        
        except Exception as e:
            logger.error(f"Error scanning resources: {str(e)}")
        
        return resources

    def open_resource(self, resource_type, resource_path):
        """
        Open a resource file for viewing or download with improved UI.
        
        Args:
            resource_type (str): Type of resource (image, pdf, file, etc.)
            resource_path (str): Path to the resource file
        """
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QFileDialog, QScrollArea
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtCore import Qt, QUrl
        import shutil
        
        if not os.path.exists(resource_path):
            QMessageBox.warning(self, "Resource Error", "Resource file not found.")
            return
        
        if resource_type == "image":
            # Create a dialog to display the image
            dialog = QDialog(self)
            dialog.setWindowTitle("Image Viewer")
            dialog.resize(1000, 800)  # Larger initial size
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
            
            # Create scroll area for image
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.NoFrame)
            
            # Image label
            image_label = QLabel()
            pixmap = QPixmap(resource_path)
            
            # For very large images, scale down but preserve aspect ratio
            screen_size = self.screen().size()
            max_width = screen_size.width() * 0.8  # 80% of screen width
            max_height = screen_size.height() * 0.8  # 80% of screen height
            
            if pixmap.width() > max_width or pixmap.height() > max_height:
                pixmap = pixmap.scaled(int(max_width), int(max_height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            
            # Add image to scroll area
            scroll_area.setWidget(image_label)
            layout.addWidget(scroll_area, 1)  # Give it stretch factor
            
            # File information
            file_info = QLabel(f"File: {os.path.basename(resource_path)}")
            file_info.setStyleSheet("font-size: 12pt;")
            layout.addWidget(file_info)
            
            # Add button box with Save button
            button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
            button_box.button(QDialogButtonBox.Save).setText("Download")
            button_box.button(QDialogButtonBox.Save).setStyleSheet("font-size: 12pt; padding: 5px 15px;")
            button_box.button(QDialogButtonBox.Close).setStyleSheet("font-size: 12pt; padding: 5px 15px;")
            button_box.rejected.connect(dialog.reject)
            button_box.button(QDialogButtonBox.Save).clicked.connect(
                lambda: self.save_resource(resource_path)
            )
            layout.addWidget(button_box)
            
            dialog.exec_()
            
        elif resource_type == "pdf":
            try:
                # Check if PDF viewer is available
                if not hasattr(self, 'pdf_viewer_available'):
                    try:
                        from PyQt5.QtWebEngineWidgets import QWebEngineView
                        self.pdf_viewer_available = True
                    except ImportError:
                        self.pdf_viewer_available = False
                
                if self.pdf_viewer_available:
                    # Create a dialog to display the PDF using QWebEngineView
                    dialog = QDialog(self)
                    dialog.setWindowTitle("PDF Viewer")
                    dialog.resize(1000, 800)  # Larger initial size
                    
                    layout = QVBoxLayout(dialog)
                    layout.setContentsMargins(10, 10, 10, 10)
                    layout.setSpacing(10)
                    
                    # File information
                    file_info = QLabel(f"File: {os.path.basename(resource_path)}")
                    file_info.setStyleSheet("font-size: 12pt;")
                    layout.addWidget(file_info)
                    
                    # PDF viewer
                    from PyQt5.QtWebEngineWidgets import QWebEngineView
                    pdf_view = QWebEngineView()
                    
                    # Set a minimum size for the viewer
                    pdf_view.setMinimumSize(800, 600)
                    
                    # Convert file path to URL
                    file_url = QUrl.fromLocalFile(resource_path)
                    pdf_view.load(file_url)
                    layout.addWidget(pdf_view, 1)  # Give it stretch factor
                    
                    # Add button box with Save button
                    button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
                    button_box.button(QDialogButtonBox.Save).setText("Download")
                    button_box.button(QDialogButtonBox.Save).setStyleSheet("font-size: 12pt; padding: 5px 15px;")
                    button_box.button(QDialogButtonBox.Close).setStyleSheet("font-size: 12pt; padding: 5px 15px;")
                    button_box.rejected.connect(dialog.reject)
                    button_box.button(QDialogButtonBox.Save).clicked.connect(
                        lambda: self.save_resource(resource_path)
                    )
                    layout.addWidget(button_box)
                    
                    dialog.exec_()
                else:
                    # PDF viewer not available, just save the file
                    QMessageBox.information(self, "PDF Viewer", 
                                        "PDF viewer component not available. You can download the file instead.")
                    self.save_resource(resource_path)
            except Exception as e:
                QMessageBox.warning(self, "PDF Viewer Error", 
                                f"Could not open PDF. Error: {str(e)}\n\nYou can still download the file.")
                self.save_resource(resource_path)
                
        elif resource_type == "text":
            try:
                # Read text file
                with open(resource_path, 'r') as f:
                    text_content = f.read()
                
                # Create a dialog to display the text
                dialog = QDialog(self)
                dialog.setWindowTitle("Text Viewer")
                dialog.resize(900, 700)  # Larger initial size
                
                layout = QVBoxLayout(dialog)
                layout.setContentsMargins(10, 10, 10, 10)
                layout.setSpacing(10)
                
                # File information
                file_info = QLabel(f"File: {os.path.basename(resource_path)}")
                file_info.setStyleSheet("font-size: 12pt;")
                layout.addWidget(file_info)
                
                # Text display
                from PyQt5.QtWidgets import QTextEdit
                text_edit = QTextEdit()
                text_edit.setStyleSheet("font-size: 14pt; line-height: 1.5;")  # Larger font
                text_edit.setPlainText(text_content)
                text_edit.setReadOnly(True)
                layout.addWidget(text_edit, 1)  # Give it stretch factor
                
                # Add button box with Save button
                button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
                button_box.button(QDialogButtonBox.Save).setText("Download")
                button_box.button(QDialogButtonBox.Save).setStyleSheet("font-size: 12pt; padding: 5px 15px;")
                button_box.button(QDialogButtonBox.Close).setStyleSheet("font-size: 12pt; padding: 5px 15px;")
                button_box.rejected.connect(dialog.reject)
                button_box.button(QDialogButtonBox.Save).clicked.connect(
                    lambda: self.save_resource(resource_path)
                )
                layout.addWidget(button_box)
                
                dialog.exec_()
                
            except Exception as e:
                QMessageBox.warning(self, "Text Viewer Error", 
                            f"Could not open text file. Error: {str(e)}\n\nYou can still download the file.")
                self.save_resource(resource_path)
        
        else:
            # For other file types, just offer to save/download
            self.save_resource(resource_path)
        
    def save_resource(self, resource_path):
        """
        Save/download a resource file.
        
        Args:
            resource_path (str): Path to the resource file
        """
        import shutil
        from PyQt5.QtWidgets import QFileDialog
        
        # Get file name
        file_name = os.path.basename(resource_path)
        
        # Ask user where to save
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", file_name, "All Files (*.*)"
        )
        
        if save_path:
            try:
                # Copy the file to the selected location
                shutil.copy2(resource_path, save_path)
                QMessageBox.information(self, "File Saved", f"File saved to: {save_path}")
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Could not save file. Error: {str(e)}")

    def get_topic_resources(self):
        """
        Get all resource files for the current topic.
        
        Returns:
            list: List of tuples (resource_type, resource_path, file_name)
        """
        resources = []
        
        # Get topic path
        topic_path = self.paths.get_topic_path(
            self.current_module,
            self.current_difficulty,
            self.current_topic
        )
        
        if not topic_path:
            return resources
            
        # Check for resources in different potential directories
        resource_folders = ["Resources", "Files", "Media", "Documents"]
        
        for folder_name in resource_folders:
            resources_dir = os.path.join(topic_path, folder_name)
            
            if not os.path.exists(resources_dir) or not os.path.isdir(resources_dir):
                continue
                
            # Look for all files in this directory
            try:
                for item in os.listdir(resources_dir):
                    item_path = os.path.join(resources_dir, item)
                    
                    if os.path.isfile(item_path):
                        # Skip hidden files
                        if item.startswith('.'):
                            continue
                            
                        # Get file extension
                        file_name = os.path.basename(item_path)
                        item_ext = os.path.splitext(item)[1].lower()
                        
                        # Determine resource type based on extension
                        resource_type = "file"  # Default type
                        
                        if item_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']:
                            resource_type = "image"
                        elif item_ext == '.pdf':
                            resource_type = "pdf"
                        elif item_ext in ['.txt', '.text', '.md', '.rtf']:
                            resource_type = "text"
                        elif item_ext in ['.mp4', '.avi', '.mov', '.wmv']:
                            resource_type = "video"
                        
                        resources.append((resource_type, item_path, file_name))
            except Exception as e:
                logger.error(f"Error scanning resource directory {folder_name}: {str(e)}")
        
        # Sort resources by type and then by name
        resources.sort(key=lambda x: (x[0], x[2]))
        
        return resources
    
    def show_overall_progress(self):
        """
        Show a dialog with overall progress statistics.
        
        This displays completion percentages for all modules and overall accuracy statistics.
        """
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea, QFrame, QGridLayout, QProgressBar, QDialogButtonBox
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Overall Progress")
        dialog.resize(800, 600)  # Large initial size
        
        # Main layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title
        title_label = QLabel("CTF Training Progress")
        title_label.setStyleSheet("""
            color: #0067C5;
            font-weight: bold;
            font-size: 24px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Add overall statistics section
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.StyledPanel)
        stats_frame.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            border: 1px solid #9EA2A4;
            padding: 15px;
        """)
        
        stats_layout = QVBoxLayout(stats_frame)
        
        # Get overall stats
        overall_stats = self.progress.get_overall_stats()
        
        # Create stats header
        stats_header = QLabel("Overall Statistics")
        stats_header.setStyleSheet("""
            color: #0067C5;
            font-weight: bold;
            font-size: 20px;
        """)
        stats_header.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(stats_header)
        
        # Create grid for stats
        stats_grid = QGridLayout()
        stats_grid.setColumnStretch(0, 1)
        stats_grid.setColumnStretch(1, 2)
        
        # Add total attempts row
        stats_grid.addWidget(QLabel("Total Attempts:"), 0, 0)
        total_attempts_label = QLabel(str(overall_stats['total_attempts']))
        total_attempts_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        stats_grid.addWidget(total_attempts_label, 0, 1)
        
        # Add correct attempts row
        stats_grid.addWidget(QLabel("Correct Attempts:"), 1, 0)
        correct_attempts_label = QLabel(str(overall_stats['correct_attempts']))
        correct_attempts_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        stats_grid.addWidget(correct_attempts_label, 1, 1)
        
        # Add accuracy row
        stats_grid.addWidget(QLabel("Overall Accuracy:"), 2, 0)
        
        if overall_stats['total_attempts'] > 0:
            accuracy = overall_stats['accuracy'] * 100
            accuracy_label = QLabel(f"{accuracy:.1f}%")
            # Set color based on accuracy
            if accuracy >= 80:
                accuracy_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #007F3E;")  # Green
            elif accuracy >= 60:
                accuracy_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #FFA500;")  # Orange
            else:
                accuracy_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #D32F2F;")  # Red
        else:
            accuracy_label = QLabel("N/A")
            accuracy_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        stats_grid.addWidget(accuracy_label, 2, 1)
        
        # Add progress bar
        if overall_stats['total_attempts'] > 0:
            accuracy_bar = QProgressBar()
            accuracy_bar.setRange(0, 100)
            accuracy_bar.setValue(int(overall_stats['accuracy'] * 100))
            accuracy_bar.setTextVisible(False)
            accuracy_bar.setFixedHeight(15)
            accuracy_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 7px;
                    background: #F0F0F0;
                }
                QProgressBar::chunk {
                    border-radius: 7px;
                    background: #007F3E;
                }
            """)
            stats_grid.addWidget(accuracy_bar, 3, 0, 1, 2)
        
        stats_layout.addLayout(stats_grid)
        main_layout.addWidget(stats_frame)
        
        # Create a scroll area for modules progress
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Container for modules progress
        modules_container = QWidget()
        modules_layout = QVBoxLayout(modules_container)
        modules_layout.setSpacing(15)
        
        # Add modules progress header
        modules_header = QLabel("Module Completion")
        modules_header.setStyleSheet("""
            color: #0067C5;
            font-weight: bold;
            font-size: 20px;
        """)
        modules_header.setAlignment(Qt.AlignCenter)
        modules_layout.addWidget(modules_header)
        
        # Calculate and display progress for each module
        for module in sorted(self.modules):
            # Create module frame
            module_frame = QFrame()
            module_frame.setFrameShape(QFrame.StyledPanel)
            module_frame.setStyleSheet("""
                background-color: white;
                border-radius: 10px;
                border: 1px solid #9EA2A4;
                padding: 10px;
            """)
            
            module_layout = QVBoxLayout(module_frame)
            
            # Module title
            module_title = QLabel(module)
            module_title.setStyleSheet("""
                font-weight: bold;
                font-size: 18px;
            """)
            module_layout.addWidget(module_title)
            
            # Calculate completion percentage
            completion_percentage = self.calculate_module_completion(module)
            
            # Module stats layout
            module_stats_layout = QHBoxLayout()
            
            # Module completion percentage
            percentage_label = QLabel(f"{completion_percentage:.1f}% Complete")
            percentage_label.setStyleSheet("""
                font-size: 16px;
                padding-right: 10px;
            """)
            module_stats_layout.addWidget(percentage_label)
            
            # Check if completed
            completed = self.is_module_completed(module)
            if completed:
                completed_label = QLabel("✓ Completed")
                completed_label.setStyleSheet("""
                    color: #007F3E;
                    font-weight: bold;
                    font-size: 16px;
                """)
                module_stats_layout.addWidget(completed_label)
            
            module_stats_layout.addStretch()
            module_layout.addLayout(module_stats_layout)
            
            # Module progress bar
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(int(completion_percentage))
            progress_bar.setTextVisible(False)
            progress_bar.setFixedHeight(15)
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 7px;
                    background: #F0F0F0;
                }
                QProgressBar::chunk {
                    border-radius: 7px;
                    background: #007F3E;
                }
            """)
            module_layout.addWidget(progress_bar)
            
            # Get module accuracy
            module_stats = self.progress.get_module_stats(module)
            
            if module_stats['total_attempts'] > 0:
                # Display accuracy for this module
                accuracy_layout = QHBoxLayout()
                
                accuracy_text = QLabel("Accuracy:")
                accuracy_layout.addWidget(accuracy_text)
                
                accuracy = module_stats['accuracy'] * 100
                accuracy_value = QLabel(f"{accuracy:.1f}% ({module_stats['correct_attempts']}/{module_stats['total_attempts']})")
                
                # Set color based on accuracy
                if accuracy >= 80:
                    accuracy_value.setStyleSheet("color: #007F3E;")  # Green
                elif accuracy >= 60:
                    accuracy_value.setStyleSheet("color: #FFA500;")  # Orange
                else:
                    accuracy_value.setStyleSheet("color: #D32F2F;")  # Red
                    
                accuracy_layout.addWidget(accuracy_value)
                accuracy_layout.addStretch()
                
                module_layout.addLayout(accuracy_layout)
            
            # Add the module frame to the modules layout
            modules_layout.addWidget(module_frame)
        
        # Add stretch to push everything to the top
        modules_layout.addStretch()
        
        # Set the container as the scroll area widget
        scroll_area.setWidget(modules_container)
        
        # Add the scroll area to the main layout with stretch
        main_layout.addWidget(scroll_area, 1)  # Give it stretch factor of 1
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        
        # Make buttons larger
        close_button = button_box.button(QDialogButtonBox.Close)
        close_button.setMinimumHeight(40)
        close_button.setFont(QFont("Segoe UI", 12))
        close_button.setStyleSheet("""
            padding: 5px 20px;
        """)
        
        main_layout.addWidget(button_box)
        
        # Show the dialog
        dialog.exec_()
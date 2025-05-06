"""
UI Components Module for I-CTF Application

This module provides custom UI components with modern styling for the CTF application.
It includes styled buttons, cards, panels, and other UI elements with visual enhancements.

Author: Matthew Tomme
Date: April 30, 2025
Version: 1.0
"""

from PyQt5.QtWidgets import (QPushButton, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
                           QGraphicsDropShadowEffect, QSizePolicy)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QSize, QRect, QRectF
from PyQt5.QtGui import QColor, QPainter, QLinearGradient, QFont, QPen, QPainterPath, QBrush

import os
import logging

# Set up logging
logger = logging.getLogger(__name__)


def create_styled_label(text, font_size=12, font_weight="normal", color="#000000", alignment=Qt.AlignLeft):
    """
    Create a styled QLabel with specified properties.
    
    Args:
        text (str): Label text
        font_size (int): Font size in points
        font_weight (str): Font weight ("normal" or "bold")
        color (str): Text color as hex string
        alignment (Qt.Alignment): Text alignment
        
    Returns:
        QLabel: The styled label
    """
    label = QLabel(text)
    
    # Set font
    weight = QFont.Bold if font_weight == "bold" else QFont.Normal
    label.setFont(QFont("Segoe UI", font_size, weight))
    
    # Set color and alignment
    label.setStyleSheet(f"color: {color};")
    label.setAlignment(alignment)
    
    return label


class RoundedPushButton(QPushButton):
    """
    A modern push button with rounded corners, gradient background, and hover effects.
    
    This class creates visually enhanced buttons with animations and proper styling
    to match the TAMU-CC color scheme.
    """
    
    def __init__(self, text, parent=None):
        """
        Initialize the button with text.
        
        Args:
            text (str): Button text
            parent: Parent widget
        """
        super().__init__(text, parent)
        
        # Default colors
        self._color = QColor("#0067C5")  # Islander Blue
        self._hover_color = QColor("#1C92D1")  # Izzy Blue
        self._pressed = False
        self._hovered = False
        
        # Configure appearance
        self.setMinimumHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("border: none; color: white;")
        
        # Add shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(10)
        self.shadow.setColor(QColor(0, 0, 0, 50))
        self.shadow.setOffset(2, 2)
        self.setGraphicsEffect(self.shadow)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
    
    def set_color(self, color):
        """
        Set the button's base color.
        
        Args:
            color (str): Hex color code
        """
        self._color = QColor(color)
        self.update()
    
    def set_hover_color(self, color):
        """
        Set the button's hover color.
        
        Args:
            color (str): Hex color code
        """
        self._hover_color = QColor(color)
        self.update()
    
    def enterEvent(self, event):
        """Handle mouse enter event for hover effect."""
        self._hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event for hover effect."""
        self._hovered = False
        self.update()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.LeftButton:
            self._pressed = False
            self.update()
        super().mouseReleaseEvent(event)
    
    def paintEvent(self, event):
        """Custom paint event to draw rounded corners and gradient background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        # Use QRectF instead of QRect
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 10, 10)
        
        # Select the appropriate color based on button state
        if self._pressed:
            # Darker when pressed
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, self._color.darker(120))
            gradient.setColorAt(1, self._color.darker(120))
        elif self._hovered:
            # Lighter when hovered
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, self._hover_color.lighter(110))
            gradient.setColorAt(1, self._hover_color)
        else:
            # Normal state
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, self._color.lighter(110))
            gradient.setColorAt(1, self._color)
        
        # Fill the path with the gradient
        painter.fillPath(path, gradient)
        
        # Draw the text
        painter.setPen(QColor("white"))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())
        
        # Draw the icon if present
        if not self.icon().isNull():
            icon_size = QSize(24, 24)
            icon_rect = QRect(10, (self.height() - icon_size.height()) // 2,
                            icon_size.width(), icon_size.height())
            self.icon().paint(painter, icon_rect)


class ModuleCard(QFrame):
    """
    A modern card widget for displaying modules with visual enhancements.
    
    This class creates stylized cards with rounded corners, shadows, and
    completion indicators for module selection.
    """
    
    clicked = pyqtSignal()  # Signal emitted when card is clicked
    
    def __init__(self, title, completed=False, completion_percentage=0, parent=None):
        """
        Initialize the module card with title and completion state.
        
        Args:
            title (str): Card title
            completed (bool): Whether the module is completed
            completion_percentage (float): Percentage of completion (0-100)
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Configure appearance
        self.setMinimumSize(180, 140)  # Slightly taller to accommodate progress bar
        self.setMaximumSize(350, 200)
        self.setCursor(Qt.PointingHandCursor)
        
        # Store properties
        self.title = title
        self.completed = completed
        self.completion_percentage = completion_percentage
        self._click_handler = None
        self._hovered = False
        
        # Add shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.shadow.setOffset(3, 3)
        self.setGraphicsEffect(self.shadow)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        
        # Add header with title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            color: white;
            font-weight: bold;
            font-size: 20px;
            padding: 15px;
            background-color: #0067C5;
            border-radius: 10px 10px 0 0;
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Add content space
        layout.addStretch()
        
        # Add completion indicator and progress bar
        if completed:
            completion_label = QLabel("✓ Completed")
            completion_label.setStyleSheet("""
                color: #007F3E;
                font-weight: bold;
                padding: 5px;
            """)
            completion_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(completion_label)
            
            # Set completion to 100% if marked as completed
            self.completion_percentage = 100
        elif completion_percentage > 0:
            # Only show percentage if not completed but progress exists
            completion_label = QLabel(f"{completion_percentage:.0f}% Complete")
            completion_label.setStyleSheet("""
                color: #0067C5;
                font-weight: bold;
                padding: 5px;
            """)
            completion_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(completion_label)
        
        # Add progress bar (always show, but only filled if there's progress)
        from PyQt5.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        # Convert float to int before setting value
        self.progress_bar.setValue(int(self.completion_percentage))
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background: #F0F0F0;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background: #007F3E;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
    
    def set_click_handler(self, handler):
        """
        Set the click handler function.
        
        Args:
            handler: Function to call when card is clicked
        """
        self._click_handler = handler
    
    def enterEvent(self, event):
        """Handle mouse enter event for hover effect."""
        self._hovered = True
        self.shadow.setBlurRadius(25)
        self.shadow.setOffset(5, 5)
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event for hover effect."""
        self._hovered = False
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(3, 3)
        self.update()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            if self._click_handler:
                self._click_handler()
        super().mousePressEvent(event)
    
    def paintEvent(self, event):
        """Custom paint event to draw rounded corners and border."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        # Use QRectF instead of QRect
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 10, 10)
        
        # Fill with white background
        painter.fillPath(path, QBrush(QColor("white")))
        
        # Draw border with slight highlight when hovered
        if self._hovered:
            pen = QPen(QColor("#0067C5"), 2)
        else:
            pen = QPen(QColor("#9EA2A4"), 1)
        painter.setPen(pen)
        painter.drawPath(path)


class TopicCard(QFrame):
    """
    A modern card widget for displaying topics with visual enhancements.
    
    This class creates stylized cards with rounded corners, shadows, and
    completion indicators for topic selection.
    """
    
    clicked = pyqtSignal()  # Signal emitted when card is clicked
    
    def __init__(self, title, completed=False, parent=None):
        """
        Initialize the topic card with title and completion state.
        
        Args:
            title (str): Card title
            completed (bool): Whether the topic is completed
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Configure appearance
        self.setMinimumSize(400, 200)
        self.setMaximumSize(600, 300)
        self.setCursor(Qt.PointingHandCursor)
        
        # Store properties
        self.title = title
        self.completed = completed
        self._click_handler = None
        self._hovered = False
        
        # Add shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(12)
        self.shadow.setColor(QColor(0, 0, 0, 50))
        self.shadow.setOffset(2, 2)
        self.setGraphicsEffect(self.shadow)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            color: #0067C5;
            font-weight: bold;
            font-size: 30px;
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        # Add completion indicator if completed
        if completed:
            completion_label = QLabel("✓ Completed")
            completion_label.setStyleSheet("""
                color: #007F3E;
                font-weight: bold;
                padding: 5px;
            """)
            completion_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(completion_label)
            
            # Add progress bar
            from PyQt5.QtWidgets import QProgressBar
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(100)
            progress_bar.setTextVisible(False)
            progress_bar.setMaximumHeight(6)
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 3px;
                    background: #F0F0F0;
                }
                QProgressBar::chunk {
                    border-radius: 3px;
                    background: #007F3E;
                }
            """)
            layout.addWidget(progress_bar)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
    
    def set_click_handler(self, handler):
        """
        Set the click handler function.
        
        Args:
            handler: Function to call when card is clicked
        """
        self._click_handler = handler
    
    def enterEvent(self, event):
        """Handle mouse enter event for hover effect."""
        self._hovered = True
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(4, 4)
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event for hover effect."""
        self._hovered = False
        self.shadow.setBlurRadius(12)
        self.shadow.setOffset(2, 2)
        self.update()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            if self._click_handler:
                self._click_handler()
        super().mousePressEvent(event)
    
    def paintEvent(self, event):
        """Custom paint event to draw rounded corners and border."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        # Use QRectF instead of QRect
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 10, 10)
        
        # Fill with white background
        painter.fillPath(path, QBrush(QColor("white")))
        
        # Draw border with slight highlight when hovered
        if self._hovered:
            pen = QPen(QColor("#0067C5"), 2)
        else:
            pen = QPen(QColor("#9EA2A4"), 1)
        painter.setPen(pen)
        painter.drawPath(path)


class QuestionPanel(QFrame):
    """
    A modern panel for displaying question content with visual enhancements.
    
    This class creates stylized panels with rounded corners, shadows, and
    formatting for displaying CTF questions and answers.
    """
    
    def __init__(self, question_text, question_index, identifier, parent=None):
        """
        Initialize the question panel with basic information.
        
        Args:
            question_text (str): The question text to display
            question_index (int): The question number
            identifier (str): Question identifier
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Configure appearance
        self.setMinimumHeight(200)
        
       # Add shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(10)
        self.shadow.setColor(QColor(0, 0, 0, 40))
        self.shadow.setOffset(1, 1)
        self.setGraphicsEffect(self.shadow)
        
        # Store properties
        self.question_text = question_text
        self.question_index = question_index
        self.identifier = identifier
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Add question header
        header_layout = QHBoxLayout()
        
        # Question number
        question_num = QLabel(f"Q{question_index}:")
        question_num.setStyleSheet("""
            color: #0067C5;
            font-weight: bold;
            font-size: 14px;
        """)
        header_layout.addWidget(question_num)
        
        # Identifier
        identifier_label = QLabel(f"[{identifier}]")
        identifier_label.setStyleSheet("""
            color: #636A6A;
            font-size: 10px;
        """)
        header_layout.addWidget(identifier_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Add question text
        text_area = QLabel(question_text)
        text_area.setWordWrap(True)
        text_area.setStyleSheet("""
            background-color: white;
            border-radius: 5px;
            padding: 10px;
            font-size: 12px;
        """)
        text_area.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(text_area)
    
    def paintEvent(self, event):
        """Custom paint event to draw rounded corners and border."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        # Use QRectF instead of QRect
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 10, 10)
        
        # Fill with light gray color
        painter.fillPath(path, QBrush(QColor("#F8F8F8")))
        
        # Draw border
        painter.setPen(QPen(QColor("#9EA2A4"), 1))
        painter.drawPath(path)
"""
Progress Manager Module for I-CTF Application

This module provides functionality for tracking user progress through CTF challenges.
It handles recording attempts, tracking completion status, and calculating statistics.

Author: Matthew Tomme
Date: April 30, 2025
Version: 1.0
"""

import os
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)


class ProgressManager:
    """
    Manages user progress through CTF challenges with persistent storage.
    
    This class handles recording and tracking attempt history, completion status,
    and performance statistics for modules, difficulties, topics, and questions.
    """
    
    def __init__(self):
        """
        Initialize the progress manager with data from the progress file.
        """
        # Set file paths
        self.stats_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ctf_stats.json")
        self.progress_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ctf_progress.json")
        
        # Load existing data
        self.stats = self._load_stats()
        self.progress = self._load_progress()
        
        # Ensure the stats has the required structure
        if "attempts" not in self.stats:
            self.stats["attempts"] = {}
        if "totals" not in self.stats:
            self.stats["totals"] = {
                "total_attempts": 0,
                "correct_attempts": 0
            }
        
        # Ensure the progress has the required structure
        if "completed" not in self.progress:
            self.progress["completed"] = {}
        
        logger.info("Progress manager initialized")
    
    def _load_stats(self):
        """
        Load statistics from the stats file.
        
        Returns:
            dict: Statistics data loaded from file
        """
        # Default stats structure
        default_stats = {
            "attempts": {},  # Track all attempts by module/difficulty/topic/question
            "totals": {
                "total_attempts": 0,
                "correct_attempts": 0
            }
        }
        
        if os.path.exists(self.stats_path):
            try:
                with open(self.stats_path, 'r') as f:
                    loaded_stats = json.load(f)
                    
                    # Ensure the loaded stats have the required structure
                    if "attempts" not in loaded_stats:
                        loaded_stats["attempts"] = {}
                    if "totals" not in loaded_stats:
                        loaded_stats["totals"] = {
                            "total_attempts": 0,
                            "correct_attempts": 0
                        }
                    
                    return loaded_stats
            except json.JSONDecodeError:
                logger.error("Invalid JSON in stats file")
            except Exception as e:
                logger.error(f"Error loading stats: {str(e)}")
        
        return default_stats
    
    def _load_progress(self):
        """
        Load progress data from the progress file.
        
        Returns:
            dict: Progress data loaded from file
        """
        # Default progress structure
        default_progress = {
            "completed": {}  # Track completed questions by module/difficulty/topic/question
        }
        
        if os.path.exists(self.progress_path):
            try:
                with open(self.progress_path, 'r') as f:
                    loaded_progress = json.load(f)
                    
                    # Ensure the loaded progress has the required structure
                    if "completed" not in loaded_progress:
                        loaded_progress["completed"] = {}
                    
                    return loaded_progress
            except json.JSONDecodeError:
                logger.error("Invalid JSON in progress file")
            except Exception as e:
                logger.error(f"Error loading progress: {str(e)}")
        
        return default_progress
    
    def _save_stats(self):
        """Save the current statistics to the stats file."""
        try:
            with open(self.stats_path, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats: {str(e)}")
    
    def _save_progress(self):
        """Save the current progress to the progress file."""
        try:
            with open(self.progress_path, 'w') as f:
                json.dump(self.progress, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving progress: {str(e)}")
    
    def record_attempt(self, module, difficulty, topic, question, is_correct):
        """
        Record an attempt at a question and update statistics.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str): The topic name
            question (str): The question file name
            is_correct (bool): Whether the attempt was correct
            
        Returns:
            bool: True if successfully recorded, False otherwise
        """
        if not module or not topic or not question:
            logger.error("Cannot record attempt with missing parameters")
            return False
        
        try:
            # Create a unique key for this question
            key = self._create_question_key(module, difficulty, topic, question)
            
            # Initialize attempts dict for this question if needed
            if key not in self.stats["attempts"]:
                self.stats["attempts"][key] = {
                    "total": 0,
                    "correct": 0
                }
            
            # Update attempt counts
            self.stats["attempts"][key]["total"] += 1
            if is_correct:
                self.stats["attempts"][key]["correct"] += 1
            
            # Update totals
            self.stats["totals"]["total_attempts"] += 1
            if is_correct:
                self.stats["totals"]["correct_attempts"] += 1
            
            # Save the updated stats
            self._save_stats()
            
            logger.debug(f"Recorded {'correct' if is_correct else 'incorrect'} attempt for {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording attempt: {str(e)}")
            return False
    
    def mark_question_completed(self, module, difficulty, topic, question):
        """
        Mark a question as completed.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str): The topic name
            question (str): The question file name
            
        Returns:
            bool: True if successfully marked as completed, False otherwise
        """
        if not module or not topic or not question:
            logger.error("Cannot mark completion with missing parameters")
            return False
        
        try:
            # Create a unique key for this question
            key = self._create_question_key(module, difficulty, topic, question)
            
            # Initialize completed dict if needed
            if "completed" not in self.progress:
                self.progress["completed"] = {}
            
            # Mark as completed
            self.progress["completed"][key] = True
            
            # Save the updated progress
            self._save_progress()
            
            logger.debug(f"Marked question completed: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking question completed: {str(e)}")
            return False
    
    def is_question_completed(self, module, difficulty, topic, question):
        """
        Check if a question is completed.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str): The topic name
            question (str): The question file name
            
        Returns:
            bool: True if the question is completed, False otherwise
        """
        if not module or not topic or not question:
            return False
        
        # Create a unique key for this question
        key = self._create_question_key(module, difficulty, topic, question)
        
        # Check if it's in the completed dict
        return self.progress.get("completed", {}).get(key, False)
    
    def _create_question_key(self, module, difficulty, topic, question):
        """
        Create a unique key for a question based on its location.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str): The topic name
            question (str): The question file name
            
        Returns:
            str: A unique key string
        """
        if isinstance(topic, tuple) and len(topic) == 2:
            # Extract directory name from topic tuple
            topic = topic[0]
            
        # Create the key with the difficulty if provided
        if difficulty:
            return f"{module}/{difficulty}/{topic}/{question}"
        else:
            return f"{module}/None/{topic}/{question}"
    
    def get_question_stats(self, module, difficulty, topic, question):
        """
        Get attempt statistics for a specific question.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str): The topic name
            question (str): The question file name
            
        Returns:
            dict: Statistics for the question, or None if no attempts recorded
        """
        # Create a unique key for this question
        key = self._create_question_key(module, difficulty, topic, question)
        
        # Get the stats for this question
        stats = self.stats["attempts"].get(key)
        
        if not stats:
            return {
                "total": 0,
                "correct": 0,
                "accuracy": 0
            }
        
        # Calculate accuracy
        if stats["total"] > 0:
            accuracy = stats["correct"] / stats["total"]
        else:
            accuracy = 0
            
        return {
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": accuracy
        }
    
    def get_topic_stats(self, module, difficulty, topic):
        """
        Get aggregated statistics for a topic.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str): The topic name
            
        Returns:
            dict: Aggregated statistics for the topic
        """
        # Extract directory name from topic tuple if needed
        if isinstance(topic, tuple) and len(topic) == 2:
            topic = topic[0]
            
        # Create a prefix for all questions in this topic
        prefix = self._create_question_key(module, difficulty, topic, "")[:-1]
        
        # Filter and aggregate stats for all questions with this prefix
        total_attempts = 0
        correct_attempts = 0
        
        for key, stats in self.stats["attempts"].items():
            if key.startswith(prefix):
                total_attempts += stats["total"]
                correct_attempts += stats["correct"]
        
        # Calculate accuracy
        if total_attempts > 0:
            accuracy = correct_attempts / total_attempts
        else:
            accuracy = 0
            
        return {
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "accuracy": accuracy
        }
    
    def get_difficulty_stats(self, module, difficulty):
        """
        Get aggregated statistics for a difficulty.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level
            
        Returns:
            dict: Aggregated statistics for the difficulty
        """
        # Create a prefix for all questions in this difficulty
        prefix = f"{module}/{difficulty}/"
        
        # Filter and aggregate stats for all questions with this prefix
        total_attempts = 0
        correct_attempts = 0
        
        for key, stats in self.stats["attempts"].items():
            if key.startswith(prefix):
                total_attempts += stats["total"]
                correct_attempts += stats["correct"]
        
        # Calculate accuracy
        if total_attempts > 0:
            accuracy = correct_attempts / total_attempts
        else:
            accuracy = 0
            
        return {
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "accuracy": accuracy
        }
    
    def get_module_stats(self, module):
        """
        Get aggregated statistics for a module.
        
        Args:
            module (str): The module name
            
        Returns:
            dict: Aggregated statistics for the module
        """
        # Create a prefix for all questions in this module
        prefix = f"{module}/"
        
        # Filter and aggregate stats for all questions with this prefix
        total_attempts = 0
        correct_attempts = 0
        
        for key, stats in self.stats["attempts"].items():
            if key.startswith(prefix):
                total_attempts += stats["total"]
                correct_attempts += stats["correct"]
        
        # Calculate accuracy
        if total_attempts > 0:
            accuracy = correct_attempts / total_attempts
        else:
            accuracy = 0
            
        return {
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "accuracy": accuracy
        }
    
    def get_overall_stats(self):
        """
        Get overall performance statistics.
        
        Returns:
            dict: Overall statistics with aggregate data
        """
        # Make sure totals exists
        if "totals" not in self.stats:
            self.stats["totals"] = {
                "total_attempts": 0,
                "correct_attempts": 0
            }
        
        totals = self.stats["totals"]
        
        # Make sure required keys exist
        if "total_attempts" not in totals:
            totals["total_attempts"] = 0
        if "correct_attempts" not in totals:
            totals["correct_attempts"] = 0
        
        # Calculate accuracy
        if totals["total_attempts"] > 0:
            accuracy = totals["correct_attempts"] / totals["total_attempts"]
        else:
            accuracy = 0
            
        return {
            "total_attempts": totals["total_attempts"],
            "correct_attempts": totals["correct_attempts"],
            "accuracy": accuracy
        }
    
    def reset(self):
        """
        Reset all progress and statistics data.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Reset stats
            self.stats = {
                "attempts": {},
                "totals": {
                    "total_attempts": 0,
                    "correct_attempts": 0
                }
            }
            
            # Reset progress
            self.progress = {
                "completed": {},
                "hints_used": {}  # Add hints_used to reset
            }
            
            # Save the reset data
            self._save_stats()
            self._save_progress()
            
            logger.info("Progress and statistics reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting progress: {str(e)}")
            return False
        

    def mark_hint_used(self, module, difficulty, topic, question):
        """
        Mark a hint as used for a specific question.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str): The topic name
            question (str): The question file name
            
        Returns:
            bool: True if successfully marked, False otherwise
        """
        if not module or not topic or not question:
            logger.error("Cannot mark hint usage with missing parameters")
            return False
        
        try:
            # Create a unique key for this question
            key = self._create_question_key(module, difficulty, topic, question)
            
            # Initialize hints_used dict if needed
            if "hints_used" not in self.progress:
                self.progress["hints_used"] = {}
            
            # Mark as used
            self.progress["hints_used"][key] = True
            
            # Save the updated progress
            self._save_progress()
            
            logger.debug(f"Marked hint used for question: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking hint used: {str(e)}")
            return False
        
    def is_hint_used(self, module, difficulty, topic, question):
        """
        Check if a hint has been used for a question.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str): The topic name
            question (str): The question file name
            
        Returns:
            bool: True if the hint has been used, False otherwise
        """
        if not module or not topic or not question:
            return False
        
        # Create a unique key for this question
        key = self._create_question_key(module, difficulty, topic, question)
        
        # Check if it's in the hints_used dict
        return self.progress.get("hints_used", {}).get(key, False)
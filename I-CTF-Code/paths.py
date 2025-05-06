"""
Path Manager Module for I-CTF Application

This module handles file and directory paths for the CTF application.
It provides standardized methods for working with module, difficulty, topic,
and question paths with proper validation.

Author: Matthew Tomme
Date: April 30, 2025
Version: 1.0
"""

import os
import logging
import re

# Set up logging
logger = logging.getLogger(__name__)


class PathManager:
    """
    Manages file and directory paths for the CTF application with error handling.
    
    This class handles all file path operations using standardized methods with
    proper validation to avoid errors and improve reliability. It determines the
    correct paths for modules, difficulties, topics, questions, and related files.
    """
    
    def __init__(self, config_manager):
        """
        Initialize the path manager with the configuration manager.
        
        Args:
            config_manager: Instance of ConfigManager for path settings
        """
        self.config = config_manager
        self.base_directory = self.config.get_base_directory()
        
        # Cache for topic display names
        self.topic_display_names = {}
        
        logger.info(f"Path Manager initialized with base directory: {self.base_directory}")
    
    def set_base_directory(self, directory):
        """
        Set the base directory and update config.
        
        Args:
            directory (str): The directory path to set as the base directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not directory or not os.path.exists(directory):
            logger.error(f"Directory does not exist: {directory}")
            return False
            
        self.base_directory = directory
        # Clear the display name cache when changing directories
        self.topic_display_names = {}
        return self.config.set_base_directory(directory)
    
    def is_valid_ctf_directory(self, directory):
        """
        Check if a directory is a valid CTF directory.
        
        A valid CTF directory contains at least one of the common module directories.
        
        Args:
            directory (str): The directory path to check
            
        Returns:
            bool: True if the directory is a valid CTF directory, False otherwise
        """
        if not directory or not os.path.exists(directory):
            logger.error(f"Directory does not exist: {directory}")
            return False
            
        # Look for at least one module directory
        common_modules = [
            "OSI", "Cryptography", "Password Cracking", "Web App Exploitation", 
            "Getting Started", "Log Analysis", "Forensics", "Network Traffic Analysis", 
            "Enumeration & Exploitation", "Scanning & Reconnaissance", "Wireless Exploitation"
        ]
        
        for module in common_modules:
            module_path = os.path.join(directory, module)
            if os.path.exists(module_path) and os.path.isdir(module_path):
                return True
                
        logger.warning(f"No common CTF modules found in directory: {directory}")
        return False
    
    def get_module_path(self, module):
        """
        Get the path to a specific module.
        
        Args:
            module (str): The module name
            
        Returns:
            str: The full path to the module directory, or None if invalid
        """
        if not self.base_directory or not module:
            return None
            
        module_path = os.path.join(self.base_directory, module)
        
        if not os.path.exists(module_path) or not os.path.isdir(module_path):
            logger.warning(f"Module path does not exist: {module_path}")
            return None
            
        return module_path
    
    def get_difficulty_path(self, module, difficulty):
        """
        Get the path to a specific difficulty within a module.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            
        Returns:
            str: The full path to the difficulty directory, or None if invalid
        """
        # Skip difficulty check for Getting Started module or if difficulty is None
        if module == "Getting Started" or not difficulty:
            return self.get_module_path(module)
        
        module_path = self.get_module_path(module)
        if not module_path:
            return None
            
        difficulty_path = os.path.join(module_path, difficulty)
        
        if not os.path.exists(difficulty_path) or not os.path.isdir(difficulty_path):
            logger.warning(f"Difficulty path does not exist: {difficulty_path}")
            return None
            
        return difficulty_path
    
    def get_topic_path(self, module, difficulty, topic):
        """
        Get the path to a specific topic.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str or tuple): The topic name or (dir_name, display_name) tuple
            
        Returns:
            str: The full path to the topic directory, or None if invalid
        """
        if not topic:
            return None
            
        # Handle tuple form (dir_name, display_name)
        if isinstance(topic, tuple) and len(topic) == 2:
            topic = topic[0]  # Use directory name
        
        difficulty_path = self.get_difficulty_path(module, difficulty)
        if not difficulty_path:
            return None
            
        topic_path = os.path.join(difficulty_path, topic)
        
        if not os.path.exists(topic_path) or not os.path.isdir(topic_path):
            logger.warning(f"Topic path does not exist: {topic_path}")
            return None
            
        return topic_path
    
    def get_topics(self, module, difficulty):
        """
        Get all topics for a module/difficulty with improved caching.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            
        Returns:
            list: List of topic tuples (directory_name, display_name)
        """
        if not module:
            logger.error("Module name cannot be None when getting topics")
            return []
            
        # Create a cache key for this module+difficulty combination
        cache_key = f"{module}:{difficulty}"
        
        # Check if we already have this info in the cache
        if cache_key in self.topic_display_names:
            return self.topic_display_names[cache_key]
        
        topics = []
        path = self.get_difficulty_path(module, difficulty)
        
        # Get all directories that start with "Topic"
        if path and os.path.exists(path):
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path) and item.startswith("Topic"):
                        # Get the display name if a topic_name.txt exists
                        display_name = item  # Default to directory name
                        topic_name_file = os.path.join(item_path, "topic_name.txt")
                        
                        if os.path.exists(topic_name_file):
                            try:
                                with open(topic_name_file, 'r') as f:
                                    custom_name = f.read().strip()
                                    if custom_name:
                                        # Store both the directory name and display name
                                        topics.append((item, custom_name))
                                        continue
                            except Exception as e:
                                logger.error(f"Error reading topic name file {topic_name_file}: {str(e)}")
                        
                        # If no custom name was found or there was an error, use the directory name
                        topics.append((item, item))  # Store as (dir_name, display_name) tuple for consistency
            except Exception as e:
                logger.error(f"Error listing topics: {str(e)}")
                return []
        else:
            logger.warning(f"Path does not exist: {path}")
            return []
        
        # Sort topics numerically if possible
        try:
            def sort_key(topic_tuple):
                dir_name = topic_tuple[0]
                # Extract topic number
                match = re.search(r'Topic\s*(\d+)', dir_name)
                if match:
                    return int(match.group(1))
                return 999  # Large number for items that don't match pattern
                
            topics.sort(key=sort_key)
        except Exception as e:
            # If sorting fails, use alphabetical order as fallback
            topics.sort()
            logger.warning(f"Could not sort topics numerically, using alphabetical order: {str(e)}")
        
        # Store in cache for future use
        self.topic_display_names[cache_key] = topics
            
        return topics
    
    def get_questions(self, module, difficulty, topic):
        """
        Get all questions for a topic with standardized path handling.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str or tuple): The topic name or (dir_name, display_name) tuple
            
        Returns:
            list: List of tuples (question_type, question_file_name)
        """
        if not module or not topic:
            logger.error(f"Module or topic cannot be None: module={module}, topic={topic}")
            return []
            
        questions = []
        
        # Get the topic path
        topic_path = self.get_topic_path(module, difficulty, topic)
        if not topic_path:
            return []
            
        # Regular questions path
        questions_path = os.path.join(topic_path, "Questions")
        
        # Prompt-style questions path
        prompt_path = os.path.join(topic_path, "Prompt or Not", "Prompt Style")
        
        # Get regular questions
        if os.path.exists(questions_path) and os.path.isdir(questions_path):
            try:
                for item in sorted(os.listdir(questions_path)):
                    if item.endswith(".txt"):
                        questions.append(("regular", item))
            except Exception as e:
                logger.error(f"Error listing regular questions: {str(e)}")
        
        # Get prompt-style questions
        if os.path.exists(prompt_path) and os.path.isdir(prompt_path):
            try:
                for item in sorted(os.listdir(prompt_path)):
                    if item.endswith(".txt"):
                        questions.append(("prompt", item))
            except Exception as e:
                logger.error(f"Error listing prompt-style questions: {str(e)}")
        
        return questions
    
    def load_question_content(self, module, difficulty, topic, q_type, q_file):
        """
        Load the content of a question file with standardized parsing.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str or tuple): The topic name or (dir_name, display_name) tuple
            q_type (str): The question type ('regular' or 'prompt')
            q_file (str): The question file name
            
        Returns:
            tuple: (formatted_content, actual_question)
        """
        if not module or not topic or not q_file:
            error_msg = f"Invalid parameters: module={module}, topic={topic}, q_file={q_file}"
            logger.error(error_msg)
            return error_msg, error_msg
            
        # Get the topic path
        topic_path = self.get_topic_path(module, difficulty, topic)
        if not topic_path:
            error_msg = f"Invalid topic path for {module}/{difficulty}/{topic}"
            logger.error(error_msg)
            return error_msg, error_msg
            
        # Determine the question file path based on type
        question_path = None
        if q_type == "prompt":
            question_path = os.path.join(topic_path, "Prompt or Not", "Prompt Style", q_file)
        else:
            question_path = os.path.join(topic_path, "Questions", q_file)
        
        # Load question content
        try:
            with open(question_path, 'r') as file:
                question_content = file.read()
                
                # Process the question content based on the format
                # Description is within [ ] and the actual question is within { }
                description = self._extract_content(question_content, '[', ']')
                actual_question = self._extract_content(question_content, '{', '}')
                
                # If the format wasn't found, use the whole content
                if not description and not actual_question:
                    formatted_content = question_content
                    actual_question = question_content
                else:
                    # Format with description and question properly highlighted
                    formatted_content = ""
                    if description:
                        formatted_content += description + "\n\n"
                    if actual_question:
                        formatted_content += actual_question
                
                return formatted_content, actual_question
                
        except FileNotFoundError:
            error_msg = f"Question file not found: {q_file}"
            logger.error(error_msg)
            return error_msg, error_msg
        except Exception as e:
            error_msg = f"Error loading question {q_file}: {str(e)}"
            logger.error(error_msg)
            return error_msg, error_msg
    
    def _extract_content(self, text, start_char, end_char):
        """
        Extract content between specified characters.
        
        Args:
            text (str): The text to search
            start_char (str): Starting character/bracket
            end_char (str): Ending character/bracket
            
        Returns:
            str: Extracted content or empty string if not found
        """
        if not text:
            return ""
            
        start_index = text.find(start_char)
        end_index = text.find(end_char, start_index + 1 if start_index != -1 else 0)
        
        if start_index != -1 and end_index != -1 and end_index > start_index:
            return text[start_index + 1:end_index].strip()
        
        return ""
    
    def get_correct_answer(self, module, difficulty, topic, question_file):
        """
        Get the correct answer for a question with improved error handling.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str or tuple): The topic name or (dir_name, display_name) tuple
            question_file (str): The question file name
            
        Returns:
            str or list: The correct answer(s), or None if not found
        """
        # Remove PS_ prefix if present (for prompt-style questions)
        base_name = question_file.replace("PS_", "")
        
        # Get answers directory
        topic_path = self.get_topic_path(module, difficulty, topic)
        if not topic_path:
            logger.error(f"Invalid topic path for {module}/{difficulty}/{topic}")
            return None
            
        answers_dir = os.path.join(topic_path, "Answers")
        if not os.path.exists(answers_dir) or not os.path.isdir(answers_dir):
            logger.error(f"Answers directory not found for {module}/{difficulty}/{topic}")
            return None
        
        # Extract first letter (identifier) from question filename
        identifier = base_name.split('_')[0] if '_' in base_name else base_name[0]
        logger.debug(f"Looking for answer with identifier: {identifier}")
        
        # Look for pattern: Letter_*_Answer.txt
        pattern1 = f"{identifier}_*_Answer.txt"
        # Look for pattern: Letter_Answer.txt
        pattern2 = f"{identifier}_Answer.txt"
        
        # Try to find matching answer files
        answer_files = []
        for item in os.listdir(answers_dir):
            if item.startswith(f"{identifier}_") and "Answer" in item and item.endswith(".txt"):
                answer_files.append(item)
        
        logger.debug(f"Found {len(answer_files)} potential answer files: {answer_files}")
        
        # If no answer files found, try the original patterns
        if not answer_files:
            possible_patterns = [
                base_name.replace("Question", "Answer"),  # Standard naming
                base_name + "_Answer.txt",                # Simple suffix
                base_name.split('_')[0] + "_Answer.txt"   # Identifier-based
            ]
            
            # Check each pattern
            for pattern in possible_patterns:
                answer_path = os.path.join(answers_dir, pattern)
                if os.path.exists(answer_path):
                    answer_files.append(pattern)
        
        # Try to read each answer file
        for answer_file in answer_files:
            answer_path = os.path.join(answers_dir, answer_file)
            try:
                with open(answer_path, 'r') as f:
                    answer_content = f.read().strip()
                    logger.debug(f"Found answer content: {answer_content}")
                    
                    # Return the answer content (will be checked for | later during answer validation)
                    return answer_content
            except Exception as e:
                logger.error(f"Error reading answer file {answer_path}: {str(e)}")
        
        # Also try the exact same name as the question file
        answer_path = os.path.join(answers_dir, base_name)
        if os.path.exists(answer_path):
            try:
                with open(answer_path, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Error reading answer file {answer_path}: {str(e)}")
        
        logger.warning(f"No answer file found for question: {question_file}")
        return None
    
    def get_hint_content(self, module, difficulty, topic, question_file):
        """
        Get hint content for a question with improved error handling and debugging.
        
        Args:
            module (str): The module name
            difficulty (str): The difficulty level, or None for modules without difficulties
            topic (str or tuple): The topic name or (dir_name, display_name) tuple
            question_file (str): The question file name
            
        Returns:
            str: The hint content, or None if not found
        """
        # Remove PS_ prefix if present (for prompt-style questions)
        base_name = question_file.replace("PS_", "")
        
        # Extract the question identifier (first letter or first part before underscore)
        identifier = base_name.split('_')[0] if '_' in base_name else base_name[0]
        
        # Log the identifier we're looking for
        logger.debug(f"Looking for hint with identifier: {identifier}")
        
        # Get hints directory
        topic_path = self.get_topic_path(module, difficulty, topic)
        if not topic_path:
            logger.warning(f"Invalid topic path for {module}/{difficulty}/{topic}")
            return None
            
        hints_dir = os.path.join(topic_path, "Hints")
        if not os.path.exists(hints_dir) or not os.path.isdir(hints_dir):
            logger.warning(f"Hints directory not found: {hints_dir}")
            return None
        
        # Log the list of files in the hints directory to help with debugging
        try:
            hint_files = os.listdir(hints_dir)
            logger.debug(f"Files in hints directory: {hint_files}")
        except Exception as e:
            logger.error(f"Error listing hints directory: {str(e)}")
        
        # Try different naming patterns for hint files with the identifier
        possible_patterns = [
            f"{identifier}_*.txt",                      # Any file starting with identifier_
            f"{identifier}*.txt",                       # Any file starting with identifier
            f"*{identifier}_*.txt",                     # Any file containing _identifier_
            f"*_{identifier}_*.txt",                    # Any file containing _identifier_
            base_name,                                  # Exact match for question name
            base_name.replace("Question", "Hint"),      # Standard naming
            base_name + "_Hint.txt",                    # Simple suffix
            identifier + "_Hint.txt",                   # Identifier-based
            identifier + "_*.txt"                       # Any file starting with identifier_
        ]
        
        # Check for any matching files in the hints directory
        matching_files = []
        try:
            for file in hint_files:
                file_path = os.path.join(hints_dir, file)
                if os.path.isfile(file_path) and file.startswith(identifier):
                    matching_files.append(file)
                    
            logger.debug(f"Files matching identifier {identifier}: {matching_files}")
            
            # Try to read each matching file
            for file in matching_files:
                file_path = os.path.join(hints_dir, file)
                try:
                    with open(file_path, 'r') as f:
                        hint_content = f.read().strip()
                        logger.debug(f"Loaded hint content from {file}")
                        return hint_content
                except Exception as e:
                    logger.error(f"Error reading hint file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing hint files: {str(e)}")
        
        # If no matching files were found, try to find using the patterns
        for pattern in possible_patterns:
            try:
                import glob
                matching_paths = glob.glob(os.path.join(hints_dir, pattern))
                
                if matching_paths:
                    logger.debug(f"Found matching hint files using pattern {pattern}: {matching_paths}")
                    
                    for hint_path in matching_paths:
                        try:
                            with open(hint_path, 'r') as f:
                                hint_content = f.read().strip()
                                logger.debug(f"Loaded hint content from {hint_path}")
                                return hint_content
                        except Exception as e:
                            logger.error(f"Error reading hint file {hint_path}: {str(e)}")
            except Exception as e:
                logger.error(f"Error using pattern {pattern}: {str(e)}")
        
        logger.warning(f"No hint file found for question: {question_file} with identifier {identifier}")
        return None
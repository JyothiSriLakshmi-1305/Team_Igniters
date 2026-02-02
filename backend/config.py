"""
Smart Attendance System - Configuration
Centralized configuration for the entire system
"""

import os

class Config:
    """System Configuration"""
    
    # ==================== PATHS ====================
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATASET_PATH = os.path.join(BASE_DIR, "dataset")
    TRAINER_PATH = os.path.join(BASE_DIR, "trainer")
    BACKUP_PATH = os.path.join(BASE_DIR, "backups")
    LOGS_PATH = os.path.join(BASE_DIR, "logs")
    
    # ==================== FILES ====================
    STUDENT_DB = os.path.join(BASE_DIR, "student_database.json")
    ATTENDANCE_CSV = os.path.join(BASE_DIR, "attendance.csv")
    TRAINER_MODEL = os.path.join(TRAINER_PATH, "trainer.yml")
    
    # ==================== ACADEMICS ====================
    ALLOWED_BRANCHES = ["CSE", "AIML", "ECE", "EEE", "MECH", "CIVIL"]
    ALLOWED_SECTIONS = ["A", "B"]
    
    # ==================== FACE RECOGNITION ====================
    # Confidence threshold (lower = stricter, higher = more lenient)
    RECOGNITION_CONFIDENCE_THRESHOLD = 75
    
    # Face detection parameters
    FACE_DETECTION_SCALE_FACTOR = 1.2
    FACE_DETECTION_MIN_NEIGHBORS = 5
    FACE_DETECTION_MIN_SIZE = (100, 100)
    
    # Image capture settings
    REQUIRED_IMAGES_PER_STUDENT = 50
    IMAGE_CAPTURE_FRAME_SKIP = 2  # Capture every 2nd detected face
    
    # ==================== ATTENDANCE ====================
    # Cooldown to prevent multiple marks (seconds)
    ATTENDANCE_COOLDOWN_SECONDS = 5
    
    # Batch writing interval (frames)
    BATCH_WRITE_INTERVAL = 10
    
    # ==================== CAMERA ====================
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 30
    CAMERA_BUFFER_SIZE = 1
    
    # Display FPS (for recognition window)
    DISPLAY_TARGET_FPS = 20
    
    # ==================== VALIDATION ====================
    # Roll number format: BRANCH + SECTION + 3 digits
    # Example: AIML001, CSE042, ECE123
    ROLL_NUMBER_MIN_LENGTH = 5
    ROLL_NUMBER_MAX_LENGTH = 20
    
    # Name validation
    NAME_MIN_LENGTH = 2
    NAME_MAX_LENGTH = 50
    
    # ==================== BACKUP ====================
    AUTO_BACKUP_ENABLED = True
    BACKUP_ON_STUDENT_ADD = True
    MAX_BACKUP_FILES = 10  # Keep last 10 backups
    
    # ==================== LOGGING ====================
    LOG_LEVEL = "INFO"
    LOG_FILE = os.path.join(LOGS_PATH, "attendance_system.log")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ==================== API ====================
    API_HOST = "0.0.0.0"
    API_PORT = 5000
    API_DEBUG = True
    
    # ==================== DEMO CREDENTIALS ====================
    # WARNING: Change these in production!
    DEMO_FACULTY_USERNAME = "faculty"
    DEMO_FACULTY_PASSWORD = "1234"
    DEMO_STUDENT_USERNAME = "student"
    DEMO_STUDENT_PASSWORD = "1234"
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.DATASET_PATH,
            cls.TRAINER_PATH,
            cls.BACKUP_PATH,
            cls.LOGS_PATH
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"✅ Created directory: {directory}")
    
    @classmethod
    def validate_branch_section(cls, branch, section):
        """Validate branch and section"""
        if branch not in cls.ALLOWED_BRANCHES:
            return False, f"Invalid branch. Allowed: {', '.join(cls.ALLOWED_BRANCHES)}"
        
        if section not in cls.ALLOWED_SECTIONS:
            return False, f"Invalid section. Allowed: {', '.join(cls.ALLOWED_SECTIONS)}"
        
        return True, "Valid"
    
    @classmethod
    def get_roll_number_prefix(cls, branch, section):
        """Generate roll number prefix"""
        return f"{branch}{section}"


# Initialize directories on import
Config.create_directories()
"""
Smart Attendance System - Validators
Comprehensive validation and duplicate prevention
"""

import re
import json
import os
from config import Config


class ValidationError(Exception):
    """Custom validation exception"""
    pass


class StudentValidator:
    """Validates student data and prevents duplicates"""
    
    @staticmethod
    def load_database():
        """Load student database"""
        if os.path.exists(Config.STUDENT_DB):
            try:
                with open(Config.STUDENT_DB, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    @staticmethod
    def validate_name(name):
        """
        Validate student name
        Rules:
        - Must be 2-50 characters
        - Can contain letters, spaces, dots, hyphens
        - Cannot be only spaces
        """
        if not name or not name.strip():
            raise ValidationError("Name cannot be empty")
        
        name = name.strip()
        
        if len(name) < Config.NAME_MIN_LENGTH:
            raise ValidationError(f"Name must be at least {Config.NAME_MIN_LENGTH} characters")
        
        if len(name) > Config.NAME_MAX_LENGTH:
            raise ValidationError(f"Name must be at most {Config.NAME_MAX_LENGTH} characters")
        
        # Allow letters, spaces, dots, hyphens, apostrophes
        if not re.match(r"^[A-Za-z\s.\-']+$", name):
            raise ValidationError("Name can only contain letters, spaces, dots, hyphens, and apostrophes")
        
        return name
    
    @staticmethod
    def validate_roll_number(roll_no, branch=None, section=None):
        """
        Validate roll number format
        Rules:
        - Must be 5-20 characters
        - Can contain alphanumeric characters
        - Should match pattern: BRANCH+SECTION+digits (recommended)
        """
        if not roll_no or not roll_no.strip():
            raise ValidationError("Roll number cannot be empty")
        
        roll_no = roll_no.strip().upper()
        
        if len(roll_no) < Config.ROLL_NUMBER_MIN_LENGTH:
            raise ValidationError(f"Roll number must be at least {Config.ROLL_NUMBER_MIN_LENGTH} characters")
        
        if len(roll_no) > Config.ROLL_NUMBER_MAX_LENGTH:
            raise ValidationError(f"Roll number must be at most {Config.ROLL_NUMBER_MAX_LENGTH} characters")
        
        # Must be alphanumeric
        if not re.match(r"^[A-Z0-9]+$", roll_no):
            raise ValidationError("Roll number can only contain uppercase letters and numbers")
        
        # Optional: Check if it follows recommended pattern
        if branch and section:
            expected_prefix = Config.get_roll_number_prefix(branch, section)
            if not roll_no.startswith(expected_prefix):
                print(f"⚠️  Warning: Roll number doesn't match pattern {expected_prefix}XXX")
        
        return roll_no
    
    @staticmethod
    def validate_branch_section(branch, section):
        """Validate branch and section"""
        if not branch or branch not in Config.ALLOWED_BRANCHES:
            raise ValidationError(f"Invalid branch. Allowed: {', '.join(Config.ALLOWED_BRANCHES)}")
        
        if not section or section not in Config.ALLOWED_SECTIONS:
            raise ValidationError(f"Invalid section. Allowed: {', '.join(Config.ALLOWED_SECTIONS)}")
        
        return branch.upper(), section.upper()
    
    @staticmethod
    def check_duplicate_roll_number(roll_no, exclude_student_id=None):
        """
        Check if roll number already exists
        
        Args:
            roll_no: Roll number to check
            exclude_student_id: Student ID to exclude from check (for updates)
        
        Returns:
            (bool, str): (is_duplicate, error_message)
        """
        db = StudentValidator.load_database()
        
        for student_id, info in db.items():
            # Skip if this is the student being updated
            if exclude_student_id and student_id == exclude_student_id:
                continue
            
            if info.get('rollNo', '').upper() == roll_no.upper():
                existing_name = info.get('name', 'Unknown')
                existing_class = f"{info.get('branch', 'N/A')}-{info.get('section', 'N/A')}"
                
                error_msg = (
                    f"❌ DUPLICATE ROLL NUMBER!\n"
                    f"   Roll number '{roll_no}' already exists.\n"
                    f"   Belongs to: {existing_name} ({existing_class})"
                )
                return True, error_msg
        
        return False, ""
    
    @staticmethod
    def check_duplicate_name(name, branch, section, exclude_student_id=None):
        """
        Check if student name already exists in the same class
        
        Args:
            name: Student name
            branch: Branch
            section: Section
            exclude_student_id: Student ID to exclude from check
        
        Returns:
            (bool, str): (is_duplicate, warning_message)
        """
        db = StudentValidator.load_database()
        
        name_lower = name.lower().strip()
        
        for student_id, info in db.items():
            # Skip if this is the student being updated
            if exclude_student_id and student_id == exclude_student_id:
                continue
            
            # Check same name in same class
            if (info.get('name', '').lower().strip() == name_lower and
                info.get('branch', '').upper() == branch.upper() and
                info.get('section', '').upper() == section.upper()):
                
                existing_roll = info.get('rollNo', 'N/A')
                
                warning_msg = (
                    f"⚠️  WARNING: Similar name exists!\n"
                    f"   '{name}' already registered in {branch}-{section}\n"
                    f"   Roll number: {existing_roll}"
                )
                return True, warning_msg
        
        return False, ""
    
    @staticmethod
    def generate_unique_student_id(name):
        """
        Generate unique student ID from name
        Handles duplicates by adding numbers
        """
        base_id = name.lower().strip().replace(" ", "_")
        base_id = re.sub(r'[^a-z0-9_]', '', base_id)
        
        db = StudentValidator.load_database()
        
        if base_id not in db:
            return base_id
        
        # If duplicate, add number
        counter = 1
        while f"{base_id}_{counter}" in db:
            counter += 1
        
        return f"{base_id}_{counter}"
    
    @staticmethod
    def validate_student_data(name, roll_no, branch, section, check_duplicates=True):
        """
        Comprehensive validation of all student data
        
        Args:
            name: Student name
            roll_no: Roll number
            branch: Branch
            section: Section
            check_duplicates: Whether to check for duplicates
        
        Returns:
            dict: Validated and formatted data
        
        Raises:
            ValidationError: If validation fails
        """
        # Validate and format each field
        name = StudentValidator.validate_name(name)
        roll_no = StudentValidator.validate_roll_number(roll_no, branch, section)
        branch, section = StudentValidator.validate_branch_section(branch, section)
        
        # Check duplicates if requested
        if check_duplicates:
            # Check roll number (critical - must be unique)
            is_dup, error = StudentValidator.check_duplicate_roll_number(roll_no)
            if is_dup:
                raise ValidationError(error)
            
            # Check name (warning only, don't block)
            is_dup, warning = StudentValidator.check_duplicate_name(name, branch, section)
            if is_dup:
                print(warning)
                response = input("\n   Continue anyway? (yes/no): ").strip().lower()
                if response != 'yes':
                    raise ValidationError("Registration cancelled by user")
        
        return {
            'name': name,
            'rollNo': roll_no,
            'branch': branch,
            'section': section
        }


class AttendanceValidator:
    """Validates attendance data"""
    
    @staticmethod
    def validate_class_selection(branch, section):
        """Validate class selection for attendance"""
        if not branch or not section:
            raise ValidationError("Both branch and section must be selected")
        
        valid, message = Config.validate_branch_section(branch, section)
        if not valid:
            raise ValidationError(message)
        
        return True
    
    @staticmethod
    def check_students_registered(branch, section):
        """Check if any students are registered in the class"""
        db = StudentValidator.load_database()
        
        count = sum(
            1 for info in db.values()
            if info.get('branch') == branch and info.get('section') == section
        )
        
        if count == 0:
            raise ValidationError(
                f"No students registered in {branch}-{section}.\n"
                f"Please register students first using face_capture.py or bulk_capture.py"
            )
        
        return count


# Utility functions
def validate_and_add_student(name, roll_no, branch, section, images_count=0, dataset_path=""):
    """
    Validate and add student to database
    Used by face_capture.py and bulk_capture.py
    """
    from datetime import datetime
    
    try:
        # Validate all data
        validated = StudentValidator.validate_student_data(
            name, roll_no, branch, section, check_duplicates=True
        )
        
        # Generate unique ID
        student_id = StudentValidator.generate_unique_student_id(validated['name'])
        
        # Load database
        db = StudentValidator.load_database()
        
        # Add student
        db[student_id] = {
            "name": validated['name'],
            "rollNo": validated['rollNo'],
            "branch": validated['branch'],
            "section": validated['section'],
            "imagesCount": images_count,
            "registeredDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "datasetPath": dataset_path
        }
        
        # Save database
        with open(Config.STUDENT_DB, 'w', encoding='utf-8') as f:
            json.dump(db, indent=4, fp=f)
        
        print(f"✅ Student added successfully: {validated['name']} ({validated['rollNo']})")
        return True, student_id
        
    except ValidationError as e:
        print(f"\n❌ Validation Error: {e}")
        return False, None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False, None
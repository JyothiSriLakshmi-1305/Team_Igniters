"""
Smart Attendance System - Individual Face Capture
With comprehensive validation and duplicate prevention
"""

import cv2
import os
import time
from config import Config
from validators import validate_and_add_student, StudentValidator, ValidationError


def get_student_info():
    """Get and validate student information"""
    print("=" * 70)
    print("📸 SMART ATTENDANCE - STUDENT FACE CAPTURE")
    print("=" * 70)
    
    # Get student name
    while True:
        name = input("\nEnter student name: ").strip()
        try:
            name = StudentValidator.validate_name(name)
            break
        except ValidationError as e:
            print(f"❌ {e}")
            continue
    
    # Get branch
    print("\n🏢 Select Branch:")
    for i, branch in enumerate(Config.ALLOWED_BRANCHES, 1):
        print(f"  {i}. {branch}")
    
    while True:
        try:
            choice = int(input(f"\nEnter branch number (1-{len(Config.ALLOWED_BRANCHES)}): "))
            branch = Config.ALLOWED_BRANCHES[choice - 1]
            break
        except (ValueError, IndexError):
            print(f"❌ Invalid choice! Please enter 1-{len(Config.ALLOWED_BRANCHES)}")
    
    # Get section
    print("\n📋 Select Section:")
    for i, section in enumerate(Config.ALLOWED_SECTIONS, 1):
        print(f"  {i}. Section {section}")
    
    while True:
        try:
            choice = int(input(f"\nEnter section (1-{len(Config.ALLOWED_SECTIONS)}): "))
            section = Config.ALLOWED_SECTIONS[choice - 1]
            break
        except (ValueError, IndexError):
            print(f"❌ Invalid choice! Please enter 1-{len(Config.ALLOWED_SECTIONS)}")
    
    # Get roll number
    suggested_roll = f"{Config.get_roll_number_prefix(branch, section)}001"
    print(f"\n🎓 Recommended Roll Number Format: {suggested_roll}")
    
    while True:
        roll_no = input(f"Enter roll number: ").strip()
        
        try:
            # Validate format
            roll_no = StudentValidator.validate_roll_number(roll_no, branch, section)
            
            # Check for duplicates
            is_duplicate, error_msg = StudentValidator.check_duplicate_roll_number(roll_no)
            if is_duplicate:
                print(error_msg)
                retry = input("\nTry different roll number? (yes/no): ").strip().lower()
                if retry == 'yes':
                    continue
                else:
                    return None
            
            break
        except ValidationError as e:
            print(f"❌ {e}")
            continue
    
    # Check for duplicate name (warning only)
    is_duplicate, warning = StudentValidator.check_duplicate_name(name, branch, section)
    if is_duplicate:
        print(warning)
        proceed = input("\nProceed anyway? (yes/no): ").strip().lower()
        if proceed != 'yes':
            print("❌ Registration cancelled")
            return None
    
    return {
        'name': name,
        'rollNo': roll_no,
        'branch': branch,
        'section': section
    }


def capture_student_faces():
    """Enhanced face capture with validation"""
    
    # Get student information with validation
    student_info = get_student_info()
    
    if not student_info:
        return
    
    name = student_info['name']
    roll_no = student_info['rollNo']
    branch = student_info['branch']
    section = student_info['section']
    
    # Create dataset directory
    dataset_path = os.path.join(Config.DATASET_PATH, name)
    os.makedirs(dataset_path, exist_ok=True)
    
    # Initialize camera
    print("\n📷 Opening camera...")
    cam = cv2.VideoCapture(Config.CAMERA_INDEX)
    
    if not cam.isOpened():
        print("❌ Cannot open camera!")
        return
    
    # Set camera properties
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
    cam.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
    
    # Load face cascade
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    
    if face_cascade.empty():
        print("❌ Error loading face cascade!")
        cam.release()
        return
    
    required_images = Config.REQUIRED_IMAGES_PER_STUDENT
    saved_count = 0
    frame_skip = Config.IMAGE_CAPTURE_FRAME_SKIP
    detect_counter = 0
    
    print("\n" + "=" * 70)
    print(f"👤 Student: {name}")
    print(f"🎓 Roll No: {roll_no}")
    print(f"🏢 Branch: {branch}")
    print(f"📋 Section: {section}")
    print("=" * 70)
    print(f"📸 Need to capture {required_images} images")
    print("\n💡 INSTRUCTIONS:")
    print("  • Look straight at the camera")
    print("  • Slowly move your head: left, right, up, down")
    print("  • Ensure good lighting")
    print("  • Keep your face in the yellow box")
    print("  • Press 'Q' to quit anytime")
    print("=" * 70)
    print("\n⏳ Starting in 3 seconds...")
    
    time.sleep(3)
    
    try:
        while saved_count < required_images:
            ret, frame = cam.read()
            if not ret:
                print("\n❌ Error reading from camera")
                break
            
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=Config.FACE_DETECTION_SCALE_FACTOR,
                minNeighbors=Config.FACE_DETECTION_MIN_NEIGHBORS,
                minSize=Config.FACE_DETECTION_MIN_SIZE
            )
            
            # Process faces
            face_detected = False
            for (x, y, w, h) in faces:
                face_detected = True
                detect_counter += 1
                
                # Only save every Nth detection for variety
                if detect_counter % frame_skip == 0 and saved_count < required_images:
                    face = gray[y:y+h, x:x+w]
                    
                    # Save face image
                    saved_count += 1
                    filename = f"{dataset_path}/{saved_count}.jpg"
                    cv2.imwrite(filename, face)
                    
                    # Green box for captured
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                    cv2.putText(frame, "✓ CAPTURED!", (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                else:
                    # Yellow box while waiting
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
            
            # Show progress bar
            progress = (saved_count / required_images) * 100
            bar_width = 400
            bar_height = 30
            bar_x = 120
            bar_y = 20
            
            # Background
            cv2.rectangle(frame, (bar_x-5, bar_y-5), (bar_x+bar_width+5, bar_y+bar_height+5),
                         (50, 50, 50), -1)
            
            # Progress bar
            progress_width = int((saved_count / required_images) * bar_width)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x+progress_width, bar_y+bar_height),
                         (0, 255, 0), -1)
            
            # Border
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x+bar_width, bar_y+bar_height),
                         (255, 255, 255), 2)
            
            # Text
            progress_text = f"{saved_count}/{required_images} ({progress:.0f}%)"
            cv2.putText(frame, progress_text, (bar_x+bar_width//2-80, bar_y+22),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Student info
            cv2.putText(frame, f"Student: {name}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Roll No: {roll_no}", (10, 95),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Class: {branch}-{section}", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Instructions
            if not face_detected:
                cv2.putText(frame, "⚠ NO FACE DETECTED - Please face the camera",
                           (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX,
                           0.6, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "✓ Face detected - Keep moving slightly",
                           (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX,
                           0.6, (0, 255, 0), 2)
            
            cv2.imshow("Face Capture - Press Q to Quit", frame)
            
            # Exit on 'q'
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                if saved_count < required_images:
                    print(f"\n⚠️ Only {saved_count} images captured (need {required_images})")
                    print("   This may affect recognition accuracy!")
                    cont = input("   Continue anyway? (yes/no): ").strip().lower()
                    if cont != 'yes':
                        print("❌ Capture cancelled")
                        cam.release()
                        cv2.destroyAllWindows()
                        return
                break
        
        cam.release()
        cv2.destroyAllWindows()
        
        # Minimum images check
        if saved_count < 30:
            print(f"\n❌ ERROR: Only {saved_count} images captured!")
            print("   Minimum 30 images required for accurate recognition.")
            print("   Student NOT saved to database.")
            return
        
        # Add student to database
        success, student_id = validate_and_add_student(
            name, roll_no, branch, section,
            images_count=saved_count,
            dataset_path=dataset_path
        )
        
        if success:
            print("\n" + "=" * 70)
            print("✅ FACE CAPTURE COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print(f"👤 Student Name: {name}")
            print(f"🎓 Roll Number: {roll_no}")
            print(f"🏢 Branch-Section: {branch}-{section}")
            print(f"📸 Images Captured: {saved_count}/{required_images}")
            print(f"📂 Dataset Path: {dataset_path}")
            print(f"💾 Database File: {Config.STUDENT_DB}")
            print("=" * 70)
            print("\n📝 NEXT STEPS:")
            print("  1. Capture more students if needed (run this script again)")
            print("  2. Train the model: python train_model.py")
            print("  3. Start attendance system from dashboard")
            print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n❌ Capture cancelled by user (Ctrl+C)")
        cam.release()
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        capture_student_faces()
    except KeyboardInterrupt:
        print("\n\n❌ Capture cancelled by user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
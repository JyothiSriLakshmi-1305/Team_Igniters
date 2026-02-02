import cv2
import os
import json
from datetime import datetime
import time

STUDENT_DB = "student_database.json"

def load_student_database():
    if os.path.exists(STUDENT_DB):
        with open(STUDENT_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_student_database(db):
    with open(STUDENT_DB, 'w', encoding='utf-8') as f:
        json.dump(db, indent=4, fp=f)

def get_next_roll_number(branch, section, existing_count):
    """Generate sequential roll numbers"""
    prefix = f"{branch}{section}"
    return f"{prefix}{str(existing_count + 1).zfill(3)}"

def bulk_capture_class():
    """Capture entire class in one session"""
    print("=" * 70)
    print("🎓 BULK STUDENT REGISTRATION - CAPTURE ENTIRE CLASS")
    print("=" * 70)
    
    # Get class details
    print("\n🏢 Select Branch:")
    branches = ["CSE", "AIML", "ECE", "EEE", "MECH", "CIVIL"]
    for i, b in enumerate(branches, 1):
        print(f"  {i}. {b}")
    
    while True:
        try:
            branch = branches[int(input("\nEnter branch number (1-6): ")) - 1]
            break
        except:
            print("❌ Invalid choice!")
    
    print("\n📋 Select Section:")
    print("  1. Section A")
    print("  2. Section B")
    
    while True:
        choice = input("\nEnter section (1-2): ")
        if choice in ['1', '2']:
            section = "A" if choice == "1" else "B"
            break
    
    # Get number of students
    print(f"\n👥 How many students in {branch}-{section}?")
    while True:
        try:
            total_students = int(input("Enter number (e.g., 60): "))
            if total_students > 0:
                break
        except:
            pass
        print("❌ Please enter a valid number!")
    
    # Check existing students
    db = load_student_database()
    existing_students = [
        info for info in db.values()
        if info.get('branch') == branch and info.get('section') == section
    ]
    
    if existing_students:
        print(f"\n⚠️  Found {len(existing_students)} existing students in {branch}-{section}")
        print("   Options:")
        print("   1. Continue and add more students")
        print("   2. Start fresh (existing data will remain)")
        choice = input("   Choose (1-2): ")
        if choice != '1':
            print("❌ Operation cancelled")
            return
        start_from = len(existing_students)
    else:
        start_from = 0
    
    print("\n" + "=" * 70)
    print(f"📸 READY TO CAPTURE {total_students} STUDENTS")
    print("=" * 70)
    print(f"Class: {branch}-{section}")
    print(f"Already registered: {start_from}")
    print(f"To capture: {total_students - start_from}")
    print("\n💡 PROCESS:")
    print("  1. Enter student name")
    print("  2. Roll number auto-generated (or manual)")
    print("  3. Capture 50 face images")
    print("  4. Move to next student")
    print("  5. Type 'QUIT' as name to stop early")
    print("=" * 70)
    
    input("\nPress ENTER to start...")
    
    # Initialize camera once for all students
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("❌ Cannot open camera!")
        return
    
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cam.set(cv2.CAP_PROP_FPS, 30)
    
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    
    students_captured = start_from
    
    try:
        for student_num in range(start_from + 1, total_students + 1):
            print("\n" + "=" * 70)
            print(f"📸 STUDENT {student_num} of {total_students}")
            print("=" * 70)
            
            # Get student name
            while True:
                name = input(f"\nEnter student name (or 'QUIT' to stop): ").strip()
                
                if name.upper() == 'QUIT':
                    print("⏹️  Stopping bulk capture...")
                    raise KeyboardInterrupt
                
                if name:
                    break
                print("❌ Name cannot be empty!")
            
            # Generate roll number
            suggested_roll = get_next_roll_number(branch, section, students_captured)
            roll_no = input(f"Roll number [{suggested_roll}]: ").strip() or suggested_roll
            
            # Check for duplicates
            student_id = name.lower().replace(" ", "_")
            if student_id in db:
                print(f"⚠️  Student '{name}' exists! Using: {name}_{student_num}")
                student_id = f"{student_id}_{student_num}"
            
            # Check duplicate roll number
            for sid, info in db.items():
                if info.get('rollNo') == roll_no and sid != student_id:
                    print(f"⚠️  Roll {roll_no} exists! Adding suffix...")
                    roll_no = f"{roll_no}_{student_num}"
                    break
            
            print(f"\n✅ Capturing: {name} ({roll_no})")
            print("⏱️  Get ready... Starting in 3 seconds...")
            time.sleep(3)
            
            # Create dataset directory
            dataset_path = os.path.join("dataset", name)
            os.makedirs(dataset_path, exist_ok=True)
            
            # Capture faces
            required_images = 50
            saved_count = 0
            detect_counter = 0
            frame_skip = 2
            
            print(f"📸 Capturing {required_images} images...")
            
            while saved_count < required_images:
                ret, frame = cam.read()
                if not ret:
                    print("❌ Camera error!")
                    break
                
                frame = cv2.flip(frame, 1)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                faces = face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.2, 
                    minNeighbors=5,
                    minSize=(120, 120)
                )
                
                for (x, y, w, h) in faces:
                    detect_counter += 1
                    
                    if detect_counter % frame_skip == 0 and saved_count < required_images:
                        face = gray[y:y+h, x:x+w]
                        saved_count += 1
                        filename = f"{dataset_path}/{saved_count}.jpg"
                        cv2.imwrite(filename, face)
                        
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                        cv2.putText(frame, "✓ CAPTURED!", (x, y-10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    else:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                
                # Progress bar
                progress = (saved_count / required_images) * 100
                cv2.rectangle(frame, (50, 20), (590, 50), (50, 50, 50), -1)
                cv2.rectangle(frame, (50, 20), (50 + int(540 * saved_count / required_images), 50), 
                             (0, 255, 0), -1)
                cv2.rectangle(frame, (50, 20), (590, 50), (255, 255, 255), 2)
                
                cv2.putText(frame, f"{saved_count}/{required_images} ({progress:.0f}%)", 
                           (200, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.putText(frame, f"Student {student_num}/{total_students}: {name}", 
                           (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"Roll: {roll_no}", 
                           (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.imshow("Bulk Capture - Press Q to skip this student", frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    if saved_count < required_images:
                        skip = input(f"\n⚠️  Only {saved_count} images. Skip student? (yes/no): ")
                        if skip.lower() == 'yes':
                            print("⏭️  Skipping student...")
                            break
                    break
            
            if saved_count >= 30:  # Minimum 30 images required
                # Save to database
                db[student_id] = {
                    "name": name,
                    "rollNo": roll_no,
                    "branch": branch,
                    "section": section,
                    "imagesCount": saved_count,
                    "registeredDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "datasetPath": dataset_path
                }
                save_student_database(db)
                students_captured += 1
                print(f"✅ Saved: {name} ({saved_count} images)")
            else:
                print(f"❌ Insufficient images ({saved_count}). Student not saved.")
            
            # Short break between students
            print("\n⏸️  5 second break before next student...")
            for i in range(5, 0, -1):
                print(f"   {i}...", end='\r')
                time.sleep(1)
            print("   ✅ Ready!     ")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Bulk capture stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cam.release()
        cv2.destroyAllWindows()
        
        print("\n" + "=" * 70)
        print("✅ BULK CAPTURE SESSION COMPLETED")
        print("=" * 70)
        print(f"Class: {branch}-{section}")
        print(f"Students captured: {students_captured} / {total_students}")
        print(f"Database file: {STUDENT_DB}")
        print("\n📝 NEXT STEPS:")
        print("  1. Review captured students: python manage_students.py")
        print("  2. Train the model: python train_model.py")
        print("  3. Test recognition: python recognize_attendance.py")
        print("=" * 70)

if __name__ == "__main__":
    try:
        bulk_capture_class()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
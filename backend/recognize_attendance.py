"""
Smart Attendance System - Face Recognition
Fixed camera with accurate attendance tracking
"""

import cv2
import csv
import os
import sys
import json
import time
from datetime import datetime
from collections import deque
from config import Config


def load_student_database():
    """Load student database"""
    if os.path.exists(Config.STUDENT_DB):
        try:
            with open(Config.STUDENT_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def batch_write_attendance(queue, filename):
    """Write attendance records in batch"""
    if not queue:
        return
    
    try:
        with open(filename, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            while queue:
                writer.writerow(queue.popleft())
    except Exception as e:
        print(f"❌ Error writing attendance: {e}")


print("=" * 70)
print("🎯 Smart Attendance System - Face Recognition")
print("=" * 70)

# Get branch and section from command line
if len(sys.argv) < 3:
    print("❌ Error: Branch and Section arguments required")
    print("Usage: python recognize_attendance.py <BRANCH> <SECTION>")
    sys.exit(1)

branch = sys.argv[1].upper()
section = sys.argv[2].upper()

print(f"✅ Branch: {branch}")
print(f"✅ Section: {section}")

# Load student database
student_db = load_student_database()
print(f"✅ Loaded database with {len(student_db)} students")

# Load trained recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()

if not os.path.exists(Config.TRAINER_MODEL):
    print(f"❌ Error: {Config.TRAINER_MODEL} not found. Please train the model first.")
    sys.exit(1)

try:
    recognizer.read(Config.TRAINER_MODEL)
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    sys.exit(1)

# Load face cascade
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

if face_cascade.empty():
    print("❌ Error: Could not load face cascade")
    sys.exit(1)

print("✅ Face cascade loaded")

# Load label mapping and student info
label_map = {}
name_to_info = {}
label_id = 0

if not os.path.exists(Config.DATASET_PATH):
    print(f"❌ Error: {Config.DATASET_PATH} folder not found")
    sys.exit(1)

for person_name in os.listdir(Config.DATASET_PATH):
    person_folder = os.path.join(Config.DATASET_PATH, person_name)
    if os.path.isdir(person_folder):
        label_map[label_id] = person_name
        
        # Find student info in database
        student_id = person_name.lower().replace(" ", "_")
        if student_id in student_db:
            name_to_info[person_name] = student_db[student_id]
        else:
            # Search by name (case insensitive)
            found = False
            for sid, info in student_db.items():
                if info.get('name', '').lower() == person_name.lower():
                    name_to_info[person_name] = info
                    found = True
                    break
            
            if not found:
                name_to_info[person_name] = {
                    'rollNo': 'N/A',
                    'branch': 'UNKNOWN',
                    'section': 'UNKNOWN'
                }
        
        label_id += 1

print(f"✅ Loaded {len(label_map)} students from dataset")

# Filter students for this class
class_students = {
    name: info for name, info in name_to_info.items()
    if info.get('branch') == branch and info.get('section') == section
}

if not class_students:
    print(f"⚠️ WARNING: No students found for {branch}-{section} in dataset!")
    print("   Students will be marked but shown as 'Wrong Class'")
else:
    print(f"✅ {len(class_students)} students belong to {branch}-{section}")

# Initialize attendance file
if not os.path.exists(Config.ATTENDANCE_CSV):
    with open(Config.ATTENDANCE_CSV, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "RollNo", "Branch", "Section", "Date", "Time"])
    print("✅ Created new attendance.csv file")

# Tracking variables
marked_names = set()
recognition_cooldown = {}
attendance_queue = deque()

# Start camera
print("🎥 Opening camera...")
cam = cv2.VideoCapture(Config.CAMERA_INDEX)

if not cam.isOpened():
    print("❌ Error: Cannot open camera")
    sys.exit(1)

# Set camera properties for stable feed
cam.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
cam.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
cam.set(cv2.CAP_PROP_BUFFERSIZE, Config.CAMERA_BUFFER_SIZE)

print(f"✅ Camera opened successfully")
print(f"📸 Starting attendance for {branch}-{section}")
print("=" * 70)
print("💡 INSTRUCTIONS:")
print("  • Students should look at the camera")
print("  • Green box = Recognized and marked")
print("  • Orange box = Wrong class")
print("  • Red box = Unknown face")
print("  • Press 'Q' to stop")
print("=" * 70)

# FPS control
target_fps = Config.DISPLAY_TARGET_FPS
frame_time = 1.0 / target_fps
last_frame_time = time.time()

# Process every Nth frame
process_every_n_frames = 2
frame_count = 0

# Store last detection results
last_detection_results = []

try:
    while True:
        ret, frame = cam.read()
        if not ret:
            print("❌ Error: Cannot read from camera")
            break

        frame_count += 1
        
        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
        
        current_time = datetime.now()
        
        # Process face detection only every N frames
        should_process = (frame_count % process_every_n_frames == 0)
        
        if should_process:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=Config.FACE_DETECTION_SCALE_FACTOR,
                minNeighbors=Config.FACE_DETECTION_MIN_NEIGHBORS,
                minSize=Config.FACE_DETECTION_MIN_SIZE
            )
            
            # Store results for next frames
            last_detection_results = []
            
            for (x, y, w, h) in faces:
                face_img = gray[y:y+h, x:x+w]
                
                try:
                    label, confidence = recognizer.predict(face_img)
                except:
                    continue

                result = {
                    'bbox': (x, y, w, h),
                    'name': 'Unknown',
                    'roll_no': '',
                    'color': (0, 0, 255),  # Red
                    'status': 'unknown',
                    'confidence': confidence
                }

                if confidence < Config.RECOGNITION_CONFIDENCE_THRESHOLD:
                    name = label_map.get(label, "Unknown")
                    student_info = name_to_info.get(name, {})
                    roll_no = student_info.get('rollNo', 'N/A')
                    student_branch = student_info.get('branch', 'UNKNOWN')
                    student_section = student_info.get('section', 'UNKNOWN')
                    
                    result['name'] = name
                    result['roll_no'] = roll_no
                    
                    # Check if student belongs to this class
                    if student_branch == branch and student_section == section:
                        result['color'] = (0, 255, 0)  # Green
                        result['status'] = 'correct_class'
                        
                        # Check cooldown
                        last_mark_time = recognition_cooldown.get(name)
                        time_since_last_mark = 999
                        if last_mark_time:
                            time_since_last_mark = (current_time - last_mark_time).total_seconds()
                        
                        # Mark attendance (once per session or after cooldown)
                        if name not in marked_names:
                            now = datetime.now()
                            date_str = now.strftime("%Y-%m-%d")
                            time_str = now.strftime("%H:%M:%S")
                            
                            # Add to queue
                            attendance_queue.append([name, roll_no, branch, section, date_str, time_str])
                            
                            marked_names.add(name)
                            recognition_cooldown[name] = current_time
                            
                            print(f"✅ MARKED: {name} ({roll_no}) | {branch}-{section} | {time_str}")
                        
                        result['marked'] = (name in marked_names)
                    else:
                        result['color'] = (0, 165, 255)  # Orange
                        result['status'] = 'wrong_class'
                        result['correct_class'] = f"{student_branch}-{student_section}"
                
                last_detection_results.append(result)
        
        # Draw ALL detections on EVERY frame
        for result in last_detection_results:
            x, y, w, h = result['bbox']
            name = result['name']
            color = result['color']
            status = result['status']
            
            # Draw rectangle
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3 if status == 'correct_class' else 2)
            
            # Draw labels
            if status == 'correct_class':
                cv2.putText(frame, name, (x, y-30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                cv2.putText(frame, result['roll_no'], (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                if result.get('marked'):
                    cv2.putText(frame, "MARKED", (x+w-100, y+20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            elif status == 'wrong_class':
                cv2.putText(frame, f"{name} - Wrong Class!", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                cv2.putText(frame, f"Should be: {result.get('correct_class', '')}", (x, y+h+20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            else:  # Unknown
                cv2.putText(frame, "Unknown", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        # Display info
        cv2.putText(frame, f"Class: {branch}-{section} | Present: {len(marked_names)}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Press Q to Stop", (10, frame.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Show frame
        cv2.imshow(f"Smart Attendance - {branch}-{section}", frame)

        # FPS control
        elapsed = time.time() - last_frame_time
        wait_time = max(1, int((frame_time - elapsed) * 1000))
        
        key = cv2.waitKey(wait_time) & 0xFF
        if key == ord('q') or key == ord('Q'):
            print("\n⏹️ Stopping by user request...")
            break
        
        last_frame_time = time.time()
        
        # Batch write every N frames
        if frame_count % Config.BATCH_WRITE_INTERVAL == 0 and attendance_queue:
            batch_write_attendance(attendance_queue, Config.ATTENDANCE_CSV)

except KeyboardInterrupt:
    print("\n⏹️ Stopped by user (Ctrl+C)")
except Exception as e:
    print(f"\n❌ Error during recognition: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Final batch write
    if attendance_queue:
        batch_write_attendance(attendance_queue, Config.ATTENDANCE_CSV)
    
    # Release resources
    cam.release()
    cv2.destroyAllWindows()

print("\n" + "=" * 70)
print("✅ ATTENDANCE SESSION COMPLETED")
print("=" * 70)
print(f"📊 Class: {branch}-{section}")
print(f"👥 Total Present: {len(marked_names)}")

if marked_names:
    print("\n📋 Students Present:")
    for i, name in enumerate(sorted(marked_names), 1):
        info = name_to_info.get(name, {})
        roll = info.get('rollNo', 'N/A')
        print(f"   {i}. {name} ({roll})")
else:
    print("\n⚠️ No students marked present")

print("=" * 70)
print(f"💾 Attendance saved to: {Config.ATTENDANCE_CSV}")
print("=" * 70)
"""
Smart Attendance System - Model Training
Train face recognition model from captured images
"""

import cv2
import numpy as np
import os
from config import Config

print("=" * 70)
print("🔄 SMART ATTENDANCE - MODEL TRAINING")
print("=" * 70)

# Check if dataset folder exists
if not os.path.exists(Config.DATASET_PATH):
    print(f"❌ Error: Dataset folder not found: {Config.DATASET_PATH}")
    print("   Please capture student faces first using:")
    print("   - python face_capture.py OR")
    print("   - python bulk_capture.py")
    exit(1)

# Create recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()

faces = []
labels = []
label_map = {}
label_id = 0

print(f"\n📂 Loading images from: {Config.DATASET_PATH}")
print("-" * 70)

total_images = 0
students_with_insufficient_images = []

# Load all student images
for person_name in sorted(os.listdir(Config.DATASET_PATH)):
    person_folder = os.path.join(Config.DATASET_PATH, person_name)

    if not os.path.isdir(person_folder):
        continue

    label_map[label_id] = person_name
    
    # Count images for this student
    image_files = [f for f in os.listdir(person_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    image_count = len(image_files)
    
    if image_count < 30:
        students_with_insufficient_images.append((person_name, image_count))
        print(f"⚠️  {person_name}: {image_count} images (⚠️ Less than 30!)")
    else:
        print(f"✅ {person_name}: {image_count} images")

    # Load images
    for image_name in image_files:
        image_path = os.path.join(person_folder, image_name)

        gray_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if gray_img is None:
            print(f"   ⚠️ Could not load: {image_name}")
            continue

        faces.append(gray_img)
        labels.append(label_id)
        total_images += 1

    label_id += 1

print("-" * 70)

# Check if enough data
if not faces:
    print("\n❌ Error: No face images found!")
    print("   Please capture student faces first.")
    exit(1)

if len(label_map) < 2:
    print("\n⚠️ Warning: Only 1 student found. Need at least 2 for training.")
    print("   The model will be trained but may not be very useful.")

# Show warnings for insufficient images
if students_with_insufficient_images:
    print("\n⚠️ WARNING: Some students have fewer than 30 images:")
    for name, count in students_with_insufficient_images:
        print(f"   • {name}: {count} images")
    print("   This may reduce recognition accuracy for these students.")
    print("   Recommended: Recapture with 50+ images per student.")

print(f"\n📊 Training Summary:")
print(f"   Students: {len(label_map)}")
print(f"   Total Images: {total_images}")
print(f"   Average Images per Student: {total_images / len(label_map):.1f}")

# Create trainer directory
if not os.path.exists(Config.TRAINER_PATH):
    os.makedirs(Config.TRAINER_PATH)

# Train the model
print(f"\n🔄 Training model...")
print("   This may take 1-5 minutes depending on dataset size...")

try:
    recognizer.train(faces, np.array(labels))
    recognizer.save(Config.TRAINER_MODEL)
    
    print("\n" + "=" * 70)
    print("✅ MODEL TRAINED SUCCESSFULLY!")
    print("=" * 70)
    print(f"💾 Model saved to: {Config.TRAINER_MODEL}")
    print(f"👥 Trained on {len(label_map)} students")
    print(f"📸 Using {total_images} face images")
    
    print("\n📋 Student Labels:")
    for lid, name in sorted(label_map.items()):
        print(f"   {lid}: {name}")
    
    print("\n" + "=" * 70)
    print("📝 NEXT STEPS:")
    print("  1. Start backend: python app.py")
    print("  2. Open frontend: index.html")
    print("  3. Login and start attendance recognition")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ Error during training: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
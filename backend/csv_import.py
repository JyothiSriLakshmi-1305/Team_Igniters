import csv
import json
import os
from datetime import datetime

STUDENT_DB = "student_database.json"

def load_student_database():
    if os.path.exists(STUDENT_DB):
        with open(STUDENT_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_student_database(db):
    with open(STUDENT_DB, 'w', encoding='utf-8') as f:
        json.dump(db, indent=4, fp=f)

def create_sample_csv():
    """Create a sample CSV template"""
    filename = "student_import_template.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'RollNo', 'Branch', 'Section'])
        writer.writerow(['John Doe', 'AIML001', 'AIML', 'A'])
        writer.writerow(['Jane Smith', 'AIML002', 'AIML', 'A'])
        writer.writerow(['Mike Johnson', 'CSE001', 'CSE', 'B'])
    
    print(f"✅ Created sample template: {filename}")
    print("   Edit this file with your student data, then import it.")

def import_students_from_csv():
    """Import students from CSV file"""
    print("=" * 70)
    print("📥 IMPORT STUDENTS FROM CSV")
    print("=" * 70)
    
    # Ask for CSV file
    csv_file = input("\nEnter CSV filename (or press ENTER for 'students.csv'): ").strip()
    if not csv_file:
        csv_file = "students.csv"
    
    if not os.path.exists(csv_file):
        print(f"\n❌ File '{csv_file}' not found!")
        create = input("\n   Create sample template? (yes/no): ").strip().lower()
        if create == 'yes':
            create_sample_csv()
        return
    
    # Load existing database
    db = load_student_database()
    initial_count = len(db)
    
    # Read CSV
    print(f"\n📖 Reading {csv_file}...")
    
    imported = 0
    skipped = 0
    errors = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate headers
            required_headers = ['Name', 'RollNo', 'Branch', 'Section']
            if not all(header in reader.fieldnames for header in required_headers):
                print(f"❌ CSV must have headers: {', '.join(required_headers)}")
                print(f"   Found: {', '.join(reader.fieldnames)}")
                return
            
            print("\n📝 Processing students...")
            
            for row_num, row in enumerate(reader, start=2):
                name = row.get('Name', '').strip()
                roll_no = row.get('RollNo', '').strip()
                branch = row.get('Branch', '').strip().upper()
                section = row.get('Section', '').strip().upper()
                
                # Validate data
                if not name or not roll_no or not branch or not section:
                    errors.append(f"Row {row_num}: Missing required fields")
                    skipped += 1
                    continue
                
                # Validate branch and section
                valid_branches = ['CSE', 'AIML', 'ECE', 'EEE', 'MECH', 'CIVIL']
                valid_sections = ['A', 'B']
                
                if branch not in valid_branches:
                    errors.append(f"Row {row_num}: Invalid branch '{branch}'")
                    skipped += 1
                    continue
                
                if section not in valid_sections:
                    errors.append(f"Row {row_num}: Invalid section '{section}'")
                    skipped += 1
                    continue
                
                # Check for duplicate roll number
                duplicate = False
                for student_id, info in db.items():
                    if info.get('rollNo') == roll_no:
                        errors.append(f"Row {row_num}: Duplicate roll number '{roll_no}'")
                        skipped += 1
                        duplicate = True
                        break
                
                if duplicate:
                    continue
                
                # Create student ID
                student_id = name.lower().replace(" ", "_")
                
                # Handle duplicate names
                if student_id in db:
                    counter = 1
                    while f"{student_id}_{counter}" in db:
                        counter += 1
                    student_id = f"{student_id}_{counter}"
                
                # Add to database
                db[student_id] = {
                    "name": name,
                    "rollNo": roll_no,
                    "branch": branch,
                    "section": section,
                    "imagesCount": 0,  # No images yet - need to capture
                    "registeredDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "datasetPath": "",
                    "imported": True
                }
                
                imported += 1
                print(f"   ✅ {name} ({roll_no}) - {branch}-{section}")
        
        # Save database
        save_student_database(db)
        
        print("\n" + "=" * 70)
        print("✅ IMPORT COMPLETED")
        print("=" * 70)
        print(f"Total in database before: {initial_count}")
        print(f"Successfully imported: {imported}")
        print(f"Skipped/Errors: {skipped}")
        print(f"Total in database now: {len(db)}")
        
        if errors:
            print(f"\n⚠️  Errors found ({len(errors)}):")
            for error in errors[:10]:  # Show first 10 errors
                print(f"   • {error}")
            if len(errors) > 10:
                print(f"   ... and {len(errors) - 10} more errors")
        
        if imported > 0:
            print("\n⚠️  IMPORTANT: Students imported but NO FACE DATA yet!")
            print("   You must capture face images for recognition to work.")
            print("\n📸 Options to capture faces:")
            print("   1. Bulk capture: python bulk_capture.py")
            print("   2. Individual: python face_capture.py")
        
        print("=" * 70)
    
    except Exception as e:
        print(f"\n❌ Error reading CSV: {e}")
        import traceback
        traceback.print_exc()

def export_database_to_csv():
    """Export current database to CSV"""
    db = load_student_database()
    
    if not db:
        print("❌ No students in database to export")
        return
    
    filename = f"student_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'RollNo', 'Branch', 'Section', 'Images', 'Registered'])
        
        for student_id, info in sorted(db.items(), key=lambda x: x[1].get('rollNo', '')):
            writer.writerow([
                info['name'],
                info['rollNo'],
                info['branch'],
                info['section'],
                info.get('imagesCount', 0),
                info.get('registeredDate', 'N/A')
            ])
    
    print(f"✅ Database exported to: {filename}")

def main():
    while True:
        print("\n" + "=" * 70)
        print("📊 STUDENT DATA MANAGEMENT")
        print("=" * 70)
        print("1. Import students from CSV")
        print("2. Export database to CSV")
        print("3. Create sample CSV template")
        print("4. View database statistics")
        print("5. Exit")
        print("=" * 70)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            import_students_from_csv()
        elif choice == '2':
            export_database_to_csv()
        elif choice == '3':
            create_sample_csv()
        elif choice == '4':
            db = load_student_database()
            print(f"\n📊 Database Statistics:")
            print(f"   Total students: {len(db)}")
            
            # Count by class
            class_counts = {}
            no_images = 0
            for info in db.values():
                class_key = f"{info['branch']}-{info['section']}"
                class_counts[class_key] = class_counts.get(class_key, 0) + 1
                if info.get('imagesCount', 0) == 0:
                    no_images += 1
            
            print(f"\n   Students by class:")
            for class_key, count in sorted(class_counts.items()):
                print(f"      {class_key}: {count}")
            
            print(f"\n   ⚠️  Students without face images: {no_images}")
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
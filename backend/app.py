"""
Smart Attendance System - Flask Backend API
Complete API with duplicate prevention and accurate attendance
"""

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import csv
import os
import json
import sys
import subprocess
import shutil
from datetime import datetime
from config import Config
from validators import StudentValidator, AttendanceValidator, ValidationError

app = Flask(__name__)
CORS(app)

# Global variable to track attendance status
attendance_running = False


def load_student_database():
    """Load student database from JSON"""
    if os.path.exists(Config.STUDENT_DB):
        try:
            with open(Config.STUDENT_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading database: {e}")
            return {}
    return {}


def count_students_in_class(branch, section):
    """Count actual registered students in a specific class"""
    db = load_student_database()
    count = 0
    for student_id, info in db.items():
        if info.get('branch') == branch and info.get('section') == section:
            count += 1
    return count


def backup_database():
    """Backup student database and attendance CSV"""
    if not Config.AUTO_BACKUP_ENABLED:
        return
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Backup student database
        if os.path.exists(Config.STUDENT_DB):
            backup_file = os.path.join(
                Config.BACKUP_PATH,
                f"student_database_{timestamp}.json"
            )
            shutil.copy2(Config.STUDENT_DB, backup_file)
            print(f"✅ Database backed up: {backup_file}")
        
        # Backup attendance CSV
        if os.path.exists(Config.ATTENDANCE_CSV):
            backup_file = os.path.join(
                Config.BACKUP_PATH,
                f"attendance_{timestamp}.csv"
            )
            shutil.copy2(Config.ATTENDANCE_CSV, backup_file)
        
        # Clean old backups (keep last 10)
        cleanup_old_backups()
        
    except Exception as e:
        print(f"Backup error: {e}")


def cleanup_old_backups():
    """Remove old backup files, keep last N"""
    try:
        backups = [
            f for f in os.listdir(Config.BACKUP_PATH)
            if f.startswith("student_database_") or f.startswith("attendance_")
        ]
        
        backups.sort(reverse=True)
        
        # Remove backups beyond limit
        for backup in backups[Config.MAX_BACKUP_FILES:]:
            os.remove(os.path.join(Config.BACKUP_PATH, backup))
    except Exception as e:
        print(f"Cleanup error: {e}")


@app.route("/")
def home():
    """API health check"""
    db = load_student_database()
    
    return jsonify({
        "message": "Smart Attendance Backend Running",
        "status": "active",
        "version": "2.0",
        "totalStudents": len(db),
        "config": {
            "branches": Config.ALLOWED_BRANCHES,
            "sections": Config.ALLOWED_SECTIONS
        }
    })


@app.route("/api/attendance/today", methods=['GET'])
def get_today_attendance():
    """
    Get today's attendance for a specific class
    Query params: branch, section
    """
    try:
        branch = request.args.get('branch', '').upper()
        section = request.args.get('section', '').upper()
        
        # Validate inputs
        try:
            AttendanceValidator.validate_class_selection(branch, section)
        except ValidationError as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400
        
        print(f"📊 Loading attendance for: {branch}-{section}")
        
        today = str(datetime.now().date())
        records = []
        present_count = 0
        
        # Get actual student count from database
        total_students = count_students_in_class(branch, section)
        
        if total_students == 0:
            return jsonify({
                "success": False,
                "error": f"No students registered in {branch}-{section}"
            }), 404
        
        # Read attendance records
        if os.path.exists(Config.ATTENDANCE_CSV):
            with open(Config.ATTENDANCE_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Track unique students (prevent duplicate counting)
                present_students = set()
                
                for row in reader:
                    row_date = str(row.get('Date', '')).strip()
                    row_branch = str(row.get('Branch', '')).strip()
                    row_section = str(row.get('Section', '')).strip()
                    roll_no = str(row.get('RollNo', '')).strip()
                    
                    if (row_date == today and 
                        row_branch == branch and 
                        row_section == section):
                        
                        # Only count unique students (in case of duplicate entries)
                        if roll_no not in present_students:
                            present_students.add(roll_no)
                            
                            records.append({
                                'name': row.get('Name', 'Unknown'),
                                'rollNo': roll_no,
                                'date': row.get('Date', ''),
                                'time': row.get('Time', '')
                            })
                
                present_count = len(present_students)
        
        absent_count = total_students - present_count
        percentage = (present_count / total_students * 100) if total_students > 0 else 0
        
        print(f"✅ Found {present_count}/{total_students} present for {branch}-{section} ({percentage:.1f}%)")
        
        return jsonify({
            "success": True,
            "data": {
                "class": f"{branch}-{section}",
                "date": today,
                "total": total_students,
                "present": present_count,
                "absent": absent_count,
                "percentage": round(percentage, 2),
                "records": records
            }
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/class/stats", methods=['GET'])
def get_class_stats():
    """Get statistics for a specific class"""
    try:
        branch = request.args.get('branch', '').upper()
        section = request.args.get('section', '').upper()
        
        db = load_student_database()
        
        students = []
        for student_id, info in db.items():
            if info.get('branch') == branch and info.get('section') == section:
                students.append({
                    'name': info['name'],
                    'rollNo': info['rollNo'],
                    'images': info.get('imagesCount', 0),
                    'registered': info.get('registeredDate', 'N/A')
                })
        
        return jsonify({
            "success": True,
            "data": {
                "class": f"{branch}-{section}",
                "totalStudents": len(students),
                "students": sorted(students, key=lambda x: x['rollNo'])
            }
        })
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/classes/summary", methods=['GET'])
def get_classes_summary():
    """Get summary of all classes with student counts"""
    try:
        db = load_student_database()
        
        # Count students by class
        class_counts = {}
        for student_id, info in db.items():
            branch = info.get('branch', 'UNKNOWN')
            section = info.get('section', 'UNKNOWN')
            class_key = f"{branch}-{section}"
            class_counts[class_key] = class_counts.get(class_key, 0) + 1
        
        # Format response
        classes = []
        for class_key, count in sorted(class_counts.items()):
            if '-' in class_key:
                branch, section = class_key.split('-')
                classes.append({
                    'branch': branch,
                    'section': section,
                    'class': class_key,
                    'students': count
                })
        
        return jsonify({
            "success": True,
            "data": {
                "totalClasses": len(classes),
                "totalStudents": len(db),
                "classes": classes
            }
        })
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/attendance/start", methods=['POST'])
def start_attendance():
    """Start attendance recognition system"""
    global attendance_running
    
    try:
        data = request.json
        branch = data.get('branch', '').upper()
        section = data.get('section', '').upper()
        
        print(f"🎯 Start request - Branch: '{branch}', Section: '{section}'")
        
        # Validate class selection
        try:
            AttendanceValidator.validate_class_selection(branch, section)
        except ValidationError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400
        
        # Check if students are registered
        try:
            student_count = AttendanceValidator.check_students_registered(branch, section)
        except ValidationError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400
        
        # Check if already running
        if attendance_running:
            return jsonify({
                "success": False,
                "message": "Attendance system already running. Please stop it first."
            }), 400
        
        # Check if trainer model exists
        if not os.path.exists(Config.TRAINER_MODEL):
            return jsonify({
                "success": False,
                "message": "Model not trained! Please run: python train_model.py"
            }), 400
        
        # Create batch file to run recognition script
        batch_content = f"""@echo off
cd /d "{os.getcwd()}"
python recognize_attendance.py {branch} {section}
"""
        
        batch_file = "run_attendance.bat"
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        print(f"✅ Created batch file: {batch_file}")
        
        # Launch recognition system
        if sys.platform == 'win32':
            subprocess.Popen(
                ['cmd', '/c', 'start', 'cmd', '/k', batch_file],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            subprocess.Popen(['python', 'recognize_attendance.py', branch, section])
        
        attendance_running = True
        
        print(f"✅ Started attendance for {branch}-{section} ({student_count} students)")
        
        return jsonify({
            "success": True,
            "message": f"Attendance started for {branch}-{section}",
            "studentCount": student_count
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/attendance/stop", methods=['POST'])
def stop_attendance():
    """Stop attendance recognition"""
    global attendance_running
    
    try:
        attendance_running = False
        
        print("⏹️ Attendance stopped (close the camera window manually)")
        
        return jsonify({
            "success": True,
            "message": "Attendance stopped. Please close the camera window."
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/attendance/export", methods=['GET'])
def export_attendance():
    """Export attendance records as CSV"""
    try:
        branch = request.args.get('branch', '').upper()
        section = request.args.get('section', '').upper()
        
        if not os.path.exists(Config.ATTENDANCE_CSV):
            return jsonify({
                "success": False,
                "error": "Attendance file not found"
            }), 404
        
        # Create filtered CSV
        timestamp = datetime.now().strftime('%Y%m%d')
        filtered_file = os.path.join(
            Config.BACKUP_PATH,
            f"attendance_{branch}_{section}_{timestamp}.csv"
        )
        
        with open(Config.ATTENDANCE_CSV, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            with open(filtered_file, 'w', newline='', encoding='utf-8') as outfile:
                fieldnames = reader.fieldnames
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in reader:
                    if row.get('Branch', '') == branch and row.get('Section', '') == section:
                        writer.writerow(row)
        
        return send_file(
            filtered_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'attendance_{branch}_{section}_{timestamp}.csv'
        )
        
    except Exception as e:
        print(f"❌ Export error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/backup/create", methods=['POST'])
def create_backup():
    """Manually trigger backup"""
    try:
        backup_database()
        return jsonify({
            "success": True,
            "message": "Backup created successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 SMART ATTENDANCE SYSTEM - BACKEND API")
    print("=" * 70)
    print(f"📂 Working directory: {os.getcwd()}")
    print(f"🐍 Python: {sys.executable}")
    print(f"⚙️  Configuration: {Config.__name__}")
    
    # Create necessary directories
    Config.create_directories()
    
    # Check student database
    db = load_student_database()
    print(f"👥 Total students registered: {len(db)}")
    
    # Show class summary
    class_counts = {}
    for info in db.values():
        branch = info.get('branch', 'UNKNOWN')
        section = info.get('section', 'UNKNOWN')
        class_key = f"{branch}-{section}"
        class_counts[class_key] = class_counts.get(class_key, 0) + 1
    
    if class_counts:
        print("📊 Students by class:")
        for class_key, count in sorted(class_counts.items()):
            print(f"   {class_key}: {count} students")
    else:
        print("⚠️  No students registered yet")
        print("   Run: python face_capture.py OR python bulk_capture.py")
    
    # Check if model is trained
    if os.path.exists(Config.TRAINER_MODEL):
        print("✅ Model trained and ready")
    else:
        print("⚠️  Model not trained yet")
        print("   Run: python train_model.py")
    
    print("=" * 70)
    print(f"🌐 Starting API server on {Config.API_HOST}:{Config.API_PORT}")
    print("=" * 70)
    
    app.run(
        debug=Config.API_DEBUG,
        host=Config.API_HOST,
        port=Config.API_PORT,
        use_reloader=False
    )
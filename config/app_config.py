import os
import sys
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def show_notification(title, medicines):
    print("\n" + "="*60)
    print(f"{title} ({datetime.now().strftime('%H:%M')})")
    print("="*60)
    
    for medicine in medicines:
        print(f"\n• {medicine['name']}")
        print(f"  ⏱ เวลา: {medicine['taken_time']}")
        if medicine.get('dosage'):
            print(f"  ▪ ขนาด: {medicine['dosage']}")
        if medicine.get('uses'):
            print(f"  ▪ สรรพคุณ: {', '.join(medicine['uses'])}")
    
    print("\n" + "="*60 + "\n")
    print("\a")

def load_modules():
    print("🚀 กำลังเริ่มต้นระบบ Medicine Robot...")
    print("📦 กำลังโหลด modules...\n")
    
    from scripts.daily_routine import MedicineReminder
    print("  ✓ Medicine Reminder loaded")
    
    from module.camera_manager import shared_camera
    print("  ✓ Camera Manager loaded")
    
    from module.fall_detection import run_fall_detection
    print("  ✓ Fall Detection loaded")
    
    from gui.web_app import app
    print("  ✓ Web App loaded")

    return {
        'MedicineReminder': MedicineReminder,
        'shared_camera': shared_camera,
        'run_fall_detection': run_fall_detection,
        'run_face_recognition': run_face_recognition_lazy,
        'app': app
    }

def run_face_recognition_lazy():
    try:
        print("  ⏳ Loading Face Recognition (in background)...", flush=True)
        from module.face_recognition import run_face_recognition
        print("  ✓ Face Recognition loaded", flush=True)
        run_face_recognition()
    except Exception as e:
        print(f"⚠️ [Face Recognition Error] {e}", flush=True)

def print_startup_message():
    print("\n" + "="*50)
    print("🌐 เปิด Web Browser แล้ว: http://127.0.0.1:5000")
    print("⚕  Medicine Robot is running...")
    print("🚨 Fall Detection is active...")
    print("👤 Face Recognition is active...")
    print("❌ กด Ctrl+C เพื่อหยุดการทำงาน")
    print("="*50 + "\n")

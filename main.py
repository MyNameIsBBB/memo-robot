import sys
import os
import threading
import time
import webbrowser

sys.pycache_prefix = os.path.join(os.path.dirname(__file__), 'caches')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from config.app_config import show_notification, load_modules, print_startup_message

def run_reminder(modules):
    reminder = modules['MedicineReminder'](notification_callback=show_notification)
    reminder.run()

def run_fall_detection_module(modules):
    try:
        modules['run_fall_detection']()
    except Exception as e:
        print(f"⚠️ [Fall Detection Error] {e}")

def run_face_recognition_module(modules):
    try:
        print("  ⏳ Loading Face Recognition (in background)...")
        from module.face_recognition import run_face_recognition
        print("  ✓ Face Recognition loaded")
        run_face_recognition()
    except Exception as e:
        print(f"⚠️ [Face Recognition Error] {e}")

def open_browser():
    time.sleep(5)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == "__main__":
    modules = load_modules()
    
    print("\n🔧 กำลังเริ่ม threads...\n")
    
    try:
        modules['shared_camera'].start()
        print("  ✓ Camera started")
    except Exception as e:
        print(f"  ✗ Camera error: {e}")
    
    reminder_thread = threading.Thread(target=run_reminder, args=(modules,), daemon=True)
    reminder_thread.start()
    print("  ✓ Medicine Reminder started")

    fall_detection_thread = threading.Thread(target=run_fall_detection_module, args=(modules,), daemon=True)
    fall_detection_thread.start()
    print("  ✓ Fall Detection started")

    face_recognition_thread = threading.Thread(target=run_face_recognition_module, args=(modules,), daemon=True)
    face_recognition_thread.start()
    print("  ✓ Face Recognition started")

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    print_startup_message()
    
    try:
        modules['app'].run(debug=False, host='127.0.0.1', port=5000)
    except KeyboardInterrupt:
        print("\n👋 ปิดระบบ Medicine Robot")
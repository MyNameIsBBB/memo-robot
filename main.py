import sys
import os
import threading
import time
import webbrowser
import cv2

sys.pycache_prefix = os.path.join(os.path.dirname(__file__), 'caches')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from config.app_config import show_notification, load_modules, print_startup_message

def run_reminder(modules):
    reminder = modules['MedicineReminder'](notification_callback=show_notification)
    reminder.run()

def run_flask(modules):
    try:
        modules['app'].run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
    except Exception as e:
        print(f"⚠️ [Flask Error] {e}")

def open_browser():
    time.sleep(5)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == "__main__":
    modules = load_modules()
    
    print("\n🔧 กำลังเริ่ม threads...\n")
    
    try:
        modules['shared_camera'].start()
        print("  ✓ Camera started")
        time.sleep(1)
    except Exception as e:
        print(f"  ✗ Camera error: {e}")
    
    reminder_thread = threading.Thread(target=run_reminder, args=(modules,), daemon=True)
    reminder_thread.start()
    print("  ✓ Medicine Reminder started")

    flask_thread = threading.Thread(target=run_flask, args=(modules,), daemon=True)
    flask_thread.start()
    print("  ✓ Flask Web started")

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    print_startup_message()
    
    print("[Main] Starting OpenCV windows (press 'q' in any window to quit)...\n")
    
    from module.fall_detection import FallDetector
    from module.face_recognition import FaceRecognizer
    
    fall_detector = FallDetector()
    face_recognizer = FaceRecognizer()
    
    try:
        while True:
            frame = modules['shared_camera'].get_frame()
            
            if frame is not None:
                fall_frame = fall_detector.process_frame(frame.copy())
                face_frame = face_recognizer.process_frame(frame.copy())
                
                if fall_frame is not None:
                    cv2.imshow("Fall Detection", fall_frame)
                
                if face_frame is not None:
                    cv2.imshow("Face Recognition", face_frame)
            
            key = cv2.waitKey(1)
            if key == ord('q'):
                break
                
    except KeyboardInterrupt:
        pass
    
    print("\n👋 ปิดระบบ Medicine Robot")
    cv2.destroyAllWindows()
    modules['shared_camera'].stop()
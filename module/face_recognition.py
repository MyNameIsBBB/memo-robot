import cv2
from deepface import DeepFace
import os
import numpy as np
from collections import deque, defaultdict
from module.camera_manager import shared_camera
import time

# Config
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "face_db")
CONFIRM_FRAMES = 5
DISTANCE_THRESH = 100

if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)
    print(f"[Face Recognition] สร้างโฟลเดอร์ {DB_PATH} แล้ว")

# โหลดโมเดล AI ล่วงหน้า
print("[Face Recognition] Loading AI Database...")
try:
    DeepFace.find(img_path=np.zeros((500,500,3), np.uint8), db_path=DB_PATH, 
                  model_name="ArcFace", enforce_detection=False, silent=True)
except:
    pass
print("[Face Recognition] Ready!")

class TrackedPerson:
    def __init__(self, face_box):
        self.box = face_box
        self.id_name = "Unknown"
        self.confidence_count = 0
        self.is_locked = False
        self.missing_frames = 0

    def update_position(self, new_box):
        self.box = new_box
        self.missing_frames = 0

    def update_name(self, name):
        if self.is_locked:
            return

        if name == self.id_name:
            self.confidence_count += 1
        else:
            self.confidence_count = max(0, self.confidence_count - 1)
            if self.confidence_count == 0:
                self.id_name = name

        if self.confidence_count >= CONFIRM_FRAMES and self.id_name != "Unknown":
            self.is_locked = True
            print(f"[Face Recognition] 🔒 LOCKED: {self.id_name}")

class FaceRecognizer:
    def __init__(self):
        print("[Face Recognition] Initializing...")
        self.active_people = []
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.running = False
        print("[Face Recognition] Ready")

    def process_frame(self, frame):
        """ประมวลผล frame เดียว และคืนค่า frame ที่วาดผลลัพธ์แล้ว"""
        if frame is None:
            return None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

        current_frame_people = []

        for (x, y, w, h) in faces:
            center_x, center_y = x + w//2, y + h//2
            matched_person = None

            for person in self.active_people:
                px, py, pw, ph = person.box
                p_center_x, p_center_y = px + pw//2, py + ph//2
                
                dist = np.sqrt((center_x - p_center_x)**2 + (center_y - p_center_y)**2)
                
                if dist < DISTANCE_THRESH:
                    matched_person = person
                    matched_person.update_position((x, y, w, h))
                    break
            
            if matched_person is None:
                new_person = TrackedPerson((x, y, w, h))
                self.active_people.append(new_person)
                matched_person = new_person

            if not matched_person.is_locked:
                try:
                    face_img = frame[y:y+h, x:x+w]
                    
                    dfs = DeepFace.find(img_path=face_img, db_path=DB_PATH, 
                                        model_name="Facenet", enforce_detection=False, silent=True)
                    
                    found_name = "Unknown"
                    if len(dfs) > 0 and not dfs[0].empty:
                        path = dfs[0].iloc[0]['identity']
                        found_name = os.path.basename(path).split('.')[0]
                    
                    matched_person.update_name(found_name)
                    
                except Exception as e:
                    pass

            current_frame_people.append(matched_person)

        self.active_people[:] = [p for p in self.active_people if p in current_frame_people]

        for p in self.active_people:
            x, y, w, h = p.box
            
            if p.is_locked:
                color = (0, 255, 0)
                status_text = f"{p.id_name} (LOCKED)"
            else:
                if p.id_name == "Unknown":
                    color = (0, 0, 255)
                    status_text = "Checking..."
                else:
                    color = (0, 255, 255)
                    status_text = f"{p.id_name} {p.confidence_count}/{CONFIRM_FRAMES}"

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, status_text, (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return frame

    def run(self):
        """รัน face recognition โดยใช้ shared camera"""
        self.running = True
        print("[Face Recognition] Start Monitoring...")
        
        while self.running:
            frame = shared_camera.get_frame()
            
            if frame is not None:
                processed_frame = self.process_frame(frame)
                
                if processed_frame is not None:
                    cv2.imshow("Face Recognition", processed_frame)
            
            if cv2.waitKey(1) == ord('q'):
                break
                
            time.sleep(0.01)
        
        cv2.destroyWindow("Face Recognition")
        self.running = False

    def stop(self):
        """หยุด face recognition"""
        self.running = False

def run_face_recognition():
    """Wrapper function สำหรับรัน face recognition"""
    recognizer = FaceRecognizer()
    recognizer.run()

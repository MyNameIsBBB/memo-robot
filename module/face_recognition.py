import cv2
import os
import numpy as np
from module.camera_manager import shared_camera
import time

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "face_db")
CONFIRM_FRAMES = 5
DISTANCE_THRESH = 100
RECOGNITION_INTERVAL = 30

class TrackedPerson:
    def __init__(self, face_box):
        self.box = face_box
        self.id_name = "Unknown"
        self.confidence_count = 0
        self.is_locked = False
        self.missing_frames = 0
        self.last_check_frame = 0

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
            print(f"[Face Recognition] 🔒 LOCKED: {self.id_name}", flush=True)

class FaceRecognizer:
    def __init__(self):
        print("[Face Recognition] Initializing...", flush=True)
        self.active_people = []
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.running = False
        self.frame_count = 0
        self.known_faces = {}
        self.load_known_faces()
        print(f"[Face Recognition] Ready with {len(self.known_faces)} known faces", flush=True)

    def load_known_faces(self):
        if not os.path.exists(DB_PATH):
            return
        
        for filename in os.listdir(DB_PATH):
            if filename.endswith(('.jpg', '.png', '.jpeg')):
                name = os.path.splitext(filename)[0]
                img_path = os.path.join(DB_PATH, filename)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    self.known_faces[name] = img

    def match_face(self, face_gray):
        if not self.known_faces:
            return "Unknown"
        
        face_resized = cv2.resize(face_gray, (100, 100))
        
        best_match = "Unknown"
        best_score = float('inf')
        
        for name, known_face in self.known_faces.items():
            known_resized = cv2.resize(known_face, (100, 100))
            score = np.sum(np.abs(face_resized.astype(float) - known_resized.astype(float)))
            
            if score < best_score:
                best_score = score
                best_match = name
        
        threshold = 1500000
        if best_score < threshold:
            return best_match
        return "Unknown"

    def process_frame(self, frame):
        if frame is None:
            return None

        self.frame_count += 1
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
                frames_since_check = self.frame_count - matched_person.last_check_frame
                
                if frames_since_check >= RECOGNITION_INTERVAL:
                    matched_person.last_check_frame = self.frame_count
                    
                    try:
                        face_gray = gray[y:y+h, x:x+w]
                        found_name = self.match_face(face_gray)
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
        self.running = True
        print("[Face Recognition] Start Monitoring (processing every 30 frames)...", flush=True)
        
        window_created = False
        while self.running:
            try:
                frame = shared_camera.get_frame()
                
                if frame is not None:
                    processed_frame = self.process_frame(frame)
                    
                    if processed_frame is not None:
                        if not window_created:
                            cv2.namedWindow("Face Recognition", cv2.WINDOW_NORMAL)
                            window_created = True
                        cv2.imshow("Face Recognition", processed_frame)
                
                if cv2.waitKey(1) == ord('q'):
                    break
                    
                time.sleep(0.033)
            except Exception as e:
                if not window_created:
                    time.sleep(0.5)
                continue
        
        if window_created:
            cv2.destroyWindow("Face Recognition")
        self.running = False

    def stop(self):
        self.running = False

def run_face_recognition():
    print("[Face Recognition] Starting (Lightweight OpenCV Mode)...", flush=True)
    if not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH)
        print(f"[Face Recognition] Created folder {DB_PATH}", flush=True)
    
    recognizer = FaceRecognizer()
    recognizer.run()


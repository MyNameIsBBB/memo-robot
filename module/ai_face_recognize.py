import cv2
from deepface import DeepFace
import os
import numpy as np

# ==========================================
# 1. ตั้งค่าระบบ (Config)
# ==========================================
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "face_db")
CONFIRM_FRAMES = 5    # ต้องเห็นว่าเป็นคนนี้กี่ครั้ง ถึงจะฟันธง (Lock)
DISTANCE_THRESH = 100 # ถ้าระยะห่างจากเฟรมเดิมไม่เกินนี้ ถือว่าเป็นคนเดิม

if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)
    print(f"สร้างโฟลเดอร์ {DB_PATH} แล้ว")

# โหลดข้อมูลหน้าล่วงหน้า (เพื่อให้เร็วขึ้น)
print("[System] Loading AI Database...")
# เรียกทิ้งไว้ 1 ครั้งเพื่อให้มันโหลดโมเดลเข้า RAM รอไว้เลย
try:
    DeepFace.find(img_path=np.zeros((500,500,3), np.uint8), db_path=DB_PATH, 
                  model_name="ArcFace", enforce_detection=False, silent=True)
except:
    pass
print("[System] Ready!")

# ==========================================
# 2. Class สำหรับจัดการคน (Tracking)
# ==========================================
class TrackedPerson:
    def __init__(self, face_box):
        self.box = face_box       # (x, y, w, h)
        self.id_name = "Unknown"  # ชื่อที่ระบบคิดว่าเป็น
        self.confidence_count = 0 # นับจำนวนครั้งที่มั่นใจ
        self.is_locked = False    # ล็อกชื่อหรือยัง?
        self.missing_frames = 0   # หายไปจากจอกี่เฟรมแล้ว (กันสั่น)

    def update_position(self, new_box):
        self.box = new_box
        self.missing_frames = 0 # รีเซ็ตการหาย

    def update_name(self, name):
        # ถ้าล็อกแล้ว ไม่ต้องทำอะไร
        if self.is_locked: return

        if name == self.id_name:
            self.confidence_count += 1
        else:
            # ถ้าชื่อเปลี่ยน ให้ลดความมั่นใจลง (ลังเล)
            self.confidence_count = max(0, self.confidence_count - 1)
            if self.confidence_count == 0:
                self.id_name = name # เปลี่ยนชื่อตามที่เจอล่าสุด

        # ถ้ามั่นใจครบกำหนด -> ล็อกเลย!
        if self.confidence_count >= CONFIRM_FRAMES and self.id_name != "Unknown":
            self.is_locked = True
            print(f"🔒 LOCKED: {self.id_name}")

# ตัวแปรเก็บรายการคนที่อยู่ในจอ
active_people = [] 

# ==========================================
# 3. Main Loop
# ==========================================
def run_face_recognition():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    while True:
        ret, frame = cap.read()
        if not ret: break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

        current_frame_people = []

        for (x, y, w, h) in faces:
            center_x, center_y = x + w//2, y + h//2
            matched_person = None

            for person in active_people:
                px, py, pw, ph = person.box
                p_center_x, p_center_y = px + pw//2, py + ph//2
                
                dist = np.sqrt((center_x - p_center_x)**2 + (center_y - p_center_y)**2)
                
                if dist < DISTANCE_THRESH:
                    matched_person = person
                    matched_person.update_position((x, y, w, h))
                    break
            
            if matched_person is None:
                new_person = TrackedPerson((x, y, w, h))
                active_people.append(new_person)
                matched_person = new_person

            if not matched_person.is_locked:
                try:
                    face_img = frame[y:y+h, x:x+w]
                    
                    dfs = DeepFace.find(img_path=face_img, db_path=DB_PATH, 
                                        model_name="ArcFace", enforce_detection=False, silent=True)
                    
                    found_name = "Unknown"
                    if len(dfs) > 0 and not dfs[0].empty:
                        path = dfs[0].iloc[0]['identity']
                        found_name = os.path.basename(path).split('.')[0]
                    
                    matched_person.update_name(found_name)
                    
                except Exception as e:
                    pass

            current_frame_people.append(matched_person)

        active_people[:] = [p for p in active_people if p in current_frame_people]

        for p in active_people:
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
            cv2.putText(frame, status_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.imshow("Smart Lock Face AI", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_face_recognition()
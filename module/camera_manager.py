import cv2
import threading
import time

class SharedCamera:
    """จัดการกล้องให้หลาย modules ใช้ร่วมกันได้"""
    
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        
    def start(self):
        """เริ่มต้นกล้องและอ่าน frame ต่อเนื่อง"""
        if self.running:
            return
            
        self.cap = cv2.VideoCapture(self.camera_id)
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        
        if not self.cap.isOpened():
            raise Exception(f"Cannot open camera {self.camera_id}")
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
    def _capture_loop(self):
        """อ่าน frame จากกล้องอย่างต่อเนื่อง"""
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame.copy()
            time.sleep(0.01)
    
    def get_frame(self):
        """ดึง frame ล่าสุดจากกล้อง"""
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
        return None
    
    def stop(self):
        """หยุดกล้อง"""
        self.running = False
        if self.cap:
            self.cap.release()

shared_camera = SharedCamera(camera_id=0)

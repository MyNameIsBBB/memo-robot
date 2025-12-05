import cv2
import numpy as np
from ultralytics import YOLO
import requests
import time
import threading
from collections import deque, defaultdict
import os
import json
import base64
from module.camera_manager import shared_camera

LINE_ACCESS_TOKEN = "G+ZNG9GrpreFB7bFFJk3sEFYDmZ/3BQlPhxbdvmBQVmqaIrbyV2Y7v3WV+qr5wfuofn16peu+IBw6BT3D6fOP7A25ts1DrKa4iVfRcQHuKpRuzKdbqVf2EpDCOdpugbHuzWa3l5K36WS6ua55b6H3AdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "U822497c4e7ad05ffe52d957ec2cb4a31"
IMGBB_API_KEY = "3a8b1c4e0d52252e0606d2b926d16a99"

MODEL_PATH = "yolov8n-pose.pt"
CONF_THRES = 0.50
FALL_CONFIRM_FRAMES = 5
HEIGHT_DROP_THRES = 0.65
ASPECT_RATIO_THRES = 1.1
ANGLE_THRES = 45
API_COOLDOWN = 30

class FallDetector:
    def __init__(self):
        print("[Fall Detection] Initializing...")
        
        try:
            self.model = YOLO(MODEL_PATH)
            print("[Fall Detection] Model Loaded")
        except Exception as e:
            print(f"[Fall Detection Error] Failed to load model: {e}")
            raise

        self.history = defaultdict(lambda: deque(maxlen=150))
        self.fall_counters = defaultdict(int)
        self.is_falling_state = defaultdict(bool)
        self.last_api_sent_time = {}
        
        self.msg_queue = deque()
        self.running = False
        threading.Thread(target=self._worker_sender, daemon=True).start()
        print("[Fall Detection] Ready")

    def upload_imgbb(self, image_path):
        url = "https://api.imgbb.com/1/upload"
        try:
            with open(image_path, "rb") as file:
                payload = {
                    "key": IMGBB_API_KEY,
                    "image": base64.b64encode(file.read()),
                }
                res = requests.post(url, payload, timeout=15)
                if res.status_code == 200:
                    return res.json()['data']['url']
                return None
        except Exception as e:
            print(f"[imgbb Error] {e}")
            return None

    def send_line_oa(self, text, image_url=None):
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
        }
        messages = [{"type": "text", "text": text}]
        if image_url:
            messages.append({
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": image_url
            })
        payload = {"to": LINE_USER_ID, "messages": messages}
        try:
            requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        except Exception as e:
            print(f"[LINE Error] {e}")

    def _worker_sender(self):
        while True:
            if self.msg_queue:
                msg_text, img_path = self.msg_queue.popleft()
                
                img_link = None
                if img_path and os.path.exists(img_path):
                    print(f"[Fall Detection] Sending Alert...")
                    img_link = self.upload_imgbb(img_path)
                
                self.send_line_oa(msg_text, img_link)
                print(f"[Fall Detection] LINE Sent")
                
                if img_path and os.path.exists(img_path):
                    try: os.remove(img_path)
                    except: pass
            time.sleep(0.1)

    def trigger_api_alert(self, person_id, frame, score):
        now = time.time()
        if now - self.last_api_sent_time.get(person_id, 0) < API_COOLDOWN:
            return 

        timestamp = time.strftime("%H%M%S")
        filename = f"fall_{person_id}_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        
        msg = f"⚠️ EMERGENCY!\nID: {person_id} ล้ม!\nความเสี่ยง: {score:.2f}"
        
        self.msg_queue.append((msg, filename))
        self.last_api_sent_time[person_id] = now

    def calculate_angle(self, p1, p2):
        dx = abs(p1[0] - p2[0])
        dy = abs(p1[1] - p2[1])
        if dy == 0: return 90.0
        return np.degrees(np.arctan(dx / dy))

    def process_frame(self, frame):
        if frame is None:
            return None
            
        try:
            results = self.model.track(frame, persist=True, verbose=False, conf=CONF_THRES, classes=0)
        except:
            return frame
        
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            
            if results[0].keypoints is not None:
                keypoints = results[0].keypoints.data.cpu().numpy()
            else:
                keypoints = []

            for i, track_id in enumerate(track_ids):
                if i >= len(keypoints): break
                
                x1, y1, x2, y2 = map(int, boxes[i])
                w, h = x2 - x1, y2 - y1
                aspect_ratio = w / h
                kp = keypoints[i]

                if not self.is_falling_state[track_id]:
                    self.history[track_id].append(h)

                recent = list(self.history[track_id])
                ref_height = np.percentile(recent, 90) if recent else h
                
                drop_ratio = h / ref_height if ref_height > 0 else 1.0

                risk_height = drop_ratio < HEIGHT_DROP_THRES
                risk_ar = aspect_ratio > ASPECT_RATIO_THRES
                risk_angle = False
                
                if kp.shape[0] > 12:
                    s_mid = ((kp[5][0]+kp[6][0])/2, (kp[5][1]+kp[6][1])/2) if kp[5][2]>0.5 and kp[6][2]>0.5 else None
                    h_mid = ((kp[11][0]+kp[12][0])/2, (kp[11][1]+kp[12][1])/2) if kp[11][2]>0.5 and kp[12][2]>0.5 else None
                    if s_mid and h_mid:
                        if self.calculate_angle(s_mid, h_mid) > ANGLE_THRES:
                            risk_angle = True

                is_currently_falling = (risk_height and (risk_ar or risk_angle)) or (drop_ratio < 0.5)

                if is_currently_falling:
                    self.fall_counters[track_id] += 1
                else:
                    self.fall_counters[track_id] = max(0, self.fall_counters[track_id] - 1)

                if self.fall_counters[track_id] >= FALL_CONFIRM_FRAMES:
                    self.is_falling_state[track_id] = True
                    status, color = "FALL DETECTED!", (0, 0, 255)
                    self.trigger_api_alert(track_id, frame, drop_ratio)
                else:
                    self.is_falling_state[track_id] = False
                    status, color = "Normal", (0, 255, 0)
                    if self.fall_counters[track_id] > 2:
                        status, color = "Warning...", (0, 165, 255)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.rectangle(frame, (x1, y1-30), (x1+200, y1), color, -1)
                cv2.putText(frame, status, (x1+5, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
                
                info = f"Drop:{drop_ratio:.2f} | AR:{aspect_ratio:.2f}"
                cv2.putText(frame, info, (x1, y2+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

        return frame

    def run(self):
        self.running = True
        print("[Fall Detection] Start Monitoring...")
        
        window_created = False
        while self.running:
            try:
                start_time = time.time()
                frame = shared_camera.get_frame()
                
                if frame is not None:
                    processed_frame = self.process_frame(frame)
                    
                    if processed_frame is not None:
                        fps = 1 / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
                        cv2.putText(processed_frame, f"FPS: {fps:.1f}", (10, 30), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        if not window_created:
                            cv2.namedWindow("Fall Detection", cv2.WINDOW_NORMAL)
                            window_created = True
                        cv2.imshow("Fall Detection", processed_frame)
                
                if cv2.waitKey(1) == ord('q'):
                    break
                
                time.sleep(0.01)
            except Exception as e:
                if not window_created:
                    time.sleep(0.5)
                continue
        
        if window_created:
            cv2.destroyWindow("Fall Detection")
        self.running = False

    def stop(self):
        self.running = False

def run_fall_detection():
    detector = FallDetector()
    detector.run()

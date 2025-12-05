import time
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.medicine_manager import MedicineDataManager

class MedicineReminder:
    def __init__(self, notification_callback=None):
        self.manager = MedicineDataManager()
        self.notified_medicines = set() 
        self.last_check_minute = None
        self.notification_callback = notification_callback
        
    def show_notification(self, medicines):
        if self.notification_callback:
            self.notification_callback("🔔 เตือนทานยา", medicines)
        else:
            print("\n" + "="*60)
            print(f"🔔 ถึงเวลาทานยาแล้ว! ({datetime.now().strftime('%H:%M')})")
            print("="*60)
            
            for medicine in medicines:
                print(f"\n💊 {medicine['name']}")
                print(f"   ⏰ เวลา: {medicine['taken_time']}")
                if medicine.get('dosage'):
                    print(f"   📏 ขนาด: {medicine['dosage']}")
                if medicine.get('uses'):
                    print(f"   ✓ สรรพคุณ: {', '.join(medicine['uses'])}")
            
            print("\n" + "="*60 + "\n")
            print("\a")
    
    def check_medicine_time(self):
        current_time = datetime.now().strftime("%H:%M")
        
        if self.last_check_minute != current_time:
            self.last_check_minute = current_time
            self.notified_medicines.clear() 
        
        medicines = self.manager.get_medicines_by_time(current_time)
        
        if medicines:
            unnotified = [m for m in medicines if m['id'] not in self.notified_medicines]
            
            if unnotified:
                self.show_notification(unnotified)
                for medicine in unnotified:
                    self.notified_medicines.add(medicine['id'])
    
    def run(self):
        print(f"\n🤖 Medicine Robot Started at {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        all_meds = self.manager.get_sorted_medicines(sort_by='taken_time')
        print(f"📊 โหลดข้อมูลยาเสร็จสิ้น: {len(all_meds)} รายการ")
        
        print("\n✅ ระบบกำลังทำงาน (กด Ctrl+C เพื่อหยุด)...")
        
        try:
            while True:
                self.check_medicine_time()
                time.sleep(20) 
                
        except KeyboardInterrupt:
            print("\n👋 ปิดระบบ")

if __name__ == "__main__":
    MedicineReminder().run()
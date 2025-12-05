# MEMO ROBOT

ระบบเตือนกินยาและตรวจจับการล้มด้วย AI พร้อมระบบจดจำใบหน้า

## Features

-   💊 **เตือนกินยา** - แจ้งเตือนอัตโนมัติตามเวลาที่กำหนด
-   🚨 **ตรวจจับการล้ม** - AI ตรวจจับและแจ้งเตือนผ่าน LINE
-   👤 **จดจำใบหน้า** - ระบุตัวตนด้วย AI (Facenet)
-   🌐 **เว็บจัดการ** - จัดการข้อมูลยาผ่านเว็บ

## ติดตั้ง

```bash
pip install -r requirements.txt
```

## รันโปรแกรม

```bash
python3 main.py
```

เว็บจะเปิดที่ http://127.0.0.1:5000 | กด `Ctrl+C` เพื่อหยุด

## โครงสร้างโปรเจค

```
memo_robot/
├── main.py                  # เริ่มต้นระบบ
├── config/
│   └── app_config.py       # การตั้งค่า
├── module/
│   ├── camera_manager.py   # จัดการกล้อง
│   ├── fall_detection.py   # ตรวจจับการล้ม
│   └── face_recognition.py # จดจำใบหน้า
├── scripts/
│   ├── daily_routine.py    # ระบบเตือนยา
│   └── medicine_manager.py # จัดการข้อมูลยา
├── gui/
│   └── web_app.py          # เว็บแอพ
└── data/
    ├── medicine_data.json  # ข้อมูลยา
    └── face_db/            # ฐานข้อมูลใบหน้า
```

## การตั้งค่า LINE (ถ้าต้องการ)

แก้ไขใน `module/fall_detection.py`:

```python
LINE_ACCESS_TOKEN = "your_token"
LINE_USER_ID = "your_user_id"
IMGBB_API_KEY = "your_api_key"
```

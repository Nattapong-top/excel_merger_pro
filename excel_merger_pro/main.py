# File: main.py
from src.ui.main_window import MainWindow

# เพิ่มส่วนนี้สำหรับจัดการ Splash Screen
try:
    import pyi_splash       # type: ignore
    # สั่งอัปเดตข้อความบนรูป (ถ้าใช้ bootloader แบบ text รองรับ)
    pyi_splash.update_text('Starting User Interface...')
    
    # ปิดรูป Splash ทิ้ง เพราะโปรแกรมเราพร้อมแล้ว
    pyi_splash.close()
except ImportError:
    pass

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
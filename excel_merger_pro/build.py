import PyInstaller.__main__
import customtkinter
import os
import shutil

# 1. หาที่อยู่ของ CustomTkinter ในเครื่อง (ต้องเอาไปด้วย ไม่งั้นเปิดไม่ติด)
ctk_path = os.path.dirname(customtkinter.__file__)

# 2. ตั้งชื่อไฟล์ .exe
exe_name = "Merge Excel Pro - By Paa Top IT v2"

print(f"🚀 Start building: {exe_name}...")
print(f"📦 CustomTkinter path found: {ctk_path}")

# 3. สั่ง PyInstaller ทำงาน
PyInstaller.__main__.run([
    'main.py',                          # ไฟล์เริ่มโปรแกรม
    f'--name={exe_name}',               # ชื่อไฟล์ผลลัพธ์
    '--onefile',                        # รวมเป็นไฟล์เดียว
    '--windowed',                       # ไม่ต้องโชว์จอดำ (Console)
    '--clean',                          # ล้าง cache เก่าก่อนทำ
    f'--add-data={ctk_path}{os.pathsep}customtkinter', # ยัดไส้ CustomTkinter เข้าไป
    
    # (Optional) ถ้าป๋ามีไอคอน .ico ให้เปิดบรรทัดล่างแล้วแก้ชื่อไฟล์
    # '--icon=my_logo.ico',
])

print("\n" + "="*50)
print(f"✅ สร้างเสร็จแล้วครับป๋า!")
print(f"📂 ไฟล์อยู่ที่โฟลเดอร์: dist/{exe_name}.exe")
print("="*50)
# เอกสารความต้องการ (Requirements Document)

## บทนำ

ฟีเจอร์การเลือกคอลัมน์สำหรับการรวมไฟล์เป็นการปรับปรุงฟังก์ชันการรวมไฟล์ Excel ที่มีอยู่ในโปรแกรม Excel Merger Pro ปัจจุบันโปรแกรมจะรวมไฟล์ Excel โดยนำทุกคอลัมน์จากไฟล์ต้นทางมารวมกัน ฟีเจอร์นี้จะเพิ่มความสามารถให้ผู้ใช้สามารถเลือกได้ว่าต้องการนำเฉพาะคอลัมน์ใดบ้างมารวมในไฟล์ผลลัพธ์ ซึ่งจะช่วยลดขนาดไฟล์และทำให้ข้อมูลที่ได้มีเฉพาะส่วนที่จำเป็นเท่านั้น

## อภิธานศัพท์ (Glossary)

- **Column_Selector**: ส่วนประกอบของระบบที่รับผิดชอบในการจัดการการเลือกคอลัมน์จากผู้ใช้
- **Merger**: ส่วนประกอบของระบบที่รับผิดชอบในการรวมไฟล์ Excel
- **Source_File**: ไฟล์ Excel ต้นทางที่ผู้ใช้ต้องการนำมารวม
- **Output_File**: ไฟล์ Excel ผลลัพธ์ที่ได้จากการรวมไฟล์
- **Column_Name**: ชื่อของคอลัมน์ในไฟล์ Excel (เช่น "A", "B", "C" หรือชื่อ header)
- **Column_Selection**: รายการคอลัมน์ที่ผู้ใช้เลือกไว้สำหรับการรวมไฟล์
- **Header_Row**: แถวแรกของไฟล์ Excel ที่มีชื่อหัวคอลัมน์

## ความต้องการ (Requirements)

### ความต้องการที่ 1: การแสดงรายการคอลัมน์ที่มีอยู่

**User Story:** ในฐานะผู้ใช้ ฉันต้องการเห็นรายการคอลัมน์ทั้งหมดที่มีในไฟล์ต้นทาง เพื่อที่ฉันจะได้เลือกคอลัมน์ที่ต้องการนำมารวม

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. WHEN ผู้ใช้เพิ่ม Source_File เข้าสู่ระบบ, THE Column_Selector SHALL แสดงรายการ Column_Name ทั้งหมดที่มีใน Source_File นั้น
2. WHERE Source_File มี Header_Row, THE Column_Selector SHALL แสดง Column_Name จาก Header_Row
3. WHERE Source_File ไม่มี Header_Row, THE Column_Selector SHALL แสดง Column_Name เป็นตัวอักษร (A, B, C, ...)
4. WHEN ผู้ใช้เพิ่ม Source_File หลายไฟล์, THE Column_Selector SHALL แสดงรายการ Column_Name ที่รวมจากทุกไฟล์โดยไม่ซ้ำกัน

### ความต้องการที่ 2: การเลือกคอลัมน์

**User Story:** ในฐานะผู้ใช้ ฉันต้องการเลือกคอลัมน์ที่ต้องการนำมารวม เพื่อที่ไฟล์ผลลัพธ์จะมีเฉพาะข้อมูลที่ฉันต้องการ

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE Column_Selector SHALL อนุญาตให้ผู้ใช้เลือก Column_Name อย่างน้อยหนึ่งคอลัมน์
2. THE Column_Selector SHALL อนุญาตให้ผู้ใช้เลือก Column_Name หลายคอลัมน์พร้อมกัน
3. THE Column_Selector SHALL อนุญาตให้ผู้ใช้ยกเลิกการเลือก Column_Name ที่เลือกไว้แล้ว
4. THE Column_Selector SHALL แสดงสถานะการเลือกของแต่ละ Column_Name อย่างชัดเจน
5. THE Column_Selector SHALL บันทึก Column_Selection ที่ผู้ใช้เลือกไว้

### ความต้องการที่ 3: การเลือกคอลัมน์ทั้งหมดและยกเลิกทั้งหมด

**User Story:** ในฐานะผู้ใช้ ฉันต้องการเลือกหรือยกเลิกคอลัมน์ทั้งหมดได้อย่างรวดเร็ว เพื่อประหยัดเวลาในกรณีที่มีคอลัมน์จำนวนมาก

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE Column_Selector SHALL มีฟังก์ชันเลือกคอลัมน์ทั้งหมด
2. WHEN ผู้ใช้เรียกใช้ฟังก์ชันเลือกคอลัมน์ทั้งหมด, THE Column_Selector SHALL เลือก Column_Name ทุกคอลัมน์ที่มีอยู่
3. THE Column_Selector SHALL มีฟังก์ชันยกเลิกการเลือกทั้งหมด
4. WHEN ผู้ใช้เรียกใช้ฟังก์ชันยกเลิกการเลือกทั้งหมด, THE Column_Selector SHALL ยกเลิกการเลือก Column_Name ทุกคอลัมน์

### ความต้องการที่ 4: การรวมไฟล์ด้วยคอลัมน์ที่เลือก

**User Story:** ในฐานะผู้ใช้ ฉันต้องการให้ไฟล์ผลลัพธ์มีเฉพาะคอลัมน์ที่ฉันเลือกไว้ เพื่อให้ได้ข้อมูลที่ตรงกับความต้องการ

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. WHEN ผู้ใช้เริ่มการรวมไฟล์, THE Merger SHALL ใช้ Column_Selection ที่ผู้ใช้เลือกไว้
2. THE Merger SHALL รวมเฉพาะ Column_Name ที่อยู่ใน Column_Selection เท่านั้น
3. THE Merger SHALL รักษาลำดับของคอลัมน์ตามที่ปรากฏใน Column_Selection
4. WHERE Source_File ไม่มี Column_Name ที่อยู่ใน Column_Selection, THE Merger SHALL สร้างคอลัมน์นั้นด้วยค่าว่าง
5. THE Merger SHALL สร้าง Output_File ที่มีเฉพาะคอลัมน์ที่อยู่ใน Column_Selection

### ความต้องการที่ 5: การจัดการกรณีไม่มีการเลือกคอลัมน์

**User Story:** ในฐานะผู้ใช้ ฉันต้องการให้ระบบแจ้งเตือนเมื่อฉันยังไม่ได้เลือกคอลัมน์ เพื่อป้องกันข้อผิดพลาด

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. WHEN ผู้ใช้เริ่มการรวมไฟล์ AND Column_Selection ว่างเปล่า, THE Merger SHALL แสดงข้อความแจ้งเตือนให้ผู้ใช้เลือกคอลัมน์อย่างน้อยหนึ่งคอลัมน์
2. WHEN ผู้ใช้เริ่มการรวมไฟล์ AND Column_Selection ว่างเปล่า, THE Merger SHALL ไม่ดำเนินการรวมไฟล์
3. WHERE ผู้ใช้ไม่ได้ระบุ Column_Selection, THE Merger SHALL ใช้ค่าเริ่มต้นเป็นการเลือกคอลัมน์ทั้งหมด

### ความต้องการที่ 6: การบันทึกและโหลดการตั้งค่าการเลือกคอลัมน์

**User Story:** ในฐานะผู้ใช้ ฉันต้องการบันทึกการเลือกคอลัมน์ไว้ใช้ในครั้งถัดไป เพื่อไม่ต้องเลือกใหม่ทุกครั้ง

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE Column_Selector SHALL มีฟังก์ชันบันทึก Column_Selection
2. WHEN ผู้ใช้บันทึก Column_Selection, THE Column_Selector SHALL เก็บ Column_Selection ไว้ในไฟล์การตั้งค่า
3. THE Column_Selector SHALL มีฟังก์ชันโหลด Column_Selection ที่บันทึกไว้
4. WHEN ผู้ใช้โหลด Column_Selection, THE Column_Selector SHALL แสดงการเลือกคอลัมน์ตามที่บันทึกไว้
5. WHERE Column_Selection ที่บันทึกไว้มี Column_Name ที่ไม่มีใน Source_File ปัจจุบัน, THE Column_Selector SHALL ข้าม Column_Name นั้นและแสดงเฉพาะคอลัมน์ที่มีอยู่

### ความต้องการที่ 7: การจัดเรียงลำดับคอลัมน์

**User Story:** ในฐานะผู้ใช้ ฉันต้องการกำหนดลำดับของคอลัมน์ในไฟล์ผลลัพธ์ เพื่อให้ข้อมูลแสดงผลตามที่ฉันต้องการ

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE Column_Selector SHALL อนุญาตให้ผู้ใช้เปลี่ยนลำดับของ Column_Name ใน Column_Selection
2. THE Column_Selector SHALL แสดงลำดับปัจจุบันของ Column_Name ใน Column_Selection
3. WHEN ผู้ใช้เปลี่ยนลำดับคอลัมน์, THE Column_Selector SHALL อัพเดท Column_Selection ตามลำดับใหม่
4. THE Merger SHALL สร้าง Output_File โดยเรียงคอลัมน์ตามลำดับใน Column_Selection

### ความต้องการที่ 8: การจัดการชื่อคอลัมน์ที่ซ้ำกัน

**User Story:** ในฐานะผู้ใช้ ฉันต้องการให้ระบบจัดการกรณีที่มีชื่อคอลัมน์ซ้ำกันในไฟล์ต่างๆ เพื่อป้องกันความสับสน

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. WHEN Source_File หลายไฟล์มี Column_Name ที่เหมือนกัน, THE Column_Selector SHALL แสดง Column_Name นั้นเพียงครั้งเดียว
2. WHEN ผู้ใช้เลือก Column_Name ที่ซ้ำกัน, THE Merger SHALL รวมข้อมูลจากคอลัมน์ที่มีชื่อเดียวกันจากทุก Source_File
3. WHERE Source_File มี Column_Name ที่เหมือนกันแต่ตำแหน่งต่างกัน, THE Merger SHALL ใช้ชื่อคอลัมน์เป็นเกณฑ์ในการจับคู่

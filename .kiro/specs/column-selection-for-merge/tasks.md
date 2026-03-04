# แผนการพัฒนา: การเลือกคอลัมน์สำหรับการรวมไฟล์

## ภาพรวม

ฟีเจอร์นี้เพิ่มความสามารถให้ผู้ใช้เลือกคอลัมน์ที่ต้องการรวมจากไฟล์ Excel ต้นทาง โดยสามารถจัดเรียงลำดับคอลัมน์ บันทึกและโหลดการตั้งค่าเพื่อใช้ซ้ำได้ การพัฒนาจะแบ่งเป็น 4 ชั้นตาม Clean Architecture: Domain Layer, Infrastructure Layer, Application Layer และ UI Layer

## Tasks

- [x] 1. สร้าง Domain Layer entities และ value objects
  - [x] 1.1 สร้าง ColumnMetadata entity
    - สร้างไฟล์ `excel_merger_pro/src/domain/column_metadata.py`
    - Implement dataclass ColumnMetadata ที่มี attributes: name, source_files, is_from_header, data_type
    - เพิ่ม validation ใน `__post_init__` ตรวจสอบว่า name ไม่ว่างและ source_files ไม่ว่าง
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 1.2 เขียน property test สำหรับ ColumnMetadata validation
    - **Property: ColumnMetadata Validation Invariants**
    - **Validates: Requirements 1.1**
    - ทดสอบว่า ColumnMetadata จะ raise ValueError เมื่อ name ว่างหรือ source_files ว่าง

  - [x] 1.3 ขยาย ProcessingOptions ให้รองรับ ColumnSelectionConfig
    - แก้ไขไฟล์ `excel_merger_pro/src/domain/processing_options.py`
    - เพิ่ม attribute `column_selection: Optional[ColumnSelectionConfig]` ใน ProcessingOptions
    - อัพเดท `__post_init__` validation ถ้าจำเป็น
    - _Requirements: 4.1_

  - [ ]* 1.4 เขียน unit tests สำหรับ ProcessingOptions ที่มี ColumnSelectionConfig
    - ทดสอบการสร้าง ProcessingOptions พร้อม column_selection
    - ทดสอบ default value (None)
    - _Requirements: 4.1_

- [x] 2. สร้าง Infrastructure Layer components
  - [x] 2.1 สร้าง IConfigurationRepository interface
    - สร้างไฟล์ `excel_merger_pro/src/infrastructure/repositories/configuration_repository.py`
    - Implement abstract class IConfigurationRepository ที่มี methods: save, load, list_saved_configs, delete
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 2.2 Implement JsonConfigurationRepository
    - Implement JsonConfigurationRepository ใน file เดียวกัน
    - รองรับการบันทึก/โหลด ColumnSelectionConfig เป็น JSON
    - สร้าง config directory ถ้ายังไม่มี
    - _Requirements: 6.2, 6.4_

  - [ ]* 2.3 เขียน property test สำหรับ configuration serialization round trip
    - **Property 14: Configuration Serialization Round Trip**
    - **Validates: Requirements 6.2, 6.4**
    - ทดสอบว่าการ save แล้ว load config จะได้ config เดิม

  - [ ]* 2.4 เขียน unit tests สำหรับ JsonConfigurationRepository
    - ทดสอบการบันทึก config ที่มีชื่อเฉพาะ
    - ทดสอบการโหลด config ที่มีอยู่
    - ทดสอบ error cases: FileNotFoundError, invalid JSON, permission errors
    - _Requirements: 6.2, 6.3, 6.4_

  - [x] 2.5 ขยาย ColumnSelector ให้รองรับ ColumnSelectionConfig
    - แก้ไขไฟล์ `excel_merger_pro/src/infrastructure/data_processors/column_selector.py`
    - เพิ่ม method `apply_selection(df: pd.DataFrame, config: ColumnSelectionConfig) -> pd.DataFrame`
    - กรองคอลัมน์ตาม selected_columns และเรียงลำดับตาม column_order
    - จัดการกรณีคอลัมน์ที่ไม่มีในไฟล์ (สร้างคอลัมน์ว่าง)
    - _Requirements: 4.2, 4.3, 4.4, 4.5_

  - [ ]* 2.6 เขียน property tests สำหรับ ColumnSelector
    - **Property 11: Output Column Filtering**
    - **Validates: Requirements 4.2, 4.5**
    - **Property 12: Output Column Ordering**
    - **Validates: Requirements 4.3, 7.4**
    - **Property 13: Missing Column Handling**
    - **Validates: Requirements 4.4**

  - [ ]* 2.7 เขียน unit tests สำหรับ ColumnSelector edge cases
    - ทดสอบกรณีคอลัมน์ที่เลือกไม่มีในไฟล์
    - ทดสอบกรณีมีคอลัมน์ซ้ำกัน
    - ทดสอบการเรียงลำดับคอลัมน์
    - _Requirements: 4.2, 4.3, 4.4_

- [ ] 3. Checkpoint - ตรวจสอบ Domain และ Infrastructure layers
  - รัน tests ทั้งหมดให้ผ่าน
  - ตรวจสอบว่า ColumnMetadata, JsonConfigurationRepository และ ColumnSelector ทำงานถูกต้อง
  - ถามผู้ใช้หากมีคำถามหรือพบปัญหา

- [x] 4. สร้าง Application Layer services
  - [x] 4.1 สร้าง ColumnDiscoveryService
    - สร้างไฟล์ `excel_merger_pro/src/application/services/column_discovery_service.py`
    - Implement method `discover_columns(files: List[SourceFile]) -> List[ColumnMetadata]`
    - อ่านคอลัมน์จากทุกไฟล์และรวมเป็น list ที่ไม่ซ้ำกัน
    - ตรวจสอบว่าไฟล์มี header row หรือไม่
    - สร้างชื่อคอลัมน์เป็นตัวอักษร (A, B, C, ...) ถ้าไม่มี header
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 4.2 เขียน property tests สำหรับ ColumnDiscoveryService
    - **Property 1: Column Discovery Completeness**
    - **Validates: Requirements 1.1**
    - **Property 2: Header Row Name Usage**
    - **Validates: Requirements 1.2**
    - **Property 3: Letter-Based Column Names**
    - **Validates: Requirements 1.3**
    - **Property 4: Multi-File Column Uniqueness**
    - **Validates: Requirements 1.4, 8.1**

  - [ ]* 4.3 เขียน unit tests สำหรับ ColumnDiscoveryService
    - ทดสอบการอ่านคอลัมน์จากไฟล์ที่มี header
    - ทดสอบการอ่านคอลัมน์จากไฟล์ที่ไม่มี header
    - ทดสอบการรวมคอลัมน์จากหลายไฟล์
    - ทดสอบ error cases: ไฟล์เสีย, ไฟล์ว่าง
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 4.4 สร้าง ColumnSelectionService
    - สร้างไฟล์ `excel_merger_pro/src/application/services/column_selection_service.py`
    - Implement methods: create_config, save_config, load_config, get_default_config
    - validate ว่า selected_columns ไม่ว่างและ column_order ตรงกับ selected_columns
    - _Requirements: 2.1, 2.5, 5.3, 6.1, 6.3_

  - [ ]* 4.5 เขียน property tests สำหรับ ColumnSelectionService
    - **Property 8: Selection Persistence**
    - **Validates: Requirements 2.5**
    - **Property 15: Configuration Column Filtering**
    - **Validates: Requirements 6.5**

  - [ ]* 4.6 เขียน unit tests สำหรับ ColumnSelectionService
    - ทดสอบการสร้าง config ที่ valid
    - ทดสอบ validation errors: empty selection, mismatched order
    - ทดสอบ get_default_config (เลือกทุกคอลัมน์)
    - _Requirements: 2.1, 5.1, 5.3_

  - [x] 4.7 ขยาย MergeService ให้รองรับ ColumnSelectionConfig
    - แก้ไขไฟล์ `excel_merger_pro/src/application/services/merge_service.py`
    - เพิ่มการตรวจสอบ column_selection ใน ProcessingOptions
    - เรียกใช้ ColumnSelector.apply_selection ถ้ามี column_selection
    - แสดง error message ถ้า column_selection ว่างเปล่า
    - _Requirements: 4.1, 5.1, 5.2_

  - [ ]* 4.8 เขียน unit tests สำหรับ MergeService กับ column selection
    - ทดสอบการรวมไฟล์ด้วย column selection
    - ทดสอบ error case: column_selection ว่างเปล่า
    - ทดสอบ default behavior: ไม่มี column_selection (รวมทุกคอลัมน์)
    - _Requirements: 4.1, 5.1, 5.2, 5.3_

- [ ] 5. Checkpoint - ตรวจสอบ Application layer
  - รัน tests ทั้งหมดให้ผ่าน
  - ตรวจสอบว่า services ทำงานร่วมกันได้ถูกต้อง
  - ถามผู้ใช้หากมีคำถามหรือพบปัญหา

- [ ] 6. สร้าง UI Layer components
  - [ ] 6.1 สร้าง ColumnSelectionDialog
    - สร้างไฟล์ `excel_merger_pro/src/ui/dialogs/column_selection_dialog.py`
    - สร้าง dialog ด้วย PyQt6 ที่แสดงรายการคอลัมน์พร้อม checkboxes
    - เพิ่มปุ่ม "Select All" และ "Deselect All"
    - เพิ่มปุ่ม "Save" และ "Load" สำหรับ configuration
    - รองรับ drag-and-drop สำหรับเรียงลำดับคอลัมน์
    - Implement method `get_selection_config() -> Optional[ColumnSelectionConfig]`
    - Implement method `load_configuration(config: ColumnSelectionConfig)`
    - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 3.1, 3.3, 6.1, 6.3, 7.1, 7.2_

  - [ ]* 6.2 เขียน unit tests สำหรับ ColumnSelectionDialog
    - ทดสอบการแสดงรายการคอลัมน์
    - ทดสอบการเลือก/ยกเลิกคอลัมน์
    - ทดสอบ Select All / Deselect All
    - ทดสอบการเรียงลำดับคอลัมน์
    - ทดสอบการ save/load configuration
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.3, 6.1, 6.3, 7.1_

  - [ ] 6.3 เชื่อมต่อ ColumnSelectionDialog กับ main window
    - แก้ไขไฟล์ main window เพื่อเพิ่มปุ่ม "Select Columns"
    - เมื่อผู้ใช้คลิกปุ่ม ให้เรียก ColumnDiscoveryService เพื่อค้นหาคอลัมน์
    - แสดง ColumnSelectionDialog พร้อมรายการคอลัมน์
    - เก็บ ColumnSelectionConfig ที่ผู้ใช้เลือกไว้ใน ProcessingOptions
    - _Requirements: 1.1, 2.5, 4.1_

  - [ ]* 6.4 เขียน integration tests สำหรับ UI flow
    - ทดสอบ end-to-end flow: เพิ่มไฟล์ → เลือกคอลัมน์ → รวมไฟล์
    - ทดสอบ save/load configuration flow
    - _Requirements: 1.1, 2.5, 4.1, 6.1, 6.3_

- [ ] 7. สร้าง integration tests สำหรับ merge operation
  - [ ]* 7.1 เขียน property tests สำหรับ merge กับ column selection
    - **Property 18: Duplicate Column Name Merging**
    - **Validates: Requirements 8.2**
    - **Property 19: Name-Based Column Matching**
    - **Validates: Requirements 8.3**

  - [ ]* 7.2 เขียน integration tests สำหรับ multi-file merge
    - ทดสอบการรวมหลายไฟล์ที่มีคอลัมน์ต่างกัน
    - ทดสอบการรวมไฟล์ที่มีคอลัมน์ซ้ำกัน
    - ทดสอบการรวมไฟล์ที่มีคอลัมน์ไม่ครบ
    - _Requirements: 4.2, 4.4, 8.1, 8.2, 8.3_

  - [ ]* 7.3 เขียน end-to-end tests
    - ทดสอบ complete flow: discover → select → reorder → save config → merge
    - ทดสอบ load config → merge
    - _Requirements: 1.1, 2.5, 4.1, 6.1, 6.3, 7.1_

- [ ] 8. Checkpoint สุดท้าย - ตรวจสอบระบบทั้งหมด
  - รัน tests ทั้งหมดให้ผ่าน (unit tests, property tests, integration tests)
  - ทดสอบ UI ด้วยตนเองกับไฟล์จริง
  - ตรวจสอบว่าทุก requirements ได้รับการ implement ครบถ้วน
  - ถามผู้ใช้หากมีคำถามหรือต้องการปรับปรุงเพิ่มเติม

## หมายเหตุ

- Tasks ที่มีเครื่องหมาย `*` เป็น optional และสามารถข้ามได้เพื่อ MVP ที่เร็วขึ้น
- แต่ละ task อ้างอิง requirements เฉพาะเจาะจงเพื่อความชัดเจน
- Checkpoints ช่วยให้มั่นใจว่าแต่ละ layer ทำงานถูกต้องก่อนไปต่อ
- Property tests ใช้ Hypothesis library ด้วย 100+ iterations
- Unit tests ทดสอบกรณีเฉพาะเจาะจงและ edge cases
- Integration tests ทดสอบการทำงานร่วมกันของทุกส่วน

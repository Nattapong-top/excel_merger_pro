# File: src/application/services.py
from typing import List, Any
from src.application.interfaces import ILogger, ISheetReader
from src.domain.entities import SourceFile

class MergeService:
    # 1. รับ reader เข้ามาด้วย
    def __init__(self, logger: ILogger, reader: ISheetReader):
        self.logger = logger
        self.reader = reader
    
    def merge(self, files: List[SourceFile]) -> Any:
        import pandas as pd
        self.logger.info("Starting merge process")
        
        all_data_frames = []
        
        for file in files:
            self.logger.info(f"Processing file: {file.path.value}")
            
            # วนลูปเฉพาะ Sheet ที่ User "เลือก" เท่านั้น (selected_sheets)
            # ถ้า user ไม่เลือกเลย (selected_sheets ว่าง) ลูปนี้ก็จะไม่ทำงาน (ถูกต้องแล้ว)
            for sheet in file.selected_sheets:
                try:
                    self.logger.info(f"  - Reading sheet: {sheet.value}")
                    
                    # สั่ง reader ให้อ่านข้อมูล
                    df = self.reader.read_sheet(file.path, sheet)
                    
                    # (Optional) เพิ่มชื่อไฟล์ต้นทาง (เหมือนโปรเจคเก่าป๋า)
                    df['Origin_File'] = file.path.value
                    df['Origin_Sheet'] = sheet.value
                    
                    all_data_frames.append(df)
                    
                except Exception as e:
                    self.logger.error(f"Failed to read sheet {sheet.value}: {e}")

        # รวมร่าง! (Concatenate)
        if not all_data_frames:
            self.logger.info("No data found to merge")
            return pd.DataFrame() # ส่งตารางเปล่ากลับไป
            
        result = pd.concat(all_data_frames, ignore_index=True)
        self.logger.info(f"Merge complete. Total rows: {len(result)}")
        return result
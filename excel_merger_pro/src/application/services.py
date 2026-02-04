from typing import List
from src.application.interfaces import ILogger
from src.domain.entities import SourceFile

class MergeService:
    def __init__(self, logger: ILogger):
        self.logger = logger
    
    def merge(self, files: List[SourceFile]):
        # 1. Log เริ่มต้นตามที่ Test ต้องการ
        self.logger.info("Starting merge process")
        
        # 2. วนลูปไฟล์เพื่อจำลองการทำงาน
        for file in files:
            self.logger.info(f"Processing file: {file.path.value}")
            
            # (อนาคตเราจะใส่ Logic การอ่าน Excel จริงๆ ตรงนี้)
            # ตอนนี้เอาแค่โครงให้ผ่าน Test ก่อนครับ
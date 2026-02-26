# File: src/application/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Any, Iterator
# ใช้ Any ไปก่อนเพื่อเลี่ยงการ import pandas ใน Application Layer (รักษาความสะอาด)
# หรือถ้าป๋ายอมให้ App รู้จัก Pandas ได้ (เพื่อความง่าย) ก็ import pandas มาใส่ type hint ได้ครับ

from src.domain.value_objects import FilePath, SheetName
from src.domain.processing_options import ProgressState

class ILogger(ABC):
    @abstractmethod
    def info(self, message: str): pass
    @abstractmethod
    def error(self, message: str): pass

class ISheetReader(ABC):
    @abstractmethod
    def get_sheet_names(self, path: FilePath) -> List[SheetName]:
        pass

    @abstractmethod
    def read_sheet(self, path: FilePath, sheet_name: SheetName) -> Any:
        """อ่านข้อมูลจาก Sheet ที่ระบุ ส่งกลับมาเป็น DataFrame"""
        pass
    
    @abstractmethod
    def read_sheet_chunked(
        self, 
        path: FilePath, 
        sheet_name: SheetName, 
        chunk_size: int
    ) -> Iterator[Any]:
        """
        อ่าน Sheet ทีละ chunk เพื่อประหยัดแรม
        
        Args:
            path: ที่อยู่ไฟล์
            sheet_name: ชื่อ Sheet
            chunk_size: จำนวนแถวต่อ chunk
            
        Yields:
            DataFrame แต่ละ chunk
        """
        pass
    
    @abstractmethod
    def estimate_row_count(self, path: FilePath, sheet_name: SheetName) -> int:
        """
        ประมาณการจำนวนแถวโดยไม่โหลดข้อมูลทั้งหมด
        ใช้สำหรับคำนวณ progress
        """
        pass


class IProgressCallback(ABC):
    """
    Interface สำหรับรายงานความคืบหน้าของการ merge
    
    ใช้ Callback Pattern เพื่อให้ UI สามารถอัพเดทแบบ real-time
    โดยไม่ต้อง polling
    """
    
    @abstractmethod
    def on_progress(self, state: ProgressState) -> None:
        """
        เรียกเมื่อมีความคืบหน้าใหม่
        
        Args:
            state: สถานะความคืบหน้าปัจจุบัน
        """
        pass
    
    @abstractmethod
    def should_cancel(self) -> bool:
        """
        ตรวจสอบว่าผู้ใช้ต้องการยกเลิกการทำงานหรือไม่
        
        Returns:
            True ถ้าต้องการยกเลิก, False ถ้าทำงานต่อ
        """
        pass


class IDataProcessor(ABC):
    """
    Interface สำหรับประมวลผลข้อมูล (Data Transformation)
    
    ใช้ Chain of Responsibility Pattern เพื่อให้สามารถ
    ต่อ processor หลายตัวเข้าด้วยกันได้
    """
    
    @abstractmethod
    def process(self, df: Any) -> Any:
        """
        ประมวลผล DataFrame และส่งกลับ DataFrame ที่ผ่านการประมวลผลแล้ว
        
        Args:
            df: DataFrame ที่ต้องการประมวลผล
            
        Returns:
            DataFrame ที่ผ่านการประมวลผลแล้ว
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        ชื่อของ processor สำหรับ logging
        
        Returns:
            ชื่อ processor เช่น "GroupByProcessor", "DuplicateRemover"
        """
        pass
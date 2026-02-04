# File: src/domain/value_objects.py
from dataclasses import dataclass

@dataclass(frozen=True)
class FilePath:
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("File path cannot be empty")

@dataclass(frozen=True)
class SheetName:
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Sheet name cannot be empty")
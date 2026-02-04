from dataclasses import dataclass

@dataclass(frozen=True)
class FilePath:
    value: str

@dataclass(frozen=True)
class SheetName:
    value: str
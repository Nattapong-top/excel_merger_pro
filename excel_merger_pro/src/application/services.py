from typing import List
from src.application.interfaces import ILogger
from src.domain.entities import SourceFile

class MergeService:
    def __init__(self, logger: ILogger):
        self.logger = logger

    def merge(self, files: List[SourceFile]):
        # TODO: Implement Logic here
        # self.logger.info("Starting merge process")
        pass
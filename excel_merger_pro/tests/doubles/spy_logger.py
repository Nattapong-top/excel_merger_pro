from src.application.interfaces import ILogger

class SpyLogger(ILogger):
    def __init__(self):
        self.logs = []

    def info(self, message: str):
        self.logs.append(f"INFO: {message}")

    def error(self, message: str):
        self.logs.append(f"ERROR: {message}")
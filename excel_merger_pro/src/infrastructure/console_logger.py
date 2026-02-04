from src.application.interfaces import ILogger

class ConsoleLogger(ILogger):
    def info(self, message: str):
        print(f"[INFO] {message}")

    def error(self, message: str):
        print(f"[ERROR] {message}")
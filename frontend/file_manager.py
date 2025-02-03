import json
import os
import time
import uuid

class FileManager:
    allowed_extensions = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a",
                          ".wma", ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm"}

    def __init__(self, send_file_func):
        """Инициализирует FileManager с функцией send_file"""
        self.send_file = send_file_func

    def add_task(self, file_path):
        """Добавляет задачу в файл tasks.json."""
        if not self.is_valid_file(file_path):
            print(f"Недопустимый файл: {file_path}")
            return None

        task_id = str(uuid.uuid4())

        while True:
            try:
                if os.path.exists("tasks.json"):
                    with open("tasks.json", "r+", encoding="utf-8") as f:
                        tasks = json.load(f)
                else:
                    tasks = {}

                # Добавляем новую задачу
                tasks[task_id] = {
                    "original_name": os.path.basename(file_path),
                    "status": "В обработке...",
                    "transcript_path": None,
                    "error": None,
                    "timestamp": time.time()
                }

                # Записываем изменения
                with open("tasks.json", "w", encoding="utf-8") as f:
                    json.dump(tasks, f, indent=4)

                return task_id, file_path

            except (OSError):
                time.sleep(0.1)

    def is_valid_file(self, file_path):
        """Проверяет, поддерживается ли загруженный файл"""
        return os.path.splitext(file_path)[1].lower() in self.allowed_extensions

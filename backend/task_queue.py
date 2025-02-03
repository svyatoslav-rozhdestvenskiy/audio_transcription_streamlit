import asyncio

from whisper_transcriber import WhisperTranscriber
from audio_processor import AudioProcessor

class TaskQueue:
    def __init__(self, maxsize=10):
        """
        Асинхронная очередь задач для обработки аудиофайлов через WebSocket.
        """
        self.queue = asyncio.Queue(maxsize=maxsize)

        # Создаем единственный экземпляр Whisper
        self.transcriber = WhisperTranscriber()

        # Храним результаты задач
        self.results = {}

        # Запускаем обработку очереди
        self.processing_task = asyncio.create_task(self.process_tasks())

    async def add_task(self, audio_bytes, task_id):
        """
        Добавляет аудиопоток в очередь. Если очередь полна, возвращает None.
        """
        if self.queue.full():
            return False

        # Создаем пустой слот для результата
        self.results[task_id] = None

        # Ставим в очередь
        await self.queue.put((task_id, audio_bytes))

        return True

    async def process_tasks(self):
        """
        Асинхронная обработка задач: предобработка → инференс Whisper.
        """
        while True:
            task_id, audio_bytes = await self.queue.get()
            try:
                processor = AudioProcessor(audio_bytes)
                preprocessed_audio, error = await asyncio.to_thread(processor.process)

                if preprocessed_audio is None:
                    self.results[task_id] = {"task_id": task_id, "error": error}
                else:
                    transcript, error = await asyncio.to_thread(self.transcriber.transcribe_audio, preprocessed_audio)
                    if transcript is None:
                        self.results[task_id] = {"task_id": task_id, "error": error}
                    else:
                        self.results[task_id] = {"task_id": task_id, "transcript": transcript}

            except Exception as e:
                self.results[task_id] = {"task_id": task_id, "error": str(e)}
            finally:
                self.queue.task_done()

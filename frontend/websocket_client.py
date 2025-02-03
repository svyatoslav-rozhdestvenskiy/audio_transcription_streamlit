import time
import os
import json
import websockets

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from file_manager import FileManager

app = FastAPI()

async def send_file(file_path, task_id):
    """Отправляет файл на сервер через WebSocket."""
    uri = "ws://localhost:8000/ws"

    async with websockets.connect(uri) as websocket:
        # Передаем task_id
        await websocket.send(json.dumps({"task_id": task_id}))

        # Отправляем файл пакетами по 1000 фреймов
        with open(file_path, "rb") as f:
            while chunk := f.read(1000):
                await websocket.send(chunk)

        # Сообщаем об окончании пакетов
        await websocket.send(b"END")

        # Ждем, пока сервер разорвет соединение
        try:
            while True:
                await websocket.recv()
        except websockets.exceptions.ConnectionClosed:
            print(f"Сервер закрыл соединение после обработки {file_path}")

    # Удаляем файл с сервера
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except PermissionError:
            print(f"Не удалось удалить файл {file_path}")

# Создаем объект класса FileManager
file_manager = FileManager(send_file)

@app.websocket("/client-endpoint")
async def client_endpoint(websocket: WebSocket):
    """
    Клиентский сервер, принимает сообщения от сервера бэкэнд.
    """
    await websocket.accept()
    try:
        while True:
            response = await websocket.receive_json()

            # Обновляем задачи
            update_task(response)

    except WebSocketDisconnect:
        print("Соединение с WebSocket закрыто клиентом или сервером.")

    except Exception as e:
        print(f"Ошибка на клиентском сервере: {e}")


def update_task(response):
    """Обновляет задачи в tasks.json при получении ответа от сервера."""
    # Получаем task_id
    task_id = response.get("task_id")
    if not task_id:
        print("Ошибка: отсутствует task_id в ответе сервера.")
        return

    while True:
        try:
            with open("tasks.json", "r+", encoding="utf-8") as f:
                tasks = json.load(f)
                if task_id not in tasks:
                    print(f"Неизвестный task_id: {task_id}")
                    return

                # Проверяем наличие ошибок при обработке
                if response.get("error"):
                    tasks[task_id]["status"] = f"Ошибка: {response['error']}"
                    tasks[task_id]["error"] = response["error"]

                # Получаем расшифровку
                elif response.get("transcript"):
                    # Проверяем есть ли нужная папка
                    os.makedirs("transcripts", exist_ok=True)

                    # Формируем новое имя для файла
                    txt_file = os.path.join("transcripts", f"{tasks[task_id]['original_name'].rsplit('.', 1)[0]}.txt")
                    counter = 1
                    while os.path.exists(txt_file):
                        txt_file = os.path.join("transcripts", f"{tasks[task_id]['original_name'].rsplit('.', 1)[0]} ({counter}).txt")
                        counter += 1
                    with open(txt_file, "w", encoding="utf-8") as t:
                        t.write(response["transcript"])

                    # Меняем статус
                    tasks[task_id]["status"] = "Готово!"
                    tasks[task_id]["transcript_path"] = txt_file

            # Обновляем нужную задачу
            with open("tasks.json", "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=4)

            break

        except (OSError, json.JSONDecodeError):
            time.sleep(0.1)

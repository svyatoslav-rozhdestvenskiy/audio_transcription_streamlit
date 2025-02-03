import json
import asyncio
import websockets

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from task_queue import TaskQueue

app = FastAPI()

task_queue = None  # Пока не создаем TaskQueue

@app.on_event("startup")
async def startup_event():
    """Создает TaskQueue после старта FastAPI."""
    global task_queue
    task_queue = TaskQueue()

async def send_result_to_client(client_uri, task_id, overload_queue=False):
    """
    Соединяется с клиентским сервером, отправляет результат и закрывает соединение.
    """
    # Отправляем сообщение клиенту, если сервер перегружен
    if overload_queue:
        result = {"task_id" : task_id, "error" : 'Сервер перегружен, попробуйте позже'}
        async with websockets.connect(client_uri) as websocket:
            await websocket.send(json.dumps(result))

    else:
        # Ждём, пока задача завершится
        while task_queue.results.get(task_id) is None:
            await asyncio.sleep(0.5)

        # Получаем результат
        result = task_queue.results.pop(task_id)

        # Подключаемся к клиентскому серверу и отправляем результат
        async with websockets.connect(client_uri) as websocket:
            await websocket.send(json.dumps(result))



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket-сервер для транскрибации аудио. Принимает данные и запускает обработку"""
    await websocket.accept()
    audio_data = b""

    try:
        first_message = await websocket.receive_json()
        task_id = first_message.get("task_id")
        while True:
            data = await websocket.receive_bytes()
            if data == b"END":
                task_added = await task_queue.add_task(audio_data, task_id)
                if not task_added:
                    client_uri = "ws://localhost:9000/client-endpoint"
                    asyncio.create_task(send_result_to_client(client_uri, task_id, overload_queue=True))
                    return

                # Запускаем фоновую задачу для ожидания результата
                client_uri = "ws://localhost:9000/client-endpoint"
                asyncio.create_task(send_result_to_client(client_uri, task_id))
                return

            audio_data += data

    except WebSocketDisconnect as e:
        print(f"Клиент отключился. Код ошибки: {e.code}")

    except Exception as e:
        print(f'Ошибка соединения : {e}')
        await websocket.close()
